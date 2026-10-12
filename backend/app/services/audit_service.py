"""Audit logging service for security and mutation operations."""

from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy.orm import Session
from app.models.entities import AuditLog


class AuditService:
    """Manages transactional audit logs with UTC timestamps."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def log_action(
        self,
        user_email: str,
        user_role: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None,
        status: str = "SUCCESS",
        ip_address: str = "127.0.0.1"
    ) -> AuditLog:
        """Write an audit entry with UTC timestamp to persistent storage."""
        entry = AuditLog(
            id=f"audit_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now(timezone.utc),
            user_email=user_email,
            user_role=user_role,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            details_json=json.dumps(details or {}),
            ip_address=ip_address
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def query_logs(
        self,
        limit: int = 50,
        action: Optional[str] = None,
        user_email: Optional[str] = None
    ) -> List[AuditLog]:
        """Query audit log entries ordered by newest first."""
        query = self.db.query(AuditLog)
        if action:
            query = query.filter(AuditLog.action == action)
        if user_email:
            query = query.filter(AuditLog.user_email == user_email)
        return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
