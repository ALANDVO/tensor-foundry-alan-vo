"""Pydantic schemas for request validation and response envelopes."""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field, ConfigDict

T = TypeVar("T")


class PageResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int


# ================= User & Auth Schemas =================

class UserProfile(BaseModel):
    id: str
    email: str
    name: str
    roles: List[str]
    is_demo_user: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserProfile


class DemoLoginRequest(BaseModel):
    username: str = Field(default="alan_engineer")
    requested_role: str = Field(default="operator")  # viewer, operator, admin


class OIDCConfigResponse(BaseModel):
    issuer: str
    client_id: str
    audience: str
    jwks_url: str
    demo_mode_enabled: bool
    author: str
    author_email: str


# ================= Tensor & Graph Schemas =================

class GraphNodeSchema(BaseModel):
    id: str
    op_type: str
    inputs: List[str]
    output_shape: List[int]
    dtype: str = "float32"
    attributes: Dict[str, Any] = Field(default_factory=dict)


class GraphEdgeSchema(BaseModel):
    source: str
    target: str
    shape: List[int]


class CompiledKernelSchema(BaseModel):
    kernel_id: str
    name: str
    target_backend: str  # cpu, mps, vulkan, cuda
    fused_ops: List[str]
    source_code: str
    estimated_flops: int
    memory_read_bytes: int
    memory_write_bytes: int


class GraphMetricsSchema(BaseModel):
    original_op_count: int
    fused_kernel_count: int
    reduction_ratio: float
    total_flops: int
    estimated_latency_ms: float
    baseline_latency_ms: float
    speedup_percentage: float
    peak_memory_mb: float


class GraphCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)
    description: Optional[str] = None
    target_backend: str = Field(default="cpu")  # cpu, mps, vulkan, cuda
    architecture_preset: Optional[str] = None  # mlp, convnet, attention, custom
    custom_nodes: Optional[List[GraphNodeSchema]] = None


class GraphResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str]
    framework: str
    target_backend: str
    input_shapes: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    compiled_kernels: List[CompiledKernelSchema]
    metrics: GraphMetricsSchema
    created_by: str
    created_at: datetime
    updated_at: datetime


# ================= Hardware Operator Coverage Schemas =================

class OpCatalogItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    op_name: str
    category: str
    pytorch_symbol: str
    cpu_status: str
    cuda_status: str
    mps_status: str
    vulkan_status: str
    rocm_status: str
    min_mps_version: str
    min_vulkan_version: str
    request_count: int
    triage_status: str
    github_issue_ref: Optional[str] = None
    pr_reference: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime


class LowerabilityAnalysisRequest(BaseModel):
    graph_id: Optional[str] = None
    target_backend: str = Field(..., description="Target hardware: mps, vulkan, cuda, rocm")
    operator_list: Optional[List[str]] = None


class LowerabilityAnalysisResponse(BaseModel):
    target_backend: str
    total_operators: int
    supported_operators: List[str]
    unsupported_operators: List[str]
    fallback_transfers_required: int
    lowerability_percentage: float
    can_execute_zero_fallback: bool
    diagnostic_recommendations: List[str]


class TriageRankingItem(BaseModel):
    op_name: str
    pytorch_symbol: str
    category: str
    request_count: int
    triage_status: str
    priority_score: float
    missing_targets: List[str]


# ================= DataLoader Memory Profiler Schemas =================

class ProfilerSimulateRequest(BaseModel):
    title: str = Field(default="Synthetic DataLoader Benchmark")
    sample_count: int = Field(default=50000, ge=1000, le=1000000)
    worker_count: int = Field(default=4, ge=0, le=32)
    batch_size: int = Field(default=128, ge=1, le=1024)
    item_size_bytes: int = Field(default=4096, ge=128, le=65536)
    ipc_mode: str = Field(default="fork_python_list")  # fork_python_list, fork_numpy_array, spawn_shared_ipc


class ProfilerRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    dataset_name: str
    sample_count: int
    worker_count: int
    batch_size: int
    ipc_mode: str
    parent_memory_mb: float
    worker_memory_mb: float
    total_memory_mb: float
    amplification_ratio: float
    zero_copy_verified: bool
    throughput_samples_sec: float
    notes: Optional[str]
    run_by: str
    created_at: datetime


# ================= Advisory LLM Schemas =================

class AdvisorRequest(BaseModel):
    graph_id: Optional[str] = None
    target_backend: str = "mps"
    focus_area: str = "fusion_and_memory"  # fusion_and_memory, op_coverage, data_loading
    prompt_context: Optional[str] = None


class AdvisorResponse(BaseModel):
    provider: str
    model: str
    status: str  # ADVISORY_GROUNDED, DEMO_SIMULATED, ERROR
    analysis: str
    recommendations: List[str]
    grounded_metrics: Dict[str, Any]
    advisory_disclaimer: str = (
        "Advisory explanation only. Deterministic compilation and benchmarks remain authoritative."
    )


# ================= Audit Schemas =================

class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    timestamp: datetime
    user_email: str
    user_role: str
    action: str
    resource_type: str
    resource_id: str
    status: str
    details: Dict[str, Any]
    ip_address: str
