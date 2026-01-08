# On-Policy Distillation with Human Feedback - Implementation Plan

## Overview

This document provides a detailed, step-by-step implementation plan for integrating on-policy distillation with human feedback into Sputnik. The goal is to continuously improve model performance by learning from expert human feedback.

## Architecture

```
Query Execution → Rollout Collection → Human Feedback → Teacher Signals → Training → Model Checkpoint → Production
```

### Key Components

1. **Rollout Collection**: Capture token-level trajectories during query execution
2. **Human Feedback**: Expert reviews provide ground truth signals
3. **Teacher Model**: Generates training signals from human feedback
4. **Training Pipeline**: Processes rollouts and updates model
5. **Model Management**: Checkpointing, versioning, deployment

---

## Phase 12A: Rollout Collection Integration

### Step 1: Extract Tokens from LLM Responses

**File**: `src/sputnik/llm/client.py`

**Task**: Modify LLM clients to return token-level logprobs.

```python
# Add to LLMClient interface
async def generate_with_logprobs(
    self,
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1000,
) -> Tuple[str, List[Token]]:
    """
    Generate text and return tokens with logprobs.
    
    Returns:
        Tuple of (generated_text, list_of_tokens_with_logprobs)
    """
    raise NotImplementedError
```

**Implementation for OpenRouterClient**:
- OpenRouter API supports `logprobs` parameter
- Parse response to extract tokens and logprobs
- Map to `Token` objects

**Implementation for OllamaClient**:
- Ollama may not support logprobs directly
- Use model's internal probabilities if available
- Fallback: Estimate logprobs from token frequencies

**Files to Modify**:
- `src/sputnik/llm/openrouter_client.py`
- `src/sputnik/llm/ollama_client.py`
- `src/sputnik/llm/client.py` (interface)

---

### Step 2: Integrate Rollout Collection into Query Execution

**File**: `src/sputnik/api/routes/query.py`

**Task**: Collect rollouts during query execution.

```python
from sputnik.distill.rollout_collector import RolloutCollector
from sputnik.types import Token, ToolCall, TrajectoryStep

# In execute_query function:
collector = RolloutCollector()
rollout_builder = collector.start_rollout(request.question)

# During SQL generation:
sql_generator = SQLGenerator(schema, llm_client=llm_client)
# Modify SQLGenerator to accept rollout_builder and collect tokens
sql_queries = sql_generator.generate(
    request.question, 
    request.context,
    rollout_builder=rollout_builder  # NEW
)

# After execution:
rollout_builder.set_final_answer(answer)
rollout_builder.add_metadata("query_id", query_id)
rollout_builder.add_metadata("confidence", confidence)
rollout = rollout_builder.build()

# Save rollout to database
rollouts_db = get_rollouts_db()
rollout_id = rollouts_db.save_rollout(rollout, query_id=query_id)
```

**Files to Modify**:
- `src/sputnik/api/routes/query.py`
- `src/sputnik/agent/sql_generator.py` - Add rollout collection
- `src/sputnik/agent/planner.py` - Add rollout collection (if needed)

---

### Step 3: Modify SQLGenerator to Collect Tokens

**File**: `src/sputnik/agent/sql_generator.py`

**Task**: Capture tokens during SQL generation.

```python
def generate(
    self, 
    query: str, 
    context: Optional[List[str]] = None,
    rollout_builder: Optional[RolloutBuilder] = None  # NEW
) -> List[SQLQuery]:
    """Generate SQL with optional rollout collection."""
    
    # Call LLM with logprobs
    if rollout_builder:
        text, tokens = await self.llm_client.generate_with_logprobs(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.2,
            max_tokens=500,
        )
        
        # Extract tool calls (SQL execution)
        tool_calls = [ToolCall(
            tool_name="execute_sql",
            arguments={"query": sql},
        ) for sql in sql_queries]
        
        # Add step to rollout
        rollout_builder.add_step(tokens=tokens, tool_calls=tool_calls)
    else:
        # Original behavior (no rollout collection)
        text = await self.llm_client.generate(...)
```

**Files to Modify**:
- `src/sputnik/agent/sql_generator.py`

---

### Step 4: Create Rollout Persistence Layer

**File**: `src/sputnik/api/db.py`

**Task**: Add RolloutsDB class.

```python
class RolloutsDB:
    """Database for storing agent rollouts."""
    
    def __init__(self, db_path: str = "sputnik_history.duckdb"):
        self.db_path = db_path
        self._ensure_schema()
    
    def _ensure_schema(self):
        """Create rollouts table if it doesn't exist."""
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
    
    def save_rollout(self, rollout: Rollout, query_id: str) -> str:
        """Save rollout to database."""
        import uuid
        import json
        
        rollout_id = str(uuid.uuid4())
        conn = duckdb.connect(self.db_path)
        
        # Serialize steps to JSON
        steps_json = json.dumps([
            {
                "tokens": [
                    {"text": t.text, "logprob": t.logprob, "token_id": t.token_id}
                    for t in step.tokens
                ],
                "tool_calls": [
                    {
                        "tool_name": tc.tool_name,
                        "arguments": tc.arguments,
                        "result": str(tc.result) if tc.result else None,
                    }
                    for tc in step.tool_calls
                ],
                "step_index": step.step_index,
            }
            for step in rollout.steps
        ])
        
        conn.execute("""
            INSERT INTO rollouts (
                id, query_id, query_text, final_answer, steps, metadata, model_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [
            rollout_id,
            query_id,
            rollout.query,
            rollout.final_answer,
            steps_json,
            json.dumps(rollout.metadata),
            rollout.metadata.get("model_id"),
        ])
        conn.close()
        return rollout_id
    
    def get_rollout(self, rollout_id: str) -> Optional[dict]:
        """Get rollout by ID."""
        # Implementation...
    
    def get_rollouts_for_training(
        self, 
        limit: int = 100,
        has_feedback: bool = True,
        used_for_training: bool = False,
    ) -> List[dict]:
        """Get rollouts ready for training."""
        # Implementation...
```

**Files to Create/Modify**:
- `src/sputnik/api/db.py` - Add RolloutsDB class

---

### Step 5: Enhance Rollout API Endpoints

**File**: `src/sputnik/api/routes/rollouts.py`

**Task**: Add endpoints for rollout management.

```python
@router.get("/rollouts", response_model=RolloutsListResponse)
async def list_rollouts(
    query_id: Optional[str] = None,
    has_feedback: Optional[bool] = None,
    used_for_training: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
) -> RolloutsListResponse:
    """List rollouts with filtering."""
    # Implementation...

@router.get("/rollouts/{rollout_id}", response_model=RolloutDetailResponse)
async def get_rollout(rollout_id: str) -> RolloutDetailResponse:
    """Get specific rollout."""
    # Implementation...

@router.get("/queries/{query_id}/rollout", response_model=RolloutDetailResponse)
async def get_rollout_for_query(query_id: str) -> RolloutDetailResponse:
    """Get rollout for a specific query."""
    # Implementation...
```

**Files to Modify**:
- `src/sputnik/api/routes/rollouts.py`

---

## Phase 12B: Human Feedback Integration

### Step 1: Create HumanFeedbackTeacher

**File**: `src/sputnik/distill/teacher.py`

**Task**: Implement teacher that uses human feedback.

```python
class HumanFeedbackTeacher(Teacher):
    """Teacher model that uses human expert feedback."""
    
    def __init__(self, reviews_db: ReviewsDB):
        self.reviews_db = reviews_db
    
    def score_tokens(
        self, 
        tokens: List[Token], 
        context: str,
        rollout_id: Optional[str] = None,
    ) -> List[float]:
        """
        Score tokens based on human feedback.
        
        If rollout has associated review:
        - Approved: Positive signal (student aligned with expert)
        - Rejected: Negative signal (student misaligned)
        - Edited: Use corrected_answer to generate teacher tokens
        """
        if not rollout_id:
            # No feedback available, return neutral scores
            return [0.0] * len(tokens)
        
        # Get review for this rollout
        review = self.reviews_db.get_review_by_rollout_id(rollout_id)
        if not review:
            return [0.0] * len(tokens)
        
        if review["status"] == "approved":
            # Expert approved: student was correct
            # Return student's logprobs (no change needed)
            return [token.logprob for token in tokens]
        
        elif review["status"] == "rejected":
            # Expert rejected: student was wrong
            # Return low logprobs (discourage this path)
            return [-10.0] * len(tokens)  # Very low probability
        
        elif review["status"] == "approved" and review.get("corrected_answer"):
            # Expert edited: use corrected answer as teacher signal
            # Generate teacher tokens from corrected_answer
            teacher_tokens = self._generate_teacher_tokens(
                corrected_answer=review["corrected_answer"],
                context=context,
            )
            # Compute teacher logprobs for student's tokens
            return self._compute_teacher_logprobs(tokens, teacher_tokens)
        
        return [0.0] * len(tokens)
    
    def _generate_teacher_tokens(self, corrected_answer: str, context: str) -> List[Token]:
        """Generate teacher's preferred tokens from corrected answer."""
        # Use LLM to generate tokens for corrected answer
        # This would call an LLM to tokenize the corrected answer
        # For now, simplified version:
        # TODO: Implement proper tokenization
        pass
    
    def _compute_teacher_logprobs(
        self, 
        student_tokens: List[Token],
        teacher_tokens: List[Token],
    ) -> List[float]:
        """Compute teacher logprobs for student tokens."""
        # Align student and teacher tokens
        # Compute teacher's logprob for each student token
        # TODO: Implement alignment algorithm
        pass
```

**Files to Modify**:
- `src/sputnik/distill/teacher.py` - Add HumanFeedbackTeacher

---

### Step 2: Link Reviews to Rollouts

**File**: `src/sputnik/api/routes/reviews.py`

**Task**: When review is created/updated, link to rollout.

```python
@router.post("/reviews/{review_id}/approve")
async def approve_review(...):
    # ... existing code ...
    
    # Link review to rollout
    rollouts_db = get_rollouts_db()
    rollouts_db.link_review_to_rollout(
        review_id=review_id,
        query_id=review["query_id"],
        feedback_status="approved",
    )
    
    return {"message": "Review approved", "review_id": review_id}
```

**Files to Modify**:
- `src/sputnik/api/routes/reviews.py` - Link reviews in all review actions
- `src/sputnik/api/db.py` - Add `link_review_to_rollout` method

---

### Step 3: Create Feedback Mapper

**File**: `src/sputnik/distill/feedback_mapper.py` (NEW)

**Task**: Map human feedback to teacher signals.

```python
class FeedbackMapper:
    """Maps human feedback to teacher training signals."""
    
    def map_review_to_teacher_signal(
        self,
        review: dict,
        rollout: Rollout,
    ) -> List[float]:
        """
        Map expert review to teacher logprobs.
        
        Returns:
            List of teacher logprobs (one per token in rollout)
        """
        if review["status"] == "approved" and not review.get("corrected_answer"):
            # Simple approval: student was correct
            return [token.logprob for step in rollout.steps for token in step.tokens]
        
        elif review["status"] == "rejected":
            # Rejection: student was wrong
            return [-5.0] * sum(len(step.tokens) for step in rollout.steps)
        
        elif review.get("corrected_answer"):
            # Expert provided correction: use as teacher signal
            return self._generate_teacher_signal_from_correction(
                corrected_answer=review["corrected_answer"],
                rollout=rollout,
            )
        
        return [0.0] * sum(len(step.tokens) for step in rollout.steps)
    
    def _generate_teacher_signal_from_correction(
        self,
        corrected_answer: str,
        rollout: Rollout,
    ) -> List[float]:
        """Generate teacher signal from expert's corrected answer."""
        # Use LLM to generate teacher tokens for corrected answer
        # Align with student tokens
        # Return teacher logprobs
        # TODO: Implement
        pass
```

**Files to Create**:
- `src/sputnik/distill/feedback_mapper.py`

---

## Phase 12C: Training Pipeline

### Step 1: Create Training Job System

**File**: `src/sputnik/distill/training_job.py` (NEW)

**Task**: Manage training runs.

```python
class TrainingJob:
    """Manages a single training run."""
    
    def __init__(
        self,
        trainer: DistillationTrainer,
        rollouts_db: RolloutsDB,
        checkpointer: ModelCheckpointer,
    ):
        self.trainer = trainer
        self.rollouts_db = rollouts_db
        self.checkpointer = checkpointer
        self.job_id = str(uuid.uuid4())
        self.status = "pending"
        self.metrics = {}
    
    async def run(self) -> dict:
        """Execute training job."""
        self.status = "running"
        start_time = time.time()
        
        try:
            # Get rollouts with feedback
            rollouts_data = self.rollouts_db.get_rollouts_for_training(
                limit=100,
                has_feedback=True,
                used_for_training=False,
            )
            
            if not rollouts_data:
                return {"status": "no_rollouts", "message": "No rollouts to train on"}
            
            # Deserialize rollouts
            rollouts = [self._deserialize_rollout(rd) for rd in rollouts_data]
            
            # Compute training signals
            all_signals = []
            for rollout in rollouts:
                signals = self.trainer.compute_training_signal(rollout)
                all_signals.extend(signals)
            
            # Training step (in real implementation, this would update model weights)
            metrics = self.trainer.train_step(rollouts)
            
            # Save checkpoint
            checkpoint_id = self.checkpointer.save_checkpoint(
                model_version=f"v{int(time.time())}",
                metrics=metrics,
                num_rollouts=len(rollouts),
            )
            
            # Mark rollouts as used
            for rd in rollouts_data:
                self.rollouts_db.mark_used_for_training(rd["id"], self.job_id)
            
            # Save training run
            training_time = time.time() - start_time
            self.metrics = {
                **metrics,
                "training_time": training_time,
                "checkpoint_id": checkpoint_id,
            }
            
            self.status = "completed"
            return {"status": "completed", "metrics": self.metrics}
            
        except Exception as e:
            self.status = "failed"
            return {"status": "failed", "error": str(e)}
    
    def _deserialize_rollout(self, rollout_data: dict) -> Rollout:
        """Deserialize rollout from database."""
        # Implementation...
```

**Files to Create**:
- `src/sputnik/distill/training_job.py`

---

### Step 2: Create Model Checkpointer

**File**: `src/sputnik/distill/checkpointer.py` (NEW)

**Task**: Save and load model checkpoints.

```python
class ModelCheckpointer:
    """Manages model checkpoints."""
    
    def __init__(self, checkpoint_dir: str = "checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)
        self.db = ModelCheckpointsDB()
    
    def save_checkpoint(
        self,
        model_version: str,
        metrics: dict,
        num_rollouts: int,
        model_state: Optional[dict] = None,  # In real implementation, actual model weights
    ) -> str:
        """Save model checkpoint."""
        checkpoint_id = str(uuid.uuid4())
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.ckpt"
        
        # In real implementation, save model weights
        # For now, save metadata
        checkpoint_data = {
            "checkpoint_id": checkpoint_id,
            "model_version": model_version,
            "metrics": metrics,
            "num_rollouts": num_rollouts,
            "created_at": datetime.now().isoformat(),
            "model_state": model_state,  # Would be actual weights
        }
        
        with open(checkpoint_path, "w") as f:
            json.dump(checkpoint_data, f)
        
        # Save to database
        self.db.save_checkpoint(
            checkpoint_id=checkpoint_id,
            version=model_version,
            checkpoint_path=str(checkpoint_path),
            metrics=metrics,
        )
        
        return checkpoint_id
    
    def load_checkpoint(self, checkpoint_id: str) -> dict:
        """Load model checkpoint."""
        checkpoint = self.db.get_checkpoint(checkpoint_id)
        if not checkpoint:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")
        
        checkpoint_path = Path(checkpoint["checkpoint_path"])
        with open(checkpoint_path, "r") as f:
            return json.load(f)
    
    def get_production_checkpoint(self) -> Optional[dict]:
        """Get current production checkpoint."""
        checkpoint = self.db.get_production_checkpoint()
        if checkpoint:
            return self.load_checkpoint(checkpoint["id"])
        return None
```

**Files to Create**:
- `src/sputnik/distill/checkpointer.py`
- `src/sputnik/api/db.py` - Add ModelCheckpointsDB class

---

### Step 3: Create Training API Endpoints

**File**: `src/sputnik/api/routes/training.py` (NEW)

**Task**: API endpoints for training management.

```python
@router.post("/training/start")
async def start_training() -> dict:
    """Start a new training job."""
    # Implementation...

@router.get("/training/runs")
async def list_training_runs(
    limit: int = 50,
    offset: int = 0,
) -> TrainingRunsResponse:
    """List training runs."""
    # Implementation...

@router.get("/training/runs/{run_id}")
async def get_training_run(run_id: str) -> TrainingRunResponse:
    """Get training run details."""
    # Implementation...

@router.post("/training/checkpoints/{checkpoint_id}/deploy")
async def deploy_checkpoint(checkpoint_id: str) -> dict:
    """Deploy checkpoint to production."""
    # Implementation...
```

**Files to Create**:
- `src/sputnik/api/routes/training.py`

---

## Phase 12D: Real Teacher Model

### Step 1: Implement LLMTeacher

**File**: `src/sputnik/distill/teacher.py`

**Task**: Teacher that uses a strong LLM.

```python
class LLMTeacher(Teacher):
    """Teacher model using a strong LLM (e.g., GPT-4, Claude)."""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
    
    def score_tokens(self, tokens: List[Token], context: str) -> List[float]:
        """Score tokens using teacher LLM."""
        # Generate teacher's preferred response
        teacher_response = await self.llm_client.generate(
            prompt=context,
            temperature=0.0,  # Deterministic
        )
        
        # Get teacher tokens with logprobs
        teacher_tokens, teacher_logprobs = await self.llm_client.generate_with_logprobs(
            prompt=context,
            temperature=0.0,
        )
        
        # Align student tokens with teacher tokens
        # Compute teacher logprob for each student token
        aligned_logprobs = self._align_tokens(tokens, teacher_tokens, teacher_logprobs)
        
        return aligned_logprobs
    
    def _align_tokens(
        self,
        student_tokens: List[Token],
        teacher_tokens: List[Token],
        teacher_logprobs: List[float],
    ) -> List[float]:
        """Align student and teacher tokens."""
        # Simple alignment: match by text
        # More sophisticated: use edit distance or BLEU alignment
        # TODO: Implement proper alignment
        pass
```

**Files to Modify**:
- `src/sputnik/distill/teacher.py` - Add LLMTeacher

---

### Step 2: Create Hybrid Teacher

**File**: `src/sputnik/distill/teacher.py`

**Task**: Combine human feedback and LLM teacher.

```python
class HybridTeacher(Teacher):
    """Combines human feedback and LLM teacher."""
    
    def __init__(
        self,
        human_teacher: HumanFeedbackTeacher,
        llm_teacher: LLMTeacher,
        human_weight: float = 0.7,  # Prefer human feedback when available
    ):
        self.human_teacher = human_teacher
        self.llm_teacher = llm_teacher
        self.human_weight = human_weight
    
    def score_tokens(
        self,
        tokens: List[Token],
        context: str,
        rollout_id: Optional[str] = None,
    ) -> List[float]:
        """Score tokens using hybrid approach."""
        # Try human feedback first
        human_logprobs = self.human_teacher.score_tokens(
            tokens, context, rollout_id=rollout_id
        )
        
        # Check if human feedback is available (non-zero scores)
        has_human_feedback = any(logprob != 0.0 for logprob in human_logprobs)
        
        if has_human_feedback:
            # Use human feedback with LLM as fallback
            llm_logprobs = self.llm_teacher.score_tokens(tokens, context)
            
            # Weighted combination
            combined = [
                self.human_weight * h + (1 - self.human_weight) * l
                for h, l in zip(human_logprobs, llm_logprobs)
            ]
            return combined
        else:
            # No human feedback: use LLM teacher only
            return self.llm_teacher.score_tokens(tokens, context)
```

**Files to Modify**:
- `src/sputnik/distill/teacher.py` - Add HybridTeacher

---

## Phase 12E: Training UI

### Step 1: Create Training Dashboard Component

**File**: `frontend/src/components/training/TrainingDashboard.tsx` (NEW)

**Task**: Display training runs and metrics.

```typescript
export function TrainingDashboard() {
  const { data: runs, isLoading } = useTrainingRuns();
  const { data: metrics } = useTrainingMetrics();
  
  return (
    <div className="space-y-6">
      <h1>Training Dashboard</h1>
      
      {/* Training Runs Table */}
      <Card>
        <CardHeader>
          <CardTitle>Training Runs</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Run ID</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Loss</TableHead>
                <TableHead>Advantage</TableHead>
                <TableHead>Rollouts</TableHead>
                <TableHead>Date</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {runs?.runs.map((run) => (
                <TableRow key={run.id}>
                  <TableCell>{run.id}</TableCell>
                  <TableCell>{run.status}</TableCell>
                  <TableCell>{run.metrics.loss?.toFixed(4)}</TableCell>
                  <TableCell>{run.metrics.mean_advantage?.toFixed(4)}</TableCell>
                  <TableCell>{run.metrics.num_rollouts}</TableCell>
                  <TableCell>{new Date(run.created_at).toLocaleString()}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
      
      {/* Metrics Charts */}
      <TrainingMetrics data={metrics} />
      
      {/* Start Training Button */}
      <Button onClick={() => startTraining.mutate()}>
        Start Training
      </Button>
    </div>
  );
}
```

**Files to Create**:
- `frontend/src/components/training/TrainingDashboard.tsx`
- `frontend/src/components/training/TrainingMetrics.tsx`
- `frontend/src/pages/Training.tsx`

---

## Testing Checklist

### Phase 12A: Rollout Collection
- [ ] Test token extraction from LLM responses
- [ ] Test rollout collection during query execution
- [ ] Test rollout persistence to database
- [ ] Test rollout retrieval API endpoints

### Phase 12B: Human Feedback
- [ ] Test HumanFeedbackTeacher with approved reviews
- [ ] Test HumanFeedbackTeacher with rejected reviews
- [ ] Test HumanFeedbackTeacher with edited reviews
- [ ] Test review-to-rollout linking

### Phase 12C: Training Pipeline
- [ ] Test training job execution
- [ ] Test model checkpointing
- [ ] Test training metrics tracking
- [ ] Test training API endpoints

### Phase 12D: Real Teacher
- [ ] Test LLMTeacher implementation
- [ ] Test HybridTeacher combination
- [ ] Test teacher fallback logic

### Phase 12E: Training UI
- [ ] Test training dashboard display
- [ ] Test metrics visualization
- [ ] Test start training button
- [ ] Test checkpoint deployment

---

## Success Criteria

1. **Rollout Collection**: 100% of queries generate rollouts with tokens
2. **Feedback Integration**: 80%+ of expert reviews linked to rollouts
3. **Training Frequency**: At least 1 training run per week
4. **Model Improvement**: 5-10% improvement in auto-answer rate per month
5. **Training Time**: < 1 hour per training run (for 100 rollouts)

---

## Next Steps After Implementation

1. **A/B Testing**: Compare trained model vs baseline
2. **Gradual Rollout**: Increase trained model usage over time
3. **Continuous Monitoring**: Track model performance metrics
4. **Feedback Loop**: Use model performance to improve training process
