"""System audit log API endpoint."""

import json
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_role
from app.schemas.domain import AuditLogResponse, UserProfile
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["Audit Log"])


@router.get("/logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    limit: int = Query(default=50, ge=1, le=100),
    action: Optional[str] = None,
    user_email: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_role("admin"))
) -> List[AuditLogResponse]:
    """Retrieve audit log records (Admin only)."""
    svc = AuditService(db)
    logs = svc.query_logs(limit=limit, action=action, user_email=user_email)

    items = []
    for log in logs:
        items.append(
            AuditLogResponse(
                id=log.id,
                timestamp=log.timestamp,
                user_email=log.user_email,
                user_role=log.user_role,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                status=log.status,
                details=log.get_details(),
                ip_address=log.ip_address
            )
        )
    return items
