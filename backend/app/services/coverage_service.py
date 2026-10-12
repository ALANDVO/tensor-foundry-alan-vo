"""Hardware operator coverage matrix and graph lowerability analyzer."""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.entities import OpCatalogItem
from app.schemas.domain import (
    LowerabilityAnalysisResponse,
    OpCatalogItemSchema,
    TriageRankingItem
)

# Reference data extracted from PyTorch issues #77764, #141287, #160230, #47702
_PR = "https://github.com/pytorch/pytorch/pull/"
OP_DEFS = [
    ("max_pool3d_with_indices", "vision_3d", "aten::max_pool3d_with_indices", "supported", "supported", "supported", "planned", "supported", "2.9", "1.3", 16, "stable", "141287", f"{_PR}156467", "PyTorch 2.9 MPS op"),
    ("linalg_solve_ex", "linalg", "aten::_linalg_solve_ex.result", "supported", "supported", "supported", "unsupported", "supported", "2.7", "1.3", 15, "stable", "141287", f"{_PR}146531", "Metal LU decomposition"),
    ("standard_gamma", "distribution", "aten::_standard_gamma", "supported", "supported", "in_progress", "planned", "supported", "nightly", "1.3", 13, "in_progress", "141287", f"{_PR}179228", "Marsaglia and Tsang method"),
    ("upsample_bicubic2d_aa", "vision_resample", "aten::_upsample_bicubic2d_aa.out", "supported", "supported", "supported", "partial", "supported", "2.8", "1.2", 10, "stable", "141287", f"{_PR}149378", "Anti-aliased resample"),
    ("linalg_qr", "linalg", "aten::linalg_qr.out", "supported", "supported", "in_progress", "unsupported", "supported", "nightly", "1.3", 10, "in_progress", "141287", f"{_PR}172536", "Householder reflectors"),
    ("angle", "complex_math", "aten::angle", "supported", "supported", "supported", "supported", "supported", "2.7", "1.2", 8, "stable", "141287", f"{_PR}143449", "Phase angle atan2"),
    ("grid_sampler_3d", "vision_3d", "aten::grid_sampler_3d", "supported", "supported", "supported", "planned", "supported", "2.9", "1.3", 7, "stable", "141287", f"{_PR}160541", "3D NeRF spatial sampler"),
    ("vdot", "tensor_math", "aten::vdot", "supported", "supported", "supported", "supported", "supported", "2.11", "1.2", 6, "stable", "141287", f"{_PR}172840", "Dot product 1D vectors"),
    ("unique_dim", "indexing", "aten::unique_dim", "supported", "supported", "supported", "unsupported", "supported", "2.10", "1.3", 4, "stable", "141287", f"{_PR}163694", "Eliminate duplicate slices"),
    ("kthvalue", "sorting", "aten::kthvalue.values", "supported", "supported", "supported", "planned", "supported", "2.9", "1.3", 3, "stable", "141287", f"{_PR}161817", "Bitonic quickselect"),
    ("matmul", "contraction", "aten::matmul", "supported", "supported", "supported", "supported", "supported", "2.0", "1.0", 120, "stable", "77764", "core", "Standard GEMM"),
    ("relu", "activation", "aten::relu", "supported", "supported", "supported", "supported", "supported", "2.0", "1.0", 80, "stable", "77764", "core", "Pointwise ReLU"),
    ("gelu", "activation", "aten::gelu", "supported", "supported", "supported", "supported", "supported", "2.1", "1.2", 95, "stable", "77764", "core", "GELU tanh polynomial")
]

_FIELDS = (
    "op_name", "category", "pytorch_symbol", "cpu_status", "cuda_status", "mps_status",
    "vulkan_status", "rocm_status", "min_mps_version", "min_vulkan_version", "request_count",
    "triage_status", "github_issue_ref", "pr_reference", "notes"
)
SEED_OPERATORS: List[Dict[str, Any]] = [dict(zip(_FIELDS, o)) for o in OP_DEFS]


class CoverageService:
    """Manages operator support status and evaluates graph lowerability."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def seed_initial_catalog(self) -> int:
        """Seed initial operator catalog if empty."""
        count = self.db.query(OpCatalogItem).count()
        if count > 0:
            return count

        for item in SEED_OPERATORS:
            self.db.add(OpCatalogItem(id=f"op_{uuid.uuid4().hex[:10]}", **item))

        self.db.commit()
        return len(SEED_OPERATORS)

    def list_operators(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None,
        target_status: Optional[str] = None,
        target_backend: str = "mps"
    ) -> List[OpCatalogItem]:
        """Query operator coverage items with filtering."""
        query = self.db.query(OpCatalogItem)

        if category:
            query = query.filter(OpCatalogItem.category == category)
        if search:
            query = query.filter(
                (OpCatalogItem.op_name.contains(search)) |
                (OpCatalogItem.pytorch_symbol.contains(search))
            )

        if target_status:
            col = getattr(OpCatalogItem, f"{target_backend.lower()}_status", None)
            if col is not None:
                query = query.filter(col == target_status)

        return query.order_by(OpCatalogItem.request_count.desc()).all()

    def analyze_graph_lowerability(
        self,
        operator_list: List[str],
        target_backend: str = "mps"
    ) -> LowerabilityAnalysisResponse:
        """Analyze whether an operator list can run without fallback transfers on target backend."""
        target_backend = target_backend.lower()
        supported: List[str] = []
        unsupported: List[str] = []

        status_attr = f"{target_backend}_status"

        for op in operator_list:
            # Look up operator in database
            item = self.db.query(OpCatalogItem).filter(
                (OpCatalogItem.op_name == op.lower()) |
                (OpCatalogItem.pytorch_symbol == op)
            ).first()

            if item is not None and hasattr(item, status_attr):
                status_val = getattr(item, status_attr)
                if status_val == "supported":
                    supported.append(op)
                else:
                    unsupported.append(op)
            else:
                # Default behavior for standard ops
                if op in ("matmul", "add", "sub", "mul", "relu", "gelu", "linear", "sum", "mean"):
                    supported.append(op)
                else:
                    unsupported.append(op)

        total = max(len(operator_list), 1)
        lowerability_pct = round((len(supported) / total) * 100.0, 1)
        fallbacks_required = len(unsupported) * 2  # Device-to-Host + Host-to-Device roundtrips

        if unsupported:
            recommendations = [
                f"Graph contains {len(unsupported)} unaccelerated ops on {target_backend.upper()}: {', '.join(unsupported)}.",
                f"Estimated {fallbacks_required} host-device synchronization transfers.",
                "Consider rewriting with elementwise equivalents or custom shader kernels."
            ]
        else:
            recommendations = [
                f"100% lowerable! All {len(supported)} operators have native kernel support on {target_backend.upper()}.",
                "Zero host-device copy overhead expected during execution."
            ]

        return LowerabilityAnalysisResponse(
            target_backend=target_backend,
            total_operators=len(operator_list),
            supported_operators=supported,
            unsupported_operators=unsupported,
            fallback_transfers_required=fallbacks_required,
            lowerability_percentage=lowerability_pct,
            can_execute_zero_fallback=len(unsupported) == 0,
            diagnostic_recommendations=recommendations
        )

    def get_triage_rankings(self) -> List[TriageRankingItem]:
        """Compute community triage priority scores for missing operator support."""
        items = self.db.query(OpCatalogItem).all()
        rankings = []

        for item in items:
            missing = []
            for target in ["mps", "vulkan", "cuda"]:
                val = getattr(item, f"{target}_status", "supported")
                if val != "supported":
                    missing.append(target)

            if missing:
                # Priority = request_count * (missing targets count * 1.5)
                score = round(item.request_count * (len(missing) * 1.5), 1)
                rankings.append(
                    TriageRankingItem(
                        op_name=item.op_name,
                        pytorch_symbol=item.pytorch_symbol,
                        category=item.category,
                        request_count=item.request_count,
                        triage_status=item.triage_status,
                        priority_score=score,
                        missing_targets=missing
                    )
                )

        return sorted(rankings, key=lambda x: x.priority_score, reverse=True)
