"""SQLAlchemy persistent entities for TensorFoundry."""

from datetime import datetime, timezone
import json
from typing import Any, Dict, List
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Text,
    DateTime,
    Index
)
from app.core.database import Base


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class GraphModel(Base):
    """Stores computational graph architectures and compilation results."""
    __tablename__ = "computational_graphs"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False, index=True)
    description = Column(Text, nullable=True)
    framework = Column(String(64), default="tensor-foundry-py")
    target_backend = Column(String(32), default="cpu", index=True)  # cpu, mps, vulkan, cuda
    input_shapes = Column(Text, default="{}")  # JSON encoded input shapes
    nodes_json = Column(Text, nullable=False, default="[]")
    edges_json = Column(Text, nullable=False, default="[]")
    compiled_kernels_json = Column(Text, nullable=False, default="[]")
    metrics_json = Column(Text, nullable=False, default="{}")
    created_by = Column(String(128), nullable=False, default="system")
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    def get_nodes(self) -> List[Dict[str, Any]]:
        return json.loads(self.nodes_json)

    def get_edges(self) -> List[Dict[str, Any]]:
        return json.loads(self.edges_json)

    def get_compiled_kernels(self) -> List[Dict[str, Any]]:
        return json.loads(self.compiled_kernels_json)

    def get_metrics(self) -> Dict[str, Any]:
        return json.loads(self.metrics_json)


class OpCatalogItem(Base):
    """Stores hardware operator coverage across CPU, CUDA, MPS, Vulkan, and ROCm."""
    __tablename__ = "operator_catalog"

    id = Column(String(64), primary_key=True, index=True)
    op_name = Column(String(128), nullable=False, unique=True, index=True)
    category = Column(String(64), default="tensor_math", index=True)  # math, linalg, vision, activation, indexing
    pytorch_symbol = Column(String(128), nullable=False)
    cpu_status = Column(String(32), default="supported")  # supported, partial, planned, unsupported
    cuda_status = Column(String(32), default="supported")
    mps_status = Column(String(32), default="supported")
    vulkan_status = Column(String(32), default="supported")
    rocm_status = Column(String(32), default="supported")
    min_mps_version = Column(String(16), default="2.0")
    min_vulkan_version = Column(String(16), default="1.2")
    request_count = Column(Integer, default=0, index=True)
    triage_status = Column(String(32), default="stable", index=True)  # stable, in_progress, to_implement, to_triage
    github_issue_ref = Column(String(64), nullable=True)
    pr_reference = Column(String(256), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class ProfilerRun(Base):
    """Stores DataLoader worker memory amplification benchmarks."""
    __tablename__ = "profiler_runs"

    id = Column(String(64), primary_key=True, index=True)
    title = Column(String(128), nullable=False)
    dataset_name = Column(String(128), default="ImageNet-Synthetic")
    sample_count = Column(Integer, default=50000)
    worker_count = Column(Integer, nullable=False, default=4)
    batch_size = Column(Integer, default=128)
    ipc_mode = Column(String(32), nullable=False)  # fork_python_list, fork_numpy_array, spawn_shared_ipc
    parent_memory_mb = Column(Float, nullable=False)
    worker_memory_mb = Column(Float, nullable=False)
    total_memory_mb = Column(Float, nullable=False)
    amplification_ratio = Column(Float, nullable=False)
    zero_copy_verified = Column(Boolean, default=False)
    throughput_samples_sec = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    run_by = Column(String(128), default="system")
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class AuditLog(Base):
    """Audit log capturing security and mutation operations with UTC timestamps."""
    __tablename__ = "audit_logs"

    id = Column(String(64), primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    user_email = Column(String(128), nullable=False, index=True)
    user_role = Column(String(64), nullable=False)
    action = Column(String(64), nullable=False, index=True)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(String(64), nullable=False)
    status = Column(String(32), default="SUCCESS")
    details_json = Column(Text, default="{}")
    ip_address = Column(String(64), default="127.0.0.1")

    def get_details(self) -> Dict[str, Any]:
        return json.loads(self.details_json)


Index("idx_audit_user_action", AuditLog.user_email, AuditLog.action)
Index("idx_op_category_triage", OpCatalogItem.category, OpCatalogItem.triage_status)
