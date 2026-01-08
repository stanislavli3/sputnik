# Component Implementation Guide

This guide provides step-by-step implementation details for each frontend component to make them enterprise-ready.

---

## 1. QueryWorkspace - Complete Integration

### Step 1: Add Query History API Hook

**File**: `frontend/src/hooks/use-api.ts`

```typescript
// Add to existing hooks
export interface QueryHistoryItem {
  id: string;
  question: string;
  answer: string;
  confidence: number;
  created_at: string;
  model_id?: string;
  execution_time_ms?: number;
}

export interface QueryHistoryResponse {
  queries: QueryHistoryItem[];
  total: number;
  page: number;
  page_size: number;
}

export const useQueryHistory = (page = 1, pageSize = 20) => {
  return useQuery({
    queryKey: ["query-history", page, pageSize],
    queryFn: async (): Promise<QueryHistoryResponse> => {
      return apiRequest<QueryHistoryResponse>(
        `/api/v1/queries/history?page=${page}&page_size=${pageSize}`
      );
    },
    staleTime: 30 * 1000, // 30 seconds
  });
};

export const useQueryTemplate = () => {
  return useMutation({
    mutationFn: async (queryId: string, templateName: string) => {
      return apiRequest("/api/v1/queries/templates", {
        method: "POST",
        body: {
          query_id: queryId,
          name: templateName,
        },
      });
    },
  });
};
```

### Step 2: Create Query History Sidebar Component

**File**: `frontend/src/components/workspace/QueryHistory.tsx` (NEW)

```typescript
import { useState } from "react";
import { Clock, Search, Bookmark, BookmarkCheck } from "lucide-react";
import { useQueryHistory } from "@/hooks/use-api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface QueryHistoryProps {
  onSelectQuery: (queryId: string) => void;
  selectedQueryId?: string;
}

export const QueryHistory = ({ onSelectQuery, selectedQueryId }: QueryHistoryProps) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [page, setPage] = useState(1);
  const { data, isLoading } = useQueryHistory(page, 20);

  const filteredQueries = data?.queries.filter((q) =>
    q.question.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  return (
    <div className="h-full flex flex-col border-r border-border">
      <div className="panel-header">
        <span>Query History</span>
      </div>
      
      <div className="p-2 border-b border-border">
        <div className="relative">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search queries..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-8"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-4 text-center text-xs text-muted-foreground">
            Loading history...
          </div>
        ) : filteredQueries.length === 0 ? (
          <div className="p-4 text-center text-xs text-muted-foreground">
            No queries found
          </div>
        ) : (
          <div className="space-y-1 p-2">
            {filteredQueries.map((query) => (
              <button
                key={query.id}
                onClick={() => onSelectQuery(query.id)}
                className={`w-full text-left p-2 rounded hover:bg-secondary transition-colors ${
                  selectedQueryId === query.id ? "bg-secondary border border-border" : ""
                }`}
              >
                <div className="text-xs font-medium truncate">{query.question}</div>
                <div className="flex items-center gap-2 mt-1 text-[10px] text-muted-foreground">
                  <Clock className="w-3 h-3" />
                  <span>{new Date(query.created_at).toLocaleDateString()}</span>
                  <span>•</span>
                  <span>{query.confidence}%</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {data && data.total > 20 && (
        <div className="p-2 border-t border-border flex items-center justify-between">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            Previous
          </Button>
          <span className="text-xs text-muted-foreground">
            Page {page} of {Math.ceil(data.total / 20)}
          </span>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setPage((p) => p + 1)}
            disabled={page >= Math.ceil(data.total / 20)}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
};
```

### Step 3: Update QueryWorkspace to Include History

**File**: `frontend/src/components/workspace/QueryWorkspace.tsx`

Add query history sidebar and integrate with existing code.

---

## 2. ExpertReviewQueue - Full Backend Integration

### Step 1: Create Review API Hooks

**File**: `frontend/src/hooks/use-api.ts` (additions)

```typescript
export interface ReviewItem {
  id: string;
  query_id: string;
  question: string;
  answer: string;
  confidence: number;
  risk: 'low' | 'medium' | 'high';
  submitted_by: string;
  submitted_at: string;
  wait_time?: string;
  priority: 'low' | 'medium' | 'high';
  status: 'pending' | 'approved' | 'rejected' | 'abstained';
}

export interface ReviewResponse {
  reviews: ReviewItem[];
  total: number;
}

export const useReviewQueue = (filters?: { priority?: string; status?: string }) => {
  const queryParams = new URLSearchParams();
  if (filters?.priority) queryParams.append('priority', filters.priority);
  if (filters?.status) queryParams.append('status', filters.status);

  return useQuery({
    queryKey: ["review-queue", filters],
    queryFn: async (): Promise<ReviewResponse> => {
      return apiRequest<ReviewResponse>(
        `/api/v1/reviews?${queryParams.toString()}`
      );
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });
};

export const useReviewActions = () => {
  const queryClient = useQueryClient();
  
  return {
    approve: useMutation({
      mutationFn: async (reviewId: string) => {
        return apiRequest(`/api/v1/reviews/${reviewId}/approve`, {
          method: "POST",
        });
      },
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ["review-queue"] });
        toast({ title: "Review approved", variant: "default" });
      },
    }),
    
    reject: useMutation({
      mutationFn: async (reviewId: string, reason: string) => {
        return apiRequest(`/api/v1/reviews/${reviewId}/reject`, {
          method: "POST",
          body: { reason },
        });
      },
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ["review-queue"] });
        toast({ title: "Review rejected", variant: "default" });
      },
    }),
    
    // Add other actions: edit, abstain, escalate
  };
};
```

### Step 2: Update ExpertReviewQueue Component

Replace mock data with real API calls using the hooks above.

---

## 3. ReliabilityDashboard - Metrics Integration

### Step 1: Create Metrics API Hooks

**File**: `frontend/src/hooks/use-api.ts` (additions)

```typescript
export interface ReliabilityMetrics {
  auto_answer_rate: number;
  expert_intervention: number;
  error_recurrence: number;
  avg_confidence: number;
  trust_score: number;
  trends: {
    auto_answer_rate: number[];
    expert_intervention: number[];
    error_recurrence: number[];
    avg_confidence: number[];
    trust_score: number[];
  };
}

export interface CategoryMetrics {
  category: string;
  queries: number;
  accuracy: number;
}

export interface ExpertCorrection {
  type: string;
  count: number;
  impact: 'learned' | 'partial' | 'pending';
}

export const useReliabilityMetrics = (period = '90d') => {
  return useQuery({
    queryKey: ["reliability-metrics", period],
    queryFn: async (): Promise<ReliabilityMetrics> => {
      return apiRequest<ReliabilityMetrics>(
        `/api/v1/metrics/overview?period=${period}`
      );
    },
    refetchInterval: 60000, // Refresh every minute
  });
};

export const useCategoryMetrics = () => {
  return useQuery({
    queryKey: ["category-metrics"],
    queryFn: async (): Promise<CategoryMetrics[]> => {
      return apiRequest<CategoryMetrics[]>("/api/v1/metrics/by-category");
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useExpertCorrections = () => {
  return useQuery({
    queryKey: ["expert-corrections"],
    queryFn: async (): Promise<ExpertCorrection[]> => {
      return apiRequest<ExpertCorrection[]>("/api/v1/metrics/expert-corrections");
    },
    staleTime: 5 * 60 * 1000,
  });
};
```

### Step 2: Update ReliabilityDashboard Component

Replace static data with API hooks and add real-time updates.

---

## 4. RiskPanel - Dynamic Risk Assessment

### Step 1: Create Risk Assessment Hook

**File**: `frontend/src/hooks/use-api.ts` (additions)

```typescript
export interface RiskAssessment {
  overall_risk: 'low' | 'medium' | 'high';
  confidence_factors: {
    query_interpretation: number;
    data_completeness: number;
    schema_match: number;
    historical_accuracy: number;
  };
  risk_factors: Array<{
    severity: 'high' | 'medium' | 'low' | 'info';
    title: string;
    description: string;
  }>;
  allowed_actions: string[];
}

export const useRiskAssessment = (queryId: string) => {
  return useQuery({
    queryKey: ["risk-assessment", queryId],
    queryFn: async (): Promise<RiskAssessment> => {
      return apiRequest<RiskAssessment>(`/api/v1/query/${queryId}/risk`);
    },
    enabled: !!queryId,
  });
};
```

### Step 2: Update RiskPanel Component

Connect to real risk assessment API.

---

## 5. ContextPanel - Enhanced Schema View

### Step 1: Enhanced Schema API Hook

**File**: `frontend/src/hooks/use-api.ts` (update existing)

```typescript
export interface TableStats {
  row_count: number;
  size_bytes: number;
  last_updated: string;
  column_count: number;
}

export interface EnhancedSchemaResponse extends SchemaResponse {
  table_stats: Record<string, TableStats>;
  data_quality: Record<string, {
    null_percentage: number;
    unique_values: number;
    completeness: number;
  }>;
}

export const useEnhancedSchema = () => {
  return useQuery({
    queryKey: ["schema-enhanced"],
    queryFn: async (): Promise<EnhancedSchemaResponse> => {
      return apiRequest<EnhancedSchemaResponse>("/api/v1/schema?include_stats=true");
    },
    staleTime: 5 * 60 * 1000,
  });
};
```

---

## Backend Implementation Tasks

### Task 1: Query History Endpoint

**File**: `src/sputnik/api/routes/query.py` (additions)

```python
@router.get("/queries/history")
async def get_query_history(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    http_request: Request = None,
) -> dict:
    """Get query history with pagination."""
    # Implementation: Query database for history
    # Return paginated results
    pass

@router.post("/queries/templates")
async def create_template(
    request: dict,
    http_request: Request,
) -> dict:
    """Create a query template."""
    # Implementation: Save template to database
    pass
```

### Task 2: Review Queue Endpoints

**File**: `src/sputnik/api/routes/reviews.py` (NEW)

```python
router = APIRouter()

@router.get("/reviews")
async def list_reviews(
    priority: Optional[str] = None,
    status: Optional[str] = None,
) -> ReviewResponse:
    """List pending reviews."""
    # Implementation
    pass

@router.post("/reviews/{review_id}/approve")
async def approve_review(
    review_id: str,
    request: dict,
) -> dict:
    """Approve a review."""
    # Implementation
    pass
```

### Task 3: Metrics Endpoints

**File**: `src/sputnik/api/routes/metrics.py` (NEW)

```python
router = APIRouter()

@router.get("/metrics/overview")
async def get_metrics_overview(
    period: str = "90d",
) -> dict:
    """Get overall reliability metrics."""
    # Calculate metrics from query history
    # Return aggregated data
    pass
```

---

## Database Schema for New Features

```sql
-- Query History
CREATE TABLE query_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR NOT NULL,
    question TEXT NOT NULL,
    sql_queries TEXT[] NOT NULL,
    answer TEXT,
    confidence FLOAT,
    execution_results JSONB,
    execution_time_ms INTEGER,
    model_id VARCHAR,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_query_history_user ON query_history(user_id);
CREATE INDEX idx_query_history_created ON query_history(created_at DESC);

-- Query Templates
CREATE TABLE query_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    category VARCHAR,
    question TEXT NOT NULL,
    sql_template TEXT,
    variables JSONB,
    created_by VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Reviews
CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id UUID REFERENCES query_history(id),
    expert_id VARCHAR NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'pending',
    correction_reason VARCHAR,
    expert_notes TEXT,
    corrected_answer TEXT,
    priority VARCHAR DEFAULT 'medium',
    created_at TIMESTAMP DEFAULT NOW(),
    reviewed_at TIMESTAMP
);

CREATE INDEX idx_reviews_status ON reviews(status);
CREATE INDEX idx_reviews_priority ON reviews(priority);
```

---

## Testing Checklist

For each component, verify:
- [ ] API integration works
- [ ] Loading states display correctly
- [ ] Error handling works
- [ ] Empty states are handled
- [ ] Real-time updates work (if applicable)
- [ ] Permissions are enforced
- [ ] Performance is acceptable
- [ ] Mobile responsive (if needed)

---

## Priority Order

**Week 1-2 (High Priority)**:
1. QueryWorkspace - Query history
2. ExpertReviewQueue - Backend integration
3. RiskPanel - Real risk assessment

**Week 3-4 (High Priority)**:
4. ReliabilityDashboard - Metrics integration
5. ContextPanel - Enhanced schema info

**Week 5+ (Medium/Low Priority)**:
6. Advanced features (templates, scheduling)
7. Analytics and reporting
8. Performance optimizations
