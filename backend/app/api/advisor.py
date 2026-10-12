"""Opt-in advisory optimization LLM endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_role
from app.models.entities import GraphModel
from app.schemas.domain import AdvisorRequest, AdvisorResponse, UserProfile
from app.services.llm_advisor import LLMAdvisorService

router = APIRouter(prefix="/advisor", tags=["Advisory LLM Diagnostics"])


@router.post("/recommend", response_model=AdvisorResponse)
async def get_advisory_recommendations(
    req: AdvisorRequest,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_role("operator"))
) -> AdvisorResponse:
    """Generate grounded compiler optimization and memory advice."""
    grounded_data = {}

    if req.graph_id:
        graph = db.query(GraphModel).filter(GraphModel.id == req.graph_id).first()
        if graph:
            grounded_data = graph.get_metrics()
            grounded_data["graph_name"] = graph.name
            grounded_data["target_backend"] = graph.target_backend

    svc = LLMAdvisorService()
    return await svc.generate_advice(req, grounded_data=grounded_data)
