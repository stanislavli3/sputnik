"""Database utilities for API data persistence."""

import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

import duckdb


class QueryHistoryDB:
    """Database for storing query history."""
    
    def __init__(self, db_path: str = "sputnik_history.duckdb"):
        """Initialize query history database."""
        self.db_path = db_path
        self._ensure_schema()
    
    def _get_connection(self):
        """Get database connection (optimized for reuse)."""
        # DuckDB connections are lightweight, but we can optimize by reusing
        # For now, create new connections (DuckDB handles this efficiently)
        # In production with PostgreSQL, use connection pooling
        return duckdb.connect(self.db_path, read_only=False)
    
    def _ensure_schema(self):
        """Ensure query_history table exists."""
        conn = self._get_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS query_history (
                    id VARCHAR PRIMARY KEY,
                    user_id VARCHAR,
                    question TEXT NOT NULL,
                    sql_queries TEXT[] NOT NULL,
                    answer TEXT,
                    confidence FLOAT,
                    execution_results JSON,
                    execution_time_ms INTEGER,
                    model_id VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for common queries
            try:
                conn.execute("CREATE INDEX IF NOT EXISTS idx_query_history_user ON query_history(user_id)")
            except:
                pass  # Index might already exist
            
            try:
                conn.execute("CREATE INDEX IF NOT EXISTS idx_query_history_created ON query_history(created_at DESC)")
            except:
                pass
            
            # Additional performance indexes
            try:
                conn.execute("CREATE INDEX IF NOT EXISTS idx_query_history_model ON query_history(model_id)")
            except:
                pass
            
            try:
                conn.execute("CREATE INDEX IF NOT EXISTS idx_query_history_confidence ON query_history(confidence)")
            except:
                pass
            
            conn.commit()
        finally:
            conn.close()
    
    def save_query(
        self,
        question: str,
        sql_queries: List[str],
        answer: str,
        confidence: float,
        execution_results: Optional[List[Dict[str, Any]]] = None,
        execution_time_ms: Optional[int] = None,
        model_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """Save a query to history."""
        import uuid
        query_id = str(uuid.uuid4())
        
        conn = self._get_connection()
        try:
            # Convert execution_results to JSON string
            # DuckDB can handle JSON directly, but we'll store as text for compatibility
            execution_results_json = None
            if execution_results:
                import json
                try:
                    execution_results_json = json.dumps(execution_results)
                except (TypeError, ValueError) as e:
                    print(f"Failed to serialize execution_results: {e}")
                    execution_results_json = None
            
            conn.execute("""
                INSERT INTO query_history 
                (id, user_id, question, sql_queries, answer, confidence, 
                 execution_results, execution_time_ms, model_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                query_id,
                user_id,
                question,
                sql_queries,
                answer,
                confidence,
                execution_results_json,
                execution_time_ms,
                model_id,
                datetime.utcnow(),
            ))
            conn.commit()
            return query_id
        finally:
            conn.close()
    
    def get_query_history(
        self,
        user_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get query history with pagination."""
        conn = self._get_connection()
        try:
            # Build WHERE clause
            conditions = []
            params = []
            
            if user_id:
                conditions.append("user_id = ?")
                params.append(user_id)
            
            if search:
                conditions.append("question ILIKE ?")
                params.append(f"%{search}%")
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM query_history {where_clause}"
            total = conn.execute(count_query, params).fetchone()[0]
            
            # Get paginated results
            offset = (page - 1) * page_size
            query = f"""
                SELECT id, user_id, question, sql_queries, answer, confidence,
                       execution_results, execution_time_ms, model_id, created_at
                FROM query_history
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            params.extend([page_size, offset])
            
            rows = conn.execute(query, params).fetchall()
            
            # Convert rows to dicts
            queries = []
            for row in rows:
                # Parse JSON execution_results if it's a string
                execution_results = row[6]
                if execution_results and isinstance(execution_results, str):
                    import json
                    try:
                        execution_results = json.loads(execution_results)
                    except (json.JSONDecodeError, TypeError):
                        execution_results = None
                
                queries.append({
                    "id": row[0],
                    "user_id": row[1],
                    "question": row[2],
                    "sql_queries": list(row[3]) if row[3] else [],
                    "answer": row[4],
                    "confidence": float(row[5]) if row[5] is not None else 0.0,
                    "execution_results": execution_results,
                    "execution_time_ms": row[7],
                    "model_id": row[8],
                    "created_at": row[9].isoformat() if row[9] else None,
                })
            
            return {
                "queries": queries,
                "total": total,
                "page": page,
                "page_size": page_size,
            }
        finally:
            conn.close()
    
    def get_query(self, query_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific query by ID."""
        conn = self._get_connection()
        try:
            row = conn.execute("""
                SELECT id, user_id, question, sql_queries, answer, confidence,
                       execution_results, execution_time_ms, model_id, created_at
                FROM query_history
                WHERE id = ?
            """, (query_id,)).fetchone()
            
            if not row:
                return None
            
            # Parse JSON execution_results if it's a string
            execution_results = row[6]
            if execution_results and isinstance(execution_results, str):
                import json
                try:
                    execution_results = json.loads(execution_results)
                except (json.JSONDecodeError, TypeError):
                    execution_results = None
            
            return {
                "id": row[0],
                "user_id": row[1],
                "question": row[2],
                "sql_queries": list(row[3]) if row[3] else [],
                "answer": row[4],
                "confidence": float(row[5]) if row[5] is not None else 0.0,
                "execution_results": execution_results,
                "execution_time_ms": row[7],
                "model_id": row[8],
                "created_at": row[9].isoformat() if row[9] else None,
            }
        finally:
            conn.close()


class ReviewsDB:
    """Database for storing expert reviews."""
    
    def __init__(self, db_path: str = "sputnik_history.duckdb"):
        """Initialize reviews database (uses same DB as history)."""
        self.db_path = db_path
        self._ensure_schema()
    
    def _get_connection(self):
        """Get database connection (optimized for reuse)."""
        # DuckDB connections are lightweight, but we can optimize by reusing
        # For now, create new connections (DuckDB handles this efficiently)
        # In production with PostgreSQL, use connection pooling
        return duckdb.connect(self.db_path, read_only=False)
    
    def _ensure_schema(self):
        """Ensure reviews table exists."""
        conn = self._get_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reviews (
                    id VARCHAR PRIMARY KEY,
                    query_id VARCHAR NOT NULL,
                    expert_id VARCHAR,
                    status VARCHAR NOT NULL DEFAULT 'pending',
                    correction_reason VARCHAR,
                    expert_notes TEXT,
                    corrected_answer TEXT,
                    priority VARCHAR DEFAULT 'medium',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reviewed_at TIMESTAMP,
                    submitted_by VARCHAR
                )
            """)
            
            # Create indexes
            try:
                conn.execute("CREATE INDEX IF NOT EXISTS idx_reviews_status ON reviews(status)")
            except:
                pass
            
            try:
                conn.execute("CREATE INDEX IF NOT EXISTS idx_reviews_priority ON reviews(priority)")
            except:
                pass
            
            try:
                conn.execute("CREATE INDEX IF NOT EXISTS idx_reviews_query ON reviews(query_id)")
            except:
                pass
            
            try:
                conn.execute("CREATE INDEX IF NOT EXISTS idx_reviews_expert ON reviews(expert_id)")
            except:
                pass
            
            try:
                conn.execute("CREATE INDEX IF NOT EXISTS idx_reviews_created ON reviews(created_at)")
            except:
                pass
            
            conn.commit()
        finally:
            conn.close()
    
    def create_review(
        self,
        query_id: str,
        priority: str = "medium",
        submitted_by: Optional[str] = None,
    ) -> str:
        """Create a new review entry."""
        import uuid
        review_id = f"R-{uuid.uuid4().hex[:4]}"
        
        conn = self._get_connection()
        try:
            conn.execute("""
                INSERT INTO reviews 
                (id, query_id, priority, status, submitted_by, created_at)
                VALUES (?, ?, ?, 'pending', ?, CURRENT_TIMESTAMP)
            """, (review_id, query_id, priority, submitted_by))
            conn.commit()
            return review_id
        finally:
            conn.close()
    
    def get_reviews(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        expert_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get reviews with optional filtering."""
        conn = self._get_connection()
        try:
            conditions = []
            params = []
            
            if status:
                conditions.append("status = ?")
                params.append(status)
            
            if priority:
                conditions.append("priority = ?")
                params.append(priority)
            
            if expert_id:
                conditions.append("expert_id = ?")
                params.append(expert_id)
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            query = f"""
                SELECT r.id, r.query_id, r.expert_id, r.status, r.correction_reason,
                       r.expert_notes, r.corrected_answer, r.priority, r.created_at,
                       r.reviewed_at, r.submitted_by,
                       qh.question, qh.answer, qh.confidence, qh.sql_queries, qh.execution_results
                FROM reviews r
                LEFT JOIN query_history qh ON r.query_id = qh.id
                {where_clause}
                ORDER BY 
                    CASE r.priority
                        WHEN 'high' THEN 1
                        WHEN 'medium' THEN 2
                        WHEN 'low' THEN 3
                    END,
                    r.created_at ASC
            """
            
            rows = conn.execute(query, params).fetchall()
            
            reviews = []
            for row in rows:
                # Calculate wait time
                created_at = row[8]  # created_at is at index 8
                wait_time = None
                if created_at:
                    from datetime import datetime, timezone
                    if isinstance(created_at, str):
                        created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    else:
                        created_dt = created_at
                    if isinstance(created_dt, datetime):
                        now = datetime.now(timezone.utc) if created_dt.tzinfo else datetime.utcnow()
                        if created_dt.tzinfo:
                            now = now.replace(tzinfo=timezone.utc)
                        delta = now - (created_dt.replace(tzinfo=timezone.utc) if created_dt.tzinfo else created_dt)
                        hours = int(delta.total_seconds() / 3600)
                        minutes = int((delta.total_seconds() % 3600) / 60)
                        if hours > 0:
                            wait_time = f"{hours}h {minutes}m"
                        else:
                            wait_time = f"{minutes}m"
                
                # Parse execution_results if it's a string
                execution_results = row[15]
                if execution_results and isinstance(execution_results, str):
                    import json
                    try:
                        execution_results = json.loads(execution_results)
                    except:
                        execution_results = None
                
                # Determine risk from confidence
                confidence_val = row[13]  # confidence is at index 13
                confidence = float(confidence_val) if confidence_val is not None else 0.0
                risk = "high" if confidence < 0.70 else ("medium" if confidence < 0.85 else "low")
                
                reviews.append({
                    "id": row[0],
                    "query_id": row[1],
                    "expert_id": row[2],
                    "status": row[3],
                    "correction_reason": row[4],
                    "expert_notes": row[5],
                    "corrected_answer": row[6],
                    "priority": row[7],
                    "created_at": row[8].isoformat() if row[8] else None,
                    "reviewed_at": row[10].isoformat() if row[10] else None,
                    "submitted_by": row[11] or "system",
                    "question": row[12] or "",
                    "answer": row[13] or "",
                    "confidence": confidence,
                    "risk": risk,
                    "wait_time": wait_time,
                    "sql_queries": list(row[14]) if row[14] else [],
                    "execution_results": execution_results,
                })
            
            return reviews
        finally:
            conn.close()
    
    def get_review(self, review_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific review by ID."""
        reviews = self.get_reviews()
        return next((r for r in reviews if r["id"] == review_id), None)
    
    def update_review(
        self,
        review_id: str,
        status: Optional[str] = None,
        expert_id: Optional[str] = None,
        correction_reason: Optional[str] = None,
        expert_notes: Optional[str] = None,
        corrected_answer: Optional[str] = None,
    ) -> bool:
        """Update a review."""
        conn = self._get_connection()
        try:
            updates = []
            params = []
            
            if status:
                updates.append("status = ?")
                params.append(status)
            
            if expert_id:
                updates.append("expert_id = ?")
                params.append(expert_id)
            
            if correction_reason:
                updates.append("correction_reason = ?")
                params.append(correction_reason)
            
            if expert_notes:
                updates.append("expert_notes = ?")
                params.append(expert_notes)
            
            if corrected_answer:
                updates.append("corrected_answer = ?")
                params.append(corrected_answer)
            
            if status in ["approved", "rejected", "abstained"]:
                updates.append("reviewed_at = CURRENT_TIMESTAMP")
            
            if not updates:
                return False
            
            params.append(review_id)
            query = f"UPDATE reviews SET {', '.join(updates)} WHERE id = ?"
            
            conn.execute(query, params)
            conn.commit()
            return True
        finally:
            conn.close()


class QueryTemplatesDB:
    """Database for storing query templates."""
    
    def __init__(self, db_path: str = "sputnik_history.duckdb"):
        """Initialize templates database (uses same DB as history)."""
        self.db_path = db_path
        self._ensure_schema()
    
    def _get_connection(self):
        """Get database connection (optimized for reuse)."""
        # DuckDB connections are lightweight, but we can optimize by reusing
        # For now, create new connections (DuckDB handles this efficiently)
        # In production with PostgreSQL, use connection pooling
        return duckdb.connect(self.db_path, read_only=False)
    
    def _ensure_schema(self):
        """Ensure query_templates table exists."""
        conn = self._get_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS query_templates (
                    id VARCHAR PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    category VARCHAR,
                    question TEXT NOT NULL,
                    sql_template TEXT,
                    variables JSON,
                    created_by VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            try:
                conn.execute("CREATE INDEX IF NOT EXISTS idx_templates_category ON query_templates(category)")
            except:
                pass
            
            try:
                conn.execute("CREATE INDEX IF NOT EXISTS idx_templates_created_by ON query_templates(created_by)")
            except:
                pass
            
            conn.commit()
        finally:
            conn.close()
    
    def create_template(
        self,
        name: str,
        question: str,
        sql_template: Optional[str] = None,
        category: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None,
    ) -> str:
        """Create a new query template."""
        import uuid
        template_id = str(uuid.uuid4())
        
        conn = self._get_connection()
        try:
            variables_json = None
            if variables:
                import json
                variables_json = json.dumps(variables)
            
            conn.execute("""
                INSERT INTO query_templates 
                (id, name, category, question, sql_template, variables, created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (template_id, name, category, question, sql_template, variables_json, created_by))
            conn.commit()
            return template_id
        finally:
            conn.close()
    
    def get_templates(
        self,
        category: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get templates with optional filtering."""
        conn = self._get_connection()
        try:
            conditions = []
            params = []
            
            if category:
                conditions.append("category = ?")
                params.append(category)
            
            if created_by:
                conditions.append("created_by = ?")
                params.append(created_by)
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            query = f"""
                SELECT id, name, category, question, sql_template, variables,
                       created_by, created_at, updated_at
                FROM query_templates
                {where_clause}
                ORDER BY updated_at DESC
            """
            
            rows = conn.execute(query, params).fetchall()
            
            templates = []
            for row in rows:
                # Parse variables JSON if it's a string
                variables = row[5]
                if variables and isinstance(variables, str):
                    import json
                    try:
                        variables = json.loads(variables)
                    except:
                        variables = None
                
                templates.append({
                    "id": row[0],
                    "name": row[1],
                    "category": row[2],
                    "question": row[3],
                    "sql_template": row[4],
                    "variables": variables,
                    "created_by": row[6],
                    "created_at": row[7].isoformat() if row[7] else None,
                    "updated_at": row[8].isoformat() if row[8] else None,
                })
            
            return templates
        finally:
            conn.close()
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific template by ID."""
        templates = self.get_templates()
        return next((t for t in templates if t["id"] == template_id), None)
    
    def update_template(
        self,
        template_id: str,
        name: Optional[str] = None,
        question: Optional[str] = None,
        sql_template: Optional[str] = None,
        category: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update a template."""
        conn = self._get_connection()
        try:
            updates = []
            params = []
            
            if name:
                updates.append("name = ?")
                params.append(name)
            
            if question:
                updates.append("question = ?")
                params.append(question)
            
            if sql_template:
                updates.append("sql_template = ?")
                params.append(sql_template)
            
            if category:
                updates.append("category = ?")
                params.append(category)
            
            if variables is not None:
                import json
                variables_json = json.dumps(variables)
                updates.append("variables = ?")
                params.append(variables_json)
            
            if not updates:
                return False
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(template_id)
            
            query = f"UPDATE query_templates SET {', '.join(updates)} WHERE id = ?"
            
            conn.execute(query, params)
            conn.commit()
            return True
        finally:
            conn.close()
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a template."""
        conn = self._get_connection()
        try:
            conn.execute("DELETE FROM query_templates WHERE id = ?", (template_id,))
            conn.commit()
            return True
        finally:
            conn.close()


# Global instance (in production, use dependency injection)
_history_db: Optional[QueryHistoryDB] = None
_reviews_db: Optional[ReviewsDB] = None
_templates_db: Optional[QueryTemplatesDB] = None


def get_history_db() -> QueryHistoryDB:
    """Get or create the query history database."""
    global _history_db
    if _history_db is None:
        _history_db = QueryHistoryDB()
    return _history_db


def get_reviews_db() -> ReviewsDB:
    """Get or create the reviews database."""
    global _reviews_db
    if _reviews_db is None:
        _reviews_db = ReviewsDB()
    return _reviews_db


def get_templates_db() -> QueryTemplatesDB:
    """Get or create the templates database."""
    global _templates_db
    if _templates_db is None:
        _templates_db = QueryTemplatesDB()
    return _templates_db
