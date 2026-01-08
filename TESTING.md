# Testing the Backend-Frontend Integration

## Servers Status

✅ **Backend API**: Running on http://localhost:8000
✅ **Frontend**: Running on http://localhost:8080
✅ **Demo Database**: `demo_erp.duckdb` exists

## Quick Test Steps

### 1. Open the Frontend
Open your browser and navigate to:
```
http://localhost:8080
```

### 2. Test Schema Loading
- The **ContextPanel** (left sidebar) should automatically load and display:
  - Available tables: `customers`, `orders`, `invoices`, `inventory_movements`
  - Table column counts

### 3. Test Model Selection
- Click the **Model Selector** in the header (brain icon)
- You should see available models (Ollama and/or OpenRouter)
- Select a model (it will be saved to localStorage)

### 4. Test Query Execution
Try these example queries in the **QueryWorkspace**:

**Simple queries:**
- "How many customers are there?"
- "What is the total amount of all orders?"
- "Show me all unpaid invoices"
- "How many inventory movements are there?"

**More complex queries:**
- "What is the total revenue from completed orders?"
- "List all customers from USA"
- "Show me orders with total amount greater than 2000"

### 5. Verify Results
After executing a query, you should see:
- ✅ **System Response**: The answer to your question
- ✅ **Execution Trace**: 
  - Generated SQL queries
  - Execution results
  - Table lineage
  - Filters applied
  - Any warnings or errors

### 6. Test Error Handling
Try an invalid query or check what happens when:
- Backend is not running (should show error toast)
- Invalid SQL is generated (should show in execution trace)

## API Endpoints to Test

You can also test the API directly:

```bash
# Health check
curl http://localhost:8000/health

# Get schema
curl http://localhost:8000/api/v1/schema

# List models
curl http://localhost:8000/api/v1/models

# Execute a query
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How many customers are there?"}'
```

## Expected Behavior

### ✅ Success Indicators:
- Frontend loads without errors
- Schema panel shows tables
- Model selector shows available models
- Queries execute and show results
- SQL queries are displayed in execution trace
- Toast notifications appear for success/errors
- Loading states show during API calls

### ⚠️ Common Issues:

1. **Backend not running**: 
   - Check terminal for backend server
   - Restart: `python scripts/start_server.py`

2. **Frontend not running**:
   - Check terminal for frontend server
   - Restart: `cd frontend && npm run dev`

3. **CORS errors**:
   - Backend CORS is configured for localhost:8080
   - Check browser console for errors

4. **Database not found**:
   - Run: `python scripts/setup_demo_db.py`

5. **No models available**:
   - Check if Ollama is running: `curl http://localhost:11434/api/tags`
   - Or set `OPENROUTER_API_KEY` environment variable

## Database Schema

The demo database contains:
- **customers**: id, name, email, created_at, country
- **orders**: id, customer_id, order_date, total_amount, status
- **invoices**: id, order_id, invoice_date, amount, paid
- **inventory_movements**: id, product_id, movement_type, quantity, movement_date, warehouse_id

## Next Steps

Once basic testing passes:
1. Test with different model selections
2. Try more complex analytical questions
3. Verify error handling with edge cases
4. Check that all UI components update correctly
5. Test the review queue and reliability dashboard (if implemented)
