# Sputnik System Test Prompts

This document contains comprehensive test prompts to verify the completeness and functionality of the Sputnik system.

## Test Categories

### 1. Basic Information Queries
Test basic data retrieval and counting functionality.

```
✓ give info
✓ How many customers are there?
✓ What is the total number of orders?
✓ Count all invoices
✓ Show me the number of inventory movements
✓ How many records are in the customers table?
```

**Expected Results:**
- Should return numeric counts
- Confidence: 75-90%
- Risk: Low to Medium
- SQL should use COUNT(*)

---

### 2. Simple Data Retrieval
Test basic SELECT queries without aggregations.

```
✓ List all customers
✓ Show me all orders
✓ Display all invoices
✓ What customers do we have?
✓ Get all inventory movements
```

**Expected Results:**
- Should return multiple rows
- Answer should indicate number of results
- SQL should be simple SELECT statements

---

### 3. Aggregation Queries
Test SUM, AVG, MAX, MIN functions.

```
✓ What is the total amount of all orders?
✓ What is the average order amount?
✓ What is the maximum order amount?
✓ What is the minimum order amount?
✓ Calculate total revenue from orders
✓ What is the sum of all invoice amounts?
```

**Expected Results:**
- Should return calculated values
- SQL should use aggregation functions
- Answer should include the calculated number

---

### 4. Filtered Queries
Test WHERE clauses and filtering.

```
✓ Show me all completed orders
✓ List all unpaid invoices
✓ Find customers from USA
✓ Show orders with amount greater than 2000
✓ Get all invoices that are paid
✓ Find orders with status 'pending'
```

**Expected Results:**
- Should filter results correctly
- SQL should include WHERE clauses
- Answer should reflect filtered count

---

### 5. Date/Time Queries
Test temporal filtering and date operations.

```
✓ Show orders from 2024
✓ List invoices created in April 2024
✓ What orders were placed in Q2 2024?
✓ Find recent inventory movements
✓ Show orders after 2024-04-01
```

**Expected Results:**
- Should filter by date correctly
- SQL should include date comparisons
- Answer should indicate time period

---

### 6. Join Queries
Test table relationships and JOINs.

```
✓ Show customer names with their orders
✓ List orders with customer information
✓ Find invoices with order details
✓ Get customers and their total order amounts
✓ Show order details with customer names
```

**Expected Results:**
- Should join multiple tables
- SQL should include JOIN clauses
- Answer should combine data from multiple tables

---

### 7. Complex Analytical Queries
Test multi-step analysis and business logic.

```
✓ What is the total revenue from completed orders?
✓ Calculate average order value per customer
✓ Show total outstanding invoice amounts
✓ What is the revenue by customer?
✓ Find customers with the most orders
✓ Calculate total inventory value
```

**Expected Results:**
- Should perform complex calculations
- May require multiple SQL queries
- Answer should provide business insights

---

### 8. Grouping and Aggregation
Test GROUP BY functionality.

```
✓ Show order count by customer
✓ Group orders by status
✓ Count invoices by payment status
✓ Total amount by customer
✓ Average order amount by status
```

**Expected Results:**
- Should group results
- SQL should use GROUP BY
- Answer should show breakdown by groups

---

### 9. Edge Cases and Error Handling
Test system robustness.

```
✓ What is the answer to life, the universe, and everything?
✓ Show me data from a table that doesn't exist
✓ Calculate something impossible
✓ Query with invalid syntax request
✓ Get information about nothing
```

**Expected Results:**
- Should handle errors gracefully
- Should show appropriate error messages
- Should not crash the system
- Confidence should be low for invalid queries

---

### 10. Schema Exploration
Test understanding of database structure.

```
✓ What tables are available?
✓ Show me the database schema
✓ What columns does the customers table have?
✓ List all tables in the database
✓ What is the structure of the orders table?
```

**Expected Results:**
- Should return schema information
- May use schema endpoint instead of SQL
- Answer should list tables/columns

---

### 11. Comparative Queries
Test comparisons and rankings.

```
✓ Which customer has the most orders?
✓ Find the largest order amount
✓ Show top 5 customers by order count
✓ Compare order totals by status
✓ Which invoices are unpaid?
```

**Expected Results:**
- Should identify maximums/minimums
- SQL may use ORDER BY and LIMIT
- Answer should highlight comparisons

---

### 12. Conditional Logic Queries
Test CASE statements and conditional logic.

```
✓ Categorize orders by amount (high/medium/low)
✓ Show order status breakdown
✓ Classify customers by order count
✓ Group invoices by payment status
```

**Expected Results:**
- Should apply business logic
- SQL may use CASE statements
- Answer should show categories

---

### 13. Null and Missing Data Handling
Test handling of NULL values.

```
✓ Find customers without orders
✓ Show invoices without associated orders
✓ List orders with missing customer information
✓ Find records with null values
```

**Expected Results:**
- Should handle NULL values correctly
- SQL should use IS NULL or LEFT JOIN
- Answer should indicate missing data

---

### 14. Model Selection Tests
Test different LLM models (if available).

```
✓ [Test with Ollama models]
  - Select "Llama 3 (8B)" and run a query
  - Select "Mistral 7B" and run a query
  - Verify answers differ or are consistent

✓ [Test with OpenRouter models if configured]
  - Select different cloud models
  - Compare response quality
```

**Expected Results:**
- Model selector should work
- Queries should execute with selected model
- Answers may vary by model quality

---

### 15. Performance and Large Result Sets
Test handling of large datasets.

```
✓ Count all records across all tables
✓ Show all data from largest table
✓ Calculate totals for all customers
✓ Aggregate data across multiple tables
```

**Expected Results:**
- Should handle large result sets
- May limit results appropriately
- Should complete in reasonable time

---

### 16. Natural Language Variations
Test understanding of different phrasings.

```
✓ How many customers do we have?
✓ What's the customer count?
✓ Tell me the number of customers
✓ Customer total please
✓ I need to know how many customers exist
```

**Expected Results:**
- Should understand variations
- Should return same/similar results
- SQL should be equivalent

---

### 17. Multi-Part Questions
Test complex questions with multiple parts.

```
✓ Show me customers and their total order amounts
✓ List orders with customer names and invoice status
✓ Get customer information with order counts and totals
✓ Show complete order details with customer and invoice info
```

**Expected Results:**
- May require multiple queries
- Should combine information
- Answer should address all parts

---

### 18. Business Intelligence Queries
Test analytical and reporting queries.

```
✓ What is our total revenue?
✓ Show sales performance by customer
✓ Calculate average order value
✓ What is the order completion rate?
✓ Show revenue trends
```

**Expected Results:**
- Should provide business insights
- May require calculations
- Answer should be actionable

---

## Test Checklist

For each test prompt, verify:

- [ ] **Query Execution**: Query executes without errors
- [ ] **SQL Generation**: Valid SQL is generated
- [ ] **Results Display**: Results are shown correctly
- [ ] **Answer Quality**: Answer is informative and relevant
- [ ] **Confidence Score**: Confidence is reasonable (not 1% or 100%)
- [ ] **Risk Assessment**: Risk level matches confidence
- [ ] **Execution Trace**: SQL and results are visible
- [ ] **Error Handling**: Errors are handled gracefully
- [ ] **Loading States**: Loading indicators appear during execution
- [ ] **Response Time**: Queries complete in reasonable time (< 10s for simple, < 30s for complex)

## Performance Benchmarks

- **Simple COUNT queries**: < 2 seconds
- **Basic SELECT queries**: < 3 seconds
- **JOIN queries**: < 5 seconds
- **Complex aggregations**: < 10 seconds
- **Multi-query operations**: < 15 seconds

## Success Criteria

✅ **System is complete if:**
1. All basic queries (categories 1-3) work correctly
2. Filtered and joined queries (categories 4-6) execute successfully
3. Error handling (category 9) doesn't crash the system
4. Schema exploration (category 10) works
5. Model selection (category 14) functions properly
6. Confidence and risk calculations are accurate
7. Answers are informative and not generic
8. SQL generation is correct for 80%+ of queries
9. Execution trace shows proper information
10. Frontend and backend integration is seamless

## Regression Test Set (Quick Check)

Run these 10 queries to quickly verify system health:

1. `How many customers are there?`
2. `What is the total amount of all orders?`
3. `Show me all completed orders`
4. `List customers with their order counts`
5. `What is the average order amount?`
6. `Find unpaid invoices`
7. `Show orders from 2024`
8. `Which customer has the most orders?`
9. `Calculate total revenue`
10. `give info`

If all 10 pass, the core system is functional.
