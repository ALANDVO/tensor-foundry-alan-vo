"""Hardware operator coverage and lowerability matrix API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_role
from app.models.entities import GraphModel
from app.schemas.domain import (
    LowerabilityAnalysisRequest,
    LowerabilityAnalysisResponse,
    OpCatalogItemSchema,
    TriageRankingItem,
    UserProfile
)
from app.services.coverage_service import CoverageService

router = APIRouter(prefix="/coverage", tags=["Hardware Op Coverage"])


@router.get("/matrix", response_model=List[OpCatalogItemSchema])
def get_coverage_matrix(
    category: Optional[str] = None,
    search: Optional[str] = None,
    target_status: Optional[str] = None,
    target_backend: str = "mps",
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_role("viewer"))
) -> List[OpCatalogItemSchema]:
    """Retrieve multi-hardware operator support matrix with filtering."""
    svc = CoverageService(db)
    items = svc.list_operators(
        category=category,
        search=search,
        target_status=target_status,
        target_backend=target_backend
    )
    return [OpCatalogItemSchema.model_validate(it) for it in items]


@router.post("/analyze-graph", response_model=LowerabilityAnalysisResponse)
def analyze_graph_lowerability(
    req: LowerabilityAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_role("operator"))
) -> LowerabilityAnalysisResponse:
    """Analyze hardware lowerability and identify CPU fallback transfers for a graph."""
    svc = CoverageService(db)

    # Determine operator list
    op_list: List[str] = []
    if req.graph_id:
        graph = db.query(GraphModel).filter(GraphModel.id == req.graph_id).first()
        if graph:
            nodes = graph.get_nodes()
            op_list = [n.get("op_type", "unknown") for n in nodes if n.get("op_type") not in ("input", "weight")]
    elif req.operator_list:
        op_list = req.operator_list
    else:
        # Default representative set
        op_list = ["matmul", "add", "relu", "grid_sampler_3d", "standard_gamma"]

    return svc.analyze_graph_lowerability(
        operator_list=op_list,
        target_backend=req.target_backend
    )


@router.get("/triage", response_model=List[TriageRankingItem])
def get_triage_rankings(
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_role("viewer"))
) -> List[TriageRankingItem]:
    """Retrieve community-requested operator triage backlog ranked by priority score."""
    svc = CoverageService(db)
    return svc.get_triage_rankings()
