export interface UserProfile {
  id: string;
  email: string;
  name: string;
  roles: string[];
  is_demo_user: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: UserProfile;
}

export interface OIDCConfig {
  issuer: string;
  client_id: string;
  audience: string;
  jwks_url: string;
  demo_mode_enabled: boolean;
  author: string;
  author_email: string;
}

export interface CompiledKernel {
  kernel_id: string;
  name: string;
  target_backend: string;
  fused_ops: string[];
  source_code: string;
  estimated_flops: number;
  memory_read_bytes: number;
  memory_write_bytes: number;
}

export interface GraphMetrics {
  original_op_count: number;
  fused_kernel_count: number;
  reduction_ratio: number;
  total_flops: number;
  estimated_latency_ms: number;
  baseline_latency_ms: number;
  speedup_percentage: number;
  peak_memory_mb: number;
}

export interface ComputationalGraph {
  id: string;
  name: string;
  description?: string;
  framework: string;
  target_backend: string;
  input_shapes: string;
  nodes: Array<{ id: string; op_type: string; output_shape: number[] }>;
  edges: Array<{ source: string; target: string; shape: number[] }>;
  compiled_kernels: CompiledKernel[];
  metrics: GraphMetrics;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface OpCatalogItem {
  id: string;
  op_name: string;
  category: string;
  pytorch_symbol: string;
  cpu_status: string;
  cuda_status: string;
  mps_status: string;
  vulkan_status: string;
  rocm_status: string;
  min_mps_version: string;
  min_vulkan_version: string;
  request_count: number;
  triage_status: string;
  github_issue_ref?: string;
  pr_reference?: string;
  notes?: string;
  created_at: string;
}

export interface LowerabilityResponse {
  target_backend: string;
  total_operators: number;
  supported_operators: string[];
  unsupported_operators: string[];
  fallback_transfers_required: number;
  lowerability_percentage: number;
  can_execute_zero_fallback: boolean;
  diagnostic_recommendations: string[];
}

export interface TriageRankingItem {
  op_name: string;
  pytorch_symbol: string;
  category: string;
  request_count: number;
  triage_status: string;
  priority_score: number;
  missing_targets: string[];
}

export interface ProfilerRun {
  id: string;
  title: string;
  dataset_name: string;
  sample_count: number;
  worker_count: number;
  batch_size: number;
  ipc_mode: string;
  parent_memory_mb: number;
  worker_memory_mb: number;
  total_memory_mb: number;
  amplification_ratio: number;
  zero_copy_verified: boolean;
  throughput_samples_sec: number;
  notes?: string;
  run_by: string;
  created_at: string;
}

export interface AuditLogItem {
  id: string;
  timestamp: string;
  user_email: string;
  user_role: string;
  action: string;
  resource_type: string;
  resource_id: string;
  status: string;
  details: Record<string, unknown>;
  ip_address: string;
}

export interface PageResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}
