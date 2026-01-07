# Technical Documentation

This document provides deep technical details about Sputnik's on-policy distillation algorithm and architecture.

## On-Policy Distillation

Sputnik uses **on-policy distillation** to improve reliability over time. Unlike traditional reinforcement learning with sparse rewards, distillation provides dense, per-token learning signals that enable faster and more stable learning.

### Core Algorithm

The training process follows these steps:

1. **Rollout Collection**: The student agent generates trajectories (sequences of tokens and tool calls) in response to business questions.

2. **Teacher Scoring**: A teacher model scores each token in the student's trajectory, providing per-token log probabilities.

3. **Reverse KL Computation**: For each token, we compute:
   ```
   reverse_kl = student_logprob - teacher_logprob
   advantage = -reverse_kl
   ```

4. **Training Signal**: The advantage signal is used to update the student model, encouraging tokens that align with the teacher's expectations.

5. **Discount Factor**: Currently set to 0, meaning we optimize next-token behavior (no temporal discounting).

### Why Reverse KL?

Reverse KL divergence (`KL(P_student || P_teacher)`) measures how much the student's distribution differs from the teacher's. By minimizing reverse KL, we encourage the student to:

- **Match teacher behavior**: Generate tokens that the teacher considers likely
- **Avoid overconfidence**: Prevent the student from being too confident in unlikely tokens
- **Improve alignment**: Better align with the teacher's understanding of correct behavior

The advantage signal (`-reverse_kl`) is positive when the student is better aligned with the teacher, providing a natural learning signal.

### Why Per-Token Signals?

Traditional RL approaches use sparse rewards (e.g., "correct answer" = +1, "incorrect" = -1). This creates several problems:

- **Credit assignment**: Hard to know which tokens led to success/failure
- **Sample efficiency**: Requires many rollouts to learn
- **Stability**: Sparse signals lead to high variance gradients

Per-token signals provide:

- **Dense feedback**: Every token gets a learning signal
- **Faster learning**: More information per rollout
- **Stability**: Lower variance, smoother gradients

### Data Structures

#### Token

```python
@dataclass
class Token:
    text: str
    logprob: float  # Student's log probability for this token
    token_id: Optional[int] = None
```

#### TrajectoryStep

```python
@dataclass
class TrajectoryStep:
    tokens: List[Token]
    tool_calls: List[ToolCall]
    step_index: int
```

#### Rollout

```python
@dataclass
class Rollout:
    query: str
    steps: List[TrajectoryStep]
    final_answer: str
    metadata: Dict[str, Any]
```

### Teacher Interface

The teacher model must implement:

```python
class Teacher:
    def score_tokens(self, tokens: List[Token], context: str) -> List[float]:
        """
        Score tokens with per-token log probabilities.
        
        Returns:
            List of log probabilities, one per token
        """
        raise NotImplementedError
```

In production, this would call a real teacher model (e.g., GPT-4, Claude) via API. The current implementation includes a `MockTeacher` for testing.

### Training Loop

```
┌─────────────────────────────────────────────────────────┐
│                    Training Loop                         │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────┐
        │  Collect Student Rollouts │
        │  (on-policy: student's     │
        │   own trajectories)        │
        └───────────────┬───────────┘
                        │
                        ▼
        ┌───────────────────────────┐
        │  Teacher Scores Tokens    │
        │  (per-token logprobs)     │
        └───────────────┬───────────┘
                        │
                        ▼
        ┌───────────────────────────┐
        │  Compute Reverse KL       │
        │  reverse_kl = student -   │
        │              teacher      │
        └───────────────┬───────────┘
                        │
                        ▼
        ┌───────────────────────────┐
        │  Compute Advantages       │
        │  advantage = -reverse_kl  │
        └───────────────┬───────────┘
                        │
                        ▼
        ┌───────────────────────────┐
        │  Apply Discount Factor    │
        │  (currently 0 = next-     │
        │   token optimization)     │
        └───────────────┬───────────┘
                        │
                        ▼
        ┌───────────────────────────┐
        │  Update Student Model     │
        │  (backpropagation)        │
        └───────────────────────────┘
```

### Why This Improves Reliability in ERP Environments

ERP systems require:

1. **Accuracy**: Incorrect SQL queries can lead to wrong business decisions
2. **Safety**: Destructive operations must be prevented
3. **Consistency**: Similar questions should produce similar, correct results
4. **Adaptation**: The system should improve as it sees more real-world usage

On-policy distillation addresses these needs:

- **Accuracy**: Teacher model (e.g., GPT-4) provides high-quality supervision
- **Safety**: Learning from teacher's safe behavior patterns
- **Consistency**: Dense signals help learn consistent patterns
- **Adaptation**: Continuous learning from real rollouts

### Implementation Details

#### Tokenization

Currently, Sputnik uses a simple whitespace tokenizer abstraction. In production, this would be replaced with the actual tokenizer used by the student model.

#### Student Logprobs

The student model must provide log probabilities for each generated token. These are used in the reverse KL computation.

#### Mock Components

For testing and development, Sputnik includes mock implementations:

- **MockTeacher**: Returns deterministic fake logprobs (hash-based)
- **Mock Student**: Generates deterministic pseudo-logprobs
- **Simple SQL Generator**: Rule-based SQL generation

These can be replaced with real LLM integrations.

### Future Extensions

- **Discount Factor > 0**: Temporal discounting for multi-step reasoning
- **Human Feedback**: Incorporate human ratings into teacher scores
- **Active Learning**: Select queries that maximize learning
- **Model Versioning**: Track and rollback model versions
- **Fine-tuning Pipeline**: Automated fine-tuning from collected rollouts

## Architecture Components

### Agent Module

- **Planner**: Breaks down business questions into execution steps
- **SQL Generator**: Converts natural language to SQL queries
- **Tool Router**: Executes tool calls (SQL queries, etc.)

### Environment Module

- **DuckDBEnv**: DuckDB-based ERP simulation
- **Schema Introspection**: Extracts table and relationship information

### Distillation Module

- **RolloutCollector**: Collects agent rollouts
- **Teacher**: Interface for teacher models
- **ReverseKL**: Computes reverse KL divergence
- **Trainer**: Training loop and metrics

### Evaluation Module

- **Metrics**: Accuracy, SQL validity, response quality
- **Runner**: Evaluation framework

## References

- Reverse KL divergence and its properties
- On-policy learning algorithms
- Distillation techniques for language models
- ERP system architectures

