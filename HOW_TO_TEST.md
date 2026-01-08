# How to Run Tests for Sputnik

This guide explains how to test the Sputnik system to verify completeness and functionality.

## Prerequisites

1. **Backend server running** on http://localhost:8000
2. **Frontend server running** on http://localhost:8080
3. **Demo database** exists (`demo_erp.duckdb`)

## Method 1: Manual Testing via Frontend (Recommended)

This is the easiest way to test the full integrated system.

### Steps:

1. **Start the servers** (if not already running):
   ```bash
   # Terminal 1 - Backend
   source .venv/bin/activate
   python scripts/start_server.py
   
   # Terminal 2 - Frontend
   cd frontend
   npm run dev
   ```

2. **Open the frontend** in your browser:
   ```
   http://localhost:8080
   ```

3. **Run test queries** in the QueryWorkspace:
   - Type a query in the "Query Input" box
   - Click "Execute" or press Cmd/Ctrl+Enter
   - Check the results

### Quick Test Queries (10 queries):

Copy and paste these one by one:

```
1. How many customers are there?
2. What is the total amount of all orders?
3. Show me all completed orders
4. List customers with their order counts
5. What is the average order amount?
6. Find unpaid invoices
7. Show orders from 2024
8. Which customer has the most orders?
9. Calculate total revenue
10. give info
```

### What to Check:

For each query, verify:
- ✅ Query executes without errors
- ✅ SQL is generated and displayed
- ✅ Results are shown correctly
- ✅ Answer is informative (not generic)
- ✅ Confidence is reasonable (not 1% or 100%)
- ✅ Risk level matches confidence
- ✅ Execution trace shows SQL and results

---

## Method 2: Automated Backend Testing

Test the backend API directly without the frontend.

### Quick Test Suite (10 queries):

```bash
# Make sure you're in the project root
cd /Users/stanislav/sputnik

# Activate virtual environment
source .venv/bin/activate

# Run quick tests
python scripts/run_tests.py --quick
```

### Test Specific Category:

```bash
# Test basic information queries
python scripts/run_tests.py --category "Basic Information"

# Test aggregations
python scripts/run_tests.py --category "Aggregations"

# Available categories:
# - Basic Information
# - Simple Retrieval
# - Aggregations
# - Filtered Queries
# - Joins
# - Complex Analysis
```

### Run All Comprehensive Tests:

```bash
python scripts/run_tests.py --all
```

### Expected Output:

```
============================================================
Sputnik Quick Test Suite
============================================================

✓ Connected to database: demo_erp.duckdb
✓ Found 4 tables

Test 1/10: How many customers are there?
  ✓ Success - Generated 1 SQL query(ies)
  ✓ Returned 1 rows

Test 2/10: What is the total amount of all orders?
  ✓ Success - Generated 1 SQL query(ies)
  ✓ Returned 1 rows

...

============================================================
Test Summary: 10 passed, 0 failed out of 10 tests
============================================================
```

---

## Method 3: API Testing with curl

Test the API endpoints directly using curl.

### Test Health Endpoint:

```bash
curl http://localhost:8000/health
```

Expected: `{"status":"healthy"}`

### Test Schema Endpoint:

```bash
curl http://localhost:8000/api/v1/schema
```

Expected: JSON with tables and relationships

### Test Models Endpoint:

```bash
curl http://localhost:8000/api/v1/models
```

Expected: JSON with available models

### Test Query Endpoint:

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How many customers are there?"}'
```

Expected: JSON with answer, SQL queries, confidence, and results

### Test with Model Selection:

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the total amount of all orders?",
    "model_id": "ollama:llama3"
  }'
```

---

## Method 4: Comprehensive Test Suite

Use the full test prompt catalog for thorough testing.

### View All Test Prompts:

```bash
cat TEST_PROMPTS.md
```

### Test Categories:

1. **Basic Information** - Simple counts
2. **Simple Retrieval** - Basic SELECT
3. **Aggregations** - SUM, AVG, MAX, MIN
4. **Filtered Queries** - WHERE clauses
5. **Date/Time Queries** - Temporal filtering
6. **Join Queries** - Table relationships
7. **Complex Analysis** - Multi-step queries
8. **Grouping** - GROUP BY
9. **Edge Cases** - Error handling
10. **Schema Exploration** - Database structure
11. **Comparative Queries** - Rankings
12. **Conditional Logic** - CASE statements
13. **NULL Handling** - Missing data
14. **Model Selection** - Different LLM models
15. **Performance** - Large datasets
16. **Natural Language** - Phrasing variations
17. **Multi-Part Questions** - Complex queries
18. **Business Intelligence** - Analytical queries

---

## Troubleshooting

### Backend Not Running:

```bash
# Check if backend is running
curl http://localhost:8000/health

# If not, start it:
source .venv/bin/activate
python scripts/start_server.py
```

### Frontend Not Running:

```bash
# Check if frontend is running
curl http://localhost:8080

# If not, start it:
cd frontend
npm run dev
```

### Database Not Found:

```bash
# Create demo database
python scripts/setup_demo_db.py
```

### Tests Failing:

1. Check backend logs for errors
2. Verify database exists and has data
3. Check that all dependencies are installed:
   ```bash
   pip install -e .
   ```

### Import Errors:

```bash
# Make sure you're in the project root
cd /Users/stanislav/sputnik

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -e .
```

---

## Success Criteria

Your system is working correctly if:

✅ **Quick Tests (10 queries)** - All pass
✅ **Basic Queries** - Return correct counts/values
✅ **Complex Queries** - Generate valid SQL with JOINs
✅ **Error Handling** - Graceful error messages
✅ **Confidence Scores** - Reasonable values (not 1% or 100%)
✅ **Risk Assessment** - Matches confidence level
✅ **Answer Quality** - Informative, not generic
✅ **Execution Trace** - Shows SQL and results
✅ **Model Selection** - Works in frontend
✅ **Schema Loading** - Tables appear in ContextPanel

---

## Quick Reference

```bash
# Start backend
python scripts/start_server.py

# Start frontend
cd frontend && npm run dev

# Run quick tests
python scripts/run_tests.py --quick

# Run all tests
python scripts/run_tests.py --all

# Test specific category
python scripts/run_tests.py --category "Basic Information"
```

---

## Next Steps

After running tests:

1. **Review Results** - Check which queries pass/fail
2. **Fix Issues** - Address any failing tests
3. **Improve Answers** - Enhance answer generation for generic responses
4. **Optimize Performance** - Speed up slow queries
5. **Add More Tests** - Expand test coverage

For a complete list of test prompts, see `TEST_PROMPTS.md`.
