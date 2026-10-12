"""Compiler and Graph Optimization API endpoints."""

import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.entities import GraphModel
from app.schemas.domain import (
    GraphCreateRequest,
    GraphResponse,
    PageResponse,
    UserProfile
)
from app.services.audit_service import AuditService
from app.services.compiler_engine import CompilerEngine, build_preset_graph

router = APIRouter(prefix="/compiler", tags=["Graph Compiler"])


def _to_graph_response(r: GraphModel) -> GraphResponse:
    return GraphResponse(
        id=r.id,
        name=r.name,
        description=r.description,
        framework=r.framework,
        target_backend=r.target_backend,
        input_shapes=r.input_shapes,
        nodes=r.get_nodes(),
        edges=r.get_edges(),
        compiled_kernels=r.get_compiled_kernels(),
        metrics=r.get_metrics(),
        created_by=r.created_by,
        created_at=r.created_at,
        updated_at=r.updated_at
    )


@router.get("/graphs", response_model=PageResponse[GraphResponse])
def list_graphs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    target_backend: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_role("viewer"))
) -> PageResponse[GraphResponse]:
    """List stored computational graphs and compiled kernels."""
    query = db.query(GraphModel)
    if target_backend:
        query = query.filter(GraphModel.target_backend == target_backend.lower())

    total = query.count()
    offset = (page - 1) * page_size
    records = query.order_by(GraphModel.created_at.desc()).offset(offset).limit(page_size).all()
    items = [_to_graph_response(r) for r in records]
    pages = (total + page_size - 1) // page_size if total > 0 else 1
    return PageResponse(items=items, total=total, page=page, page_size=page_size, pages=pages)


@router.post("/trace", response_model=GraphResponse)
def trace_and_compile(
    req: GraphCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_role("operator"))
) -> GraphResponse:
    """Trace, optimize, and compile computational graph into target backend kernels."""
    preset = req.architecture_preset or "mlp"
    if req.custom_nodes and len(req.custom_nodes) > 0:
        nodes = [n.model_dump() for n in req.custom_nodes]
        edges = []
        for n in nodes:
            for inp in n.get("inputs", []):
                edges.append({"source": inp, "target": n["id"], "shape": n["output_shape"]})
        input_shapes = {n["id"]: n["output_shape"] for n in nodes if n["op_type"] == "input"}
    else:
        nodes, edges, input_shapes = build_preset_graph(preset)

    engine = CompilerEngine(target_backend=req.target_backend)
    compiled_kernels, metrics = engine.optimize_and_compile(nodes, edges)

    graph_id = f"graph_{uuid.uuid4().hex[:10]}"
    graph_obj = GraphModel(
        id=graph_id,
        name=req.name,
        description=req.description or f"Graph generated via {preset.upper()} architecture preset",
        framework="tensor-foundry-py",
        target_backend=req.target_backend.lower(),
        input_shapes=json.dumps(input_shapes),
        nodes_json=json.dumps(nodes),
        edges_json=json.dumps(edges),
        compiled_kernels_json=json.dumps([k.model_dump() for k in compiled_kernels]),
        metrics_json=json.dumps(metrics.model_dump()),
        created_by=current_user.email
    )

    db.add(graph_obj)
    db.commit()
    db.refresh(graph_obj)

    audit_svc = AuditService(db)
    audit_svc.log_action(
        user_email=current_user.email,
        user_role=current_user.roles[0],
        action="TRACE_AND_COMPILE",
        resource_type="computational_graph",
        resource_id=graph_id,
        details={
            "name": req.name,
            "target_backend": req.target_backend,
            "fused_kernels": len(compiled_kernels),
            "speedup_pct": metrics.speedup_percentage
        }
    )

    return _to_graph_response(graph_obj)


@router.get("/graphs/{graph_id}", response_model=GraphResponse)
def get_graph(
    graph_id: str,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_role("viewer"))
) -> GraphResponse:
    """Retrieve full details, IR nodes, and compiled kernel sources for a graph."""
    record = db.query(GraphModel).filter(GraphModel.id == graph_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Graph with ID '{graph_id}' not found"
        )
    return _to_graph_response(record)


@router.delete("/graphs/{graph_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_graph(
    graph_id: str,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(require_role("admin"))
):
    """Delete a computational graph record (Admin only)."""
    record = db.query(GraphModel).filter(GraphModel.id == graph_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Graph with ID '{graph_id}' not found"
        )

    db.delete(record)
    db.commit()

    audit_svc = AuditService(db)
    audit_svc.log_action(
        user_email=current_user.email,
        user_role=current_user.roles[0],
        action="DELETE_GRAPH",
        resource_type="computational_graph",
        resource_id=graph_id,
        details={"deleted_graph_id": graph_id}
    )
