# =============================================================================
# Clinical Guideline Research Assistant
# Copyright (c) 2024. MIT License. See LICENSE file for details.
# =============================================================================
"""SQLite-based audit logging for API requests.

Tracks all requests for compliance and debugging.
No external dependencies - uses built-in SQLite.
"""
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import contextmanager

from config.settings_lite import settings


class AuditLogger:
    """SQLite-based audit logger for API requests."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize audit logger.
        
        Args:
            db_path: Path to SQLite database. Defaults to settings path.
        """
        if db_path is None:
            settings.ensure_directories()
            db_path = settings.data_dir / "audit.db"
        
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Create audit log table if it doesn't exist."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    request_id TEXT,
                    endpoint TEXT NOT NULL,
                    method TEXT NOT NULL,
                    topic TEXT,
                    status_code INTEGER,
                    response_time_ms REAL,
                    error TEXT,
                    metadata TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp 
                ON audit_logs(timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_request_id 
                ON audit_logs(request_id)
            """)
    
    @contextmanager
    def _get_connection(self):
        """Get database connection context manager."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    def log_request(
        self,
        endpoint: str,
        method: str,
        request_id: Optional[str] = None,
        topic: Optional[str] = None,
        status_code: Optional[int] = None,
        response_time_ms: Optional[float] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log an API request.
        
        Args:
            endpoint: API endpoint path
            method: HTTP method (GET, POST, etc.)
            request_id: Optional request ID
            topic: Research topic if applicable
            status_code: HTTP response status code
            response_time_ms: Response time in milliseconds
            error: Error message if any
            metadata: Additional metadata as dict
            
        Returns:
            Audit log entry ID
        """
        log_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        import json
        metadata_str = json.dumps(metadata) if metadata else None
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO audit_logs 
                (id, timestamp, request_id, endpoint, method, topic, 
                 status_code, response_time_ms, error, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log_id, timestamp, request_id, endpoint, method,
                topic, status_code, response_time_ms, error, metadata_str
            ))
        
        return log_id
    
    def get_recent_logs(self, limit: int = 100) -> list:
        """Get recent audit log entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of audit log entries as dicts
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM audit_logs 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_logs_by_request_id(self, request_id: str) -> list:
        """Get all logs for a specific request ID.
        
        Args:
            request_id: Request ID to search for
            
        Returns:
            List of matching audit log entries
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM audit_logs 
                WHERE request_id = ?
                ORDER BY timestamp
            """, (request_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get audit log statistics.
        
        Returns:
            Dict with log statistics
        """
        with self._get_connection() as conn:
            # Total count
            total = conn.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0]
            
            # Error count
            errors = conn.execute(
                "SELECT COUNT(*) FROM audit_logs WHERE error IS NOT NULL"
            ).fetchone()[0]
            
            # Average response time
            avg_time = conn.execute(
                "SELECT AVG(response_time_ms) FROM audit_logs WHERE response_time_ms IS NOT NULL"
            ).fetchone()[0]
            
            # Requests by endpoint
            endpoints = conn.execute("""
                SELECT endpoint, COUNT(*) as count 
                FROM audit_logs 
                GROUP BY endpoint 
                ORDER BY count DESC
            """).fetchall()
            
            return {
                "total_requests": total,
                "error_count": errors,
                "error_rate": errors / total if total > 0 else 0,
                "avg_response_time_ms": avg_time or 0,
                "requests_by_endpoint": {row[0]: row[1] for row in endpoints}
            }


# Singleton instance
_audit_logger = None

def get_audit_logger() -> AuditLogger:
    """Get or create singleton audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def log_request(**kwargs) -> str:
    """Convenience function to log a request."""
    return get_audit_logger().log_request(**kwargs)


if __name__ == "__main__":
    # Quick test
    print("Testing audit logger...")
    
    logger = AuditLogger()
    
    # Log some test requests
    log_id = logger.log_request(
        endpoint="/api/v1/research",
        method="POST",
        topic="diabetes elderly",
        status_code=200,
        response_time_ms=1234.5
    )
    print(f"Logged request: {log_id}")
    
    logger.log_request(
        endpoint="/api/v1/research/123",
        method="GET",
        request_id="123",
        status_code=200,
        response_time_ms=50.2
    )
    
    # Get stats
    stats = logger.get_stats()
    print(f"\nStats: {stats}")
    
    # Get recent logs
    logs = logger.get_recent_logs(5)
    print(f"\nRecent logs: {len(logs)} entries")
