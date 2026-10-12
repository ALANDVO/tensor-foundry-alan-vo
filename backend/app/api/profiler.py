"""DataLoader worker memory profiler API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_role
from app.schemas.domain import (
    ProfilerRunResponse,
    ProfilerSimulateRequest,
    UserProfile
)
from app.services.audit_service import AuditService
from app.services.profiler_service import ProfilerService

router = APIRouter(prefix="/profiler", tags=["DataLoader Memory Profiler"])


@router.post("/simulate", response_model=ProfilerRunResponse)
def simulate_worker_memory(
    req: ProfilerSimulateRequest,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_role("operator"))
) -> ProfilerRunResponse:
    """Simulate and profile DataLoader process worker memory amplification (PyTorch #13246)."""
    svc = ProfilerService(db)
    run = svc.run_simulation(req, user_email=current_user.email)

    audit_svc = AuditService(db)
    audit_svc.log_action(
        user_email=current_user.email,
        user_role=current_user.roles[0],
        action="RUN_MEMORY_PROFILER",
        resource_type="profiler_run",
        resource_id=run.id,
        details={
            "workers": req.worker_count,
            "mode": req.ipc_mode,
            "amplification_ratio": run.amplification_ratio
        }
    )

    return ProfilerRunResponse.model_validate(run)


@router.get("/runs", response_model=List[ProfilerRunResponse])
def list_profiler_runs(
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_role("viewer"))
) -> List[ProfilerRunResponse]:
    """List historical DataLoader memory profiling benchmarks."""
    svc = ProfilerService(db)
    runs = svc.list_runs()
    return [ProfilerRunResponse.model_validate(r) for r in runs]


@router.get("/runs/{run_id}", response_model=ProfilerRunResponse)
def get_profiler_run(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_role("viewer"))
) -> ProfilerRunResponse:
    """Retrieve details and diagnostic log for a single profiler benchmark."""
    svc = ProfilerService(db)
    run = svc.get_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profiler run with ID '{run_id}' not found"
        )
    return ProfilerRunResponse.model_validate(run)
