"""Background job queue system for async tasks."""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from threading import Lock, Thread


class JobStatus(Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Job:
    """Background job representation."""
    id: str
    task_name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    status: JobStatus = JobStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class JobQueue:
    """Simple in-memory job queue with async execution."""
    
    def __init__(self, max_workers: int = 2):
        """
        Initialize job queue.
        
        Args:
            max_workers: Maximum number of concurrent workers
        """
        self._jobs: Dict[str, Job] = {}
        self._lock = Lock()
        self._workers: List[Thread] = []
        self._running = False
        self._max_workers = max_workers
        self._queue: List[str] = []  # Queue of job IDs
    
    def start(self) -> None:
        """Start the job queue workers."""
        if self._running:
            return
        
        self._running = True
        for i in range(self._max_workers):
            worker = Thread(target=self._worker_loop, daemon=True, name=f"JobWorker-{i}")
            worker.start()
            self._workers.append(worker)
    
    def stop(self) -> None:
        """Stop the job queue workers."""
        self._running = False
        # Wait for workers to finish current jobs
        for worker in self._workers:
            worker.join(timeout=5.0)
        self._workers.clear()
    
    def enqueue(
        self,
        task_name: str,
        func: Callable,
        *args,
        **kwargs,
    ) -> str:
        """
        Enqueue a job for execution.
        
        Args:
            task_name: Name of the task
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())
        job = Job(
            id=job_id,
            task_name=task_name,
            func=func,
            args=args,
            kwargs=kwargs,
        )
        
        with self._lock:
            self._jobs[job_id] = job
            self._queue.append(job_id)
        
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        with self._lock:
            return self._jobs.get(job_id)
    
    def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        limit: int = 100,
    ) -> List[Job]:
        """
        List jobs with optional filtering.
        
        Args:
            status: Filter by status
            limit: Maximum number of jobs to return
            
        Returns:
            List of jobs
        """
        with self._lock:
            jobs = list(self._jobs.values())
            if status:
                jobs = [j for j in jobs if j.status == status]
            # Sort by created_at descending
            jobs.sort(key=lambda j: j.created_at, reverse=True)
            return jobs[:limit]
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a pending job.
        
        Args:
            job_id: Job ID to cancel
            
        Returns:
            True if job was cancelled, False if not found or already running
        """
        with self._lock:
            if job_id not in self._jobs:
                return False
            
            job = self._jobs[job_id]
            if job.status != JobStatus.PENDING:
                return False
            
            job.status = JobStatus.CANCELLED
            if job_id in self._queue:
                self._queue.remove(job_id)
            return True
    
    def _worker_loop(self) -> None:
        """Worker thread loop."""
        while self._running:
            job_id = None
            try:
                # Get next job from queue
                with self._lock:
                    if not self._queue:
                        time.sleep(0.1)  # Wait a bit before checking again
                        continue
                    
                    job_id = self._queue.pop(0)
                    job = self._jobs.get(job_id)
                    
                    if not job or job.status != JobStatus.PENDING:
                        continue
                    
                    job.status = JobStatus.RUNNING
                    job.started_at = datetime.utcnow()
                
                # Execute job
                try:
                    result = job.func(*job.args, **job.kwargs)
                    job.result = result
                    job.status = JobStatus.COMPLETED
                except Exception as e:
                    job.error = str(e)
                    job.status = JobStatus.FAILED
                finally:
                    job.completed_at = datetime.utcnow()
            
            except Exception as e:
                # Handle errors in worker loop
                if job_id and job_id in self._jobs:
                    with self._lock:
                        job = self._jobs[job_id]
                        job.error = f"Worker error: {str(e)}"
                        job.status = JobStatus.FAILED
                        job.completed_at = datetime.utcnow()
    
    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """
        Remove old completed/failed jobs.
        
        Args:
            max_age_hours: Maximum age in hours
            
        Returns:
            Number of jobs removed
        """
        with self._lock:
            cutoff = datetime.utcnow().timestamp() - (max_age_hours * 3600)
            to_remove = [
                job_id for job_id, job in self._jobs.items()
                if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
                and job.completed_at
                and job.completed_at.timestamp() < cutoff
            ]
            
            for job_id in to_remove:
                del self._jobs[job_id]
            
            return len(to_remove)


# Global job queue instance
_job_queue: Optional[JobQueue] = None


def get_job_queue() -> JobQueue:
    """Get or create the global job queue."""
    global _job_queue
    if _job_queue is None:
        _job_queue = JobQueue(max_workers=2)
        _job_queue.start()
    return _job_queue
