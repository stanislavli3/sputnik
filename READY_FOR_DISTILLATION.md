# ✅ Ready for On-Policy Distillation Implementation

## Status: READY TO START

All Phase 6 backend performance tasks are complete. The infrastructure is ready for implementing on-policy distillation with human feedback.

---

## What's Ready

### ✅ Background Job Queue
**File**: `src/sputnik/api/jobs.py`

**Usage for Training Jobs**:
```python
from sputnik.api.jobs import get_job_queue, JobStatus

queue = get_job_queue()

# Enqueue a training job
job_id = queue.enqueue(
    "training",
    train_model_function,
    rollouts=rollouts,
    model_config=config,
)

# Check job status
job = queue.get_job(job_id)
if job.status == JobStatus.COMPLETED:
    print(f"Training complete! Result: {job.result}")
```

**Features**:
- Auto-starts on server startup
- Thread-safe execution
- Status tracking (PENDING → RUNNING → COMPLETED/FAILED)
- Error handling

---

### ✅ Caching System
**File**: `src/sputnik/api/cache.py`

**Usage**:
```python
from sputnik.api.cache import get_schema_cache, get_metrics_cache

# Schema cache (5 min TTL)
schema_cache = get_schema_cache()
schema_cache.set("key", data, ttl=300)

# Metrics cache (1 min TTL)
metrics_cache = get_metrics_cache()
metrics_cache.set("key", data, ttl=60)
```

**Already Integrated**:
- ✅ Schema endpoints cached
- ✅ Metrics endpoints cached

---

### ✅ Database Optimization
**File**: `src/sputnik/api/db.py`

**New Indexes Added**:
- `idx_query_history_model` - For model filtering
- `idx_query_history_confidence` - For confidence queries
- `idx_reviews_expert` - For expert filtering
- `idx_reviews_created` - For time-based queries

**Ready for Rollouts Table**:
- Can add `rollouts` table with same optimization pattern
- Indexes ready for `query_id`, `created_at`, `has_human_feedback`

---

### ✅ Query Optimization
**File**: `src/sputnik/api/query_optimizer.py`

**Usage**:
```python
from sputnik.api.query_optimizer import analyze_query_performance

analysis = analyze_query_performance(sql_query)
print(f"Complexity: {analysis['complexity']}")
print(f"Issues: {analysis['issues']}")
print(f"Suggestions: {analysis['suggestions']}")
```

---

### ✅ Enhanced Health Check
**Endpoint**: `GET /health`

**Checks**:
- Database connectivity
- Job queue status
- Job queue size

**Useful for**:
- Monitoring training job status
- Debugging issues

---

## Quick Start for Phase 12A (Rollout Collection)

### Step 1: Create RolloutsDB
Add to `src/sputnik/api/db.py`:

```python
class RolloutsDB:
    def __init__(self, db_path: str = "sputnik_history.duckdb"):
        self.db_path = db_path
        self._ensure_schema()
    
    def _ensure_schema(self):
        conn = duckdb.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rollouts (
                id VARCHAR PRIMARY KEY,
                query_id VARCHAR,
                query_text TEXT NOT NULL,
                final_answer TEXT,
                steps JSON NOT NULL,
                metadata JSON,
                model_id VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                has_human_feedback BOOLEAN DEFAULT FALSE,
                feedback_review_id VARCHAR,
                feedback_status VARCHAR,
                used_for_training BOOLEAN DEFAULT FALSE,
                training_batch_id VARCHAR,
                FOREIGN KEY (query_id) REFERENCES query_history(id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_rollouts_query_id ON rollouts(query_id);
            CREATE INDEX IF NOT EXISTS idx_rollouts_created ON rollouts(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_rollouts_feedback ON rollouts(has_human_feedback, used_for_training);
        """)
        conn.close()
```

### Step 2: Integrate Rollout Collection
In `src/sputnik/api/routes/query.py`, add:

```python
from sputnik.distill.rollout_collector import RolloutCollector

# In execute_query function:
collector = RolloutCollector()
rollout_builder = collector.start_rollout(request.question)

# During SQL generation, collect tokens:
# (Modify SQLGenerator to accept rollout_builder)

# After execution:
rollout_builder.set_final_answer(answer)
rollout = rollout_builder.build()

# Save to database
rollouts_db = get_rollouts_db()
rollout_id = rollouts_db.save_rollout(rollout, query_id=query_id)
```

### Step 3: Use Job Queue for Training
In `src/sputnik/api/routes/training.py` (new file):

```python
from sputnik.api.jobs import get_job_queue

@router.post("/training/start")
async def start_training():
    queue = get_job_queue()
    
    job_id = queue.enqueue(
        "training",
        train_model_function,
        rollouts=get_rollouts_for_training(),
    )
    
    return {"job_id": job_id, "status": "queued"}
```

---

## Files to Create Tomorrow

1. **RolloutsDB** - `src/sputnik/api/db.py` (add class)
2. **Training Routes** - `src/sputnik/api/routes/training.py` (new file)
3. **HumanFeedbackTeacher** - `src/sputnik/distill/teacher.py` (add class)
4. **Training Job** - `src/sputnik/distill/training_job.py` (new file)
5. **Model Checkpointer** - `src/sputnik/distill/checkpointer.py` (new file)

---

## Testing Checklist

Before starting distillation implementation:

- [ ] Test job queue: `queue.enqueue("test", lambda: "result")`
- [ ] Test cache: `cache.set("key", "value")`
- [ ] Test health check: `curl http://localhost:8000/health`
- [ ] Verify database indexes exist
- [ ] Test query optimization: `analyze_query_performance(sql)`

---

## Key Points

1. **Job Queue is Ready**: Use it for async training jobs
2. **Caching is Ready**: Reduces load during training
3. **Database is Optimized**: Fast queries for rollouts
4. **Health Check Works**: Monitor training status

---

## Next Steps (Tomorrow)

1. **Phase 12A**: Rollout Collection (2-3 days)
   - Create RolloutsDB
   - Integrate token collection
   - Persist rollouts

2. **Phase 12B**: Human Feedback Integration (3-4 days)
   - Create HumanFeedbackTeacher
   - Link reviews to rollouts
   - Map feedback to signals

3. **Phase 12C**: Training Pipeline (4-5 days)
   - Use job queue for training
   - Model checkpointing
   - Training metrics

---

## Documentation

- **Phase 6 Completion**: `PHASE6_COMPLETION.md`
- **Distillation Plan**: `DISTILLATION_IMPLEMENTATION_PLAN.md`
- **Enterprise Status**: `ENTERPRISE_READINESS_STATUS.md`

---

**Status**: ✅ READY FOR MVP IMPLEMENTATION

**You can start implementing on-policy distillation tomorrow!**
