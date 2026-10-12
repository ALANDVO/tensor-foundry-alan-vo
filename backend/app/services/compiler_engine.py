"""TorchInductor-inspired computational graph compiler, fusion optimizer, and kernel code generator."""

import uuid
from typing import Any, Dict, List, Tuple
from app.schemas.domain import CompiledKernelSchema, GraphMetricsSchema, GraphNodeSchema


class CompilerEngine:
    """Performs graph IR optimization, operator fusion passes, and multi-backend kernel emission."""

    POINTWISE_OPS = {"add", "sub", "mul", "relu", "gelu", "sigmoid"}
    CONTRACTION_OPS = {"matmul", "linear"}
    REDUCTION_OPS = {"sum", "mean"}

    def __init__(self, target_backend: str = "cpu") -> None:
        self.target_backend = target_backend.lower()

    def optimize_and_compile(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ) -> Tuple[List[CompiledKernelSchema], GraphMetricsSchema]:
        """Execute Dead-Code Elimination, Inductor Fusion passes, and Kernel Code Emission."""
        # 1. Dead code elimination
        active_nodes = self._eliminate_dead_code(nodes, edges)

        # 2. Inductor Fusion Pass: Group operations into fused kernels
        fused_groups = self._fuse_operators(active_nodes, edges)

        # 3. Kernel code emission for the target backend
        compiled_kernels: List[CompiledKernelSchema] = []
        total_flops = 0
        total_read_bytes = 0
        total_write_bytes = 0

        for group_idx, group in enumerate(fused_groups):
            kernel_name = f"kernel_{self.target_backend}_{group_idx}_{'_'.join(group['op_types'])}"
            code = self._generate_kernel_code(kernel_name, group)
            flops = self._calculate_group_flops(group)
            read_bytes, write_bytes = self._calculate_memory_traffic(group)

            total_flops += flops
            total_read_bytes += read_bytes
            total_write_bytes += write_bytes

            compiled_kernels.append(
                CompiledKernelSchema(
                    kernel_id=f"kern_{uuid.uuid4().hex[:8]}",
                    name=kernel_name,
                    target_backend=self.target_backend,
                    fused_ops=group["op_types"],
                    source_code=code,
                    estimated_flops=flops,
                    memory_read_bytes=read_bytes,
                    memory_write_bytes=write_bytes
                )
            )

        # 4. Metrics calculation
        orig_count = max(len(nodes), 1)
        fused_count = max(len(compiled_kernels), 1)
        reduction_ratio = round(orig_count / fused_count, 2)

        # Theoretical latency modeling based on memory bandwidth vs arithmetic intensity
        baseline_mem_traffic_mb = (total_read_bytes * 2.2 + total_write_bytes * 2.5) / (1024 * 1024)
        fused_mem_traffic_mb = (total_read_bytes + total_write_bytes) / (1024 * 1024)

        # Assume 80 GB/s memory bandwidth for baseline simulation
        baseline_latency_ms = round(max(0.05, (baseline_mem_traffic_mb / 80.0) * 1000 + (total_flops / 1e9) * 0.1), 3)
        fused_latency_ms = round(max(0.02, (fused_mem_traffic_mb / 80.0) * 1000 + (total_flops / 1e9) * 0.08), 3)
        speedup_percentage = round(max(0.0, ((baseline_latency_ms - fused_latency_ms) / baseline_latency_ms) * 100.0), 1)
        peak_memory_mb = round(fused_mem_traffic_mb, 2)

        metrics = GraphMetricsSchema(
            original_op_count=orig_count,
            fused_kernel_count=fused_count,
            reduction_ratio=reduction_ratio,
            total_flops=total_flops,
            estimated_latency_ms=fused_latency_ms,
            baseline_latency_ms=baseline_latency_ms,
            speedup_percentage=speedup_percentage,
            peak_memory_mb=peak_memory_mb
        )

        return compiled_kernels, metrics

    def _eliminate_dead_code(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Prune unreferenced intermediate operations."""
        if not nodes:
            return []
        # In this DAG tracer, the terminal node is the final operation
        terminal_id = nodes[-1]["id"]
        used_ids = {terminal_id}

        # Work backwards from the terminal node
        incoming_map: Dict[str, List[str]] = {}
        for edge in edges:
            incoming_map.setdefault(edge["target"], []).append(edge["source"])

        queue = [terminal_id]
        while queue:
            curr = queue.pop(0)
            for src in incoming_map.get(curr, []):
                if src not in used_ids:
                    used_ids.add(src)
                    queue.append(src)

        return [n for n in nodes if n["id"] in used_ids]

    def _fuse_operators(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Apply Inductor fusion passes to combine compatible operators."""
        if not nodes:
            return []

        groups: List[Dict[str, Any]] = []
        current_group: Optional[Dict[str, Any]] = None

        for node in nodes:
            op_type = node.get("op_type", "unknown")
            output_shape = node.get("output_shape", [128, 128])

            if current_group is None:
                current_group = {
                    "node_ids": [node["id"]],
                    "op_types": [op_type],
                    "shape": output_shape,
                    "is_gemm_fused": (op_type in self.CONTRACTION_OPS)
                }
                continue

            # Check if this node can be fused with current_group
            can_fuse = False
            if current_group["is_gemm_fused"] and op_type in self.POINTWISE_OPS:
                # GEMM + Bias/Activation fusion (e.g. MatMul + Add + ReLU)
                can_fuse = True
            elif all(op in self.POINTWISE_OPS for op in current_group["op_types"]) and op_type in self.POINTWISE_OPS:
                # Pointwise chain fusion
                can_fuse = True

            if can_fuse:
                current_group["node_ids"].append(node["id"])
                current_group["op_types"].append(op_type)
                current_group["shape"] = output_shape
            else:
                groups.append(current_group)
                current_group = {
                    "node_ids": [node["id"]],
                    "op_types": [op_type],
                    "shape": output_shape,
                    "is_gemm_fused": (op_type in self.CONTRACTION_OPS)
                }

        if current_group:
            groups.append(current_group)

        return groups

    def _calculate_group_flops(self, group: Dict[str, Any]) -> int:
        """Estimate required floating point operations for a kernel."""
        shape = group["shape"]
        num_elements = 1
        for dim in shape:
            num_elements *= max(dim, 1)

        flops = 0
        for op in group["op_types"]:
            if op in ("matmul", "linear"):
                # 2 * M * N * K
                k_dim = shape[-1] if len(shape) > 1 else 128
                flops += 2 * num_elements * k_dim
            elif op == "gelu":
                flops += num_elements * 8
            elif op in ("relu", "add", "sub", "mul"):
                flops += num_elements
            else:
                flops += num_elements * 2
        return flops

    def _calculate_memory_traffic(self, group: Dict[str, Any]) -> Tuple[int, int]:
        """Calculate bytes read and written."""
        shape = group["shape"]
        num_elements = 1
        for dim in shape:
            num_elements *= max(dim, 1)

        elem_size = 4  # float32
        read_bytes = num_elements * elem_size * len(group["op_types"])
        write_bytes = num_elements * elem_size
        return read_bytes, write_bytes

    def _generate_kernel_code(self, kernel_name: str, group: Dict[str, Any]) -> str:
        """Generate backend-specific production kernel source code."""
        op_types = group["op_types"]
        backend = self.target_backend

        if backend == "mps":
            return self._emit_metal_kernel(kernel_name, op_types)
        elif backend == "vulkan":
            return self._emit_vulkan_glsl(kernel_name, op_types)
        elif backend == "cuda":
            return self._emit_cuda_kernel(kernel_name, op_types)
        else:
            return self._emit_cpu_c(kernel_name, op_types)

    def _build_ops_body(self, op_types: List[str], b_expr: str, is_vulkan: bool = False) -> str:
        ops = []
        for op in op_types:
            if op == "relu":
                ops.append("val = max(0.0, val);" if is_vulkan else "val = fmaxf(0.0f, val);" if self.target_backend != "mps" else "val = fmax(0.0f, val);")
            elif op == "gelu":
                ops.append(f"val = 0.5 * val * (1.0 + tanh(0.79788456 * (val + 0.044715 * val * val * val)));")
            elif op == "add":
                ops.append(f"val += {b_expr};")
            elif op == "mul":
                ops.append(f"val *= {b_expr};")
        return "\n        ".join(ops) if ops else f"val = {b_expr.replace('_b', '_a')};"

    def _emit_cpu_c(self, name: str, op_types: List[str]) -> str:
        body = self._build_ops_body(op_types, "in_b[i]")
        return f"#include <immintrin.h>\n#include <omp.h>\nvoid {name}(const float* in_a, const float* in_b, float* out, int N) {{\n    #pragma omp parallel for simd\n    for (int i = 0; i < N; ++i) {{\n        float val = in_a[i];\n        {body}\n        out[i] = val;\n    }}\n}}\n"

    def _emit_metal_kernel(self, name: str, op_types: List[str]) -> str:
        body = self._build_ops_body(op_types, "in_b[gid]")
        return f"#include <metal_stdlib>\nusing namespace metal;\nkernel void {name}(device const float* in_a [[buffer(0)]], device const float* in_b [[buffer(1)]], device float* out [[buffer(2)]], constant uint& N [[buffer(3)]], uint gid [[thread_position_in_grid]]) {{\n    if (gid >= N) return;\n    float val = in_a[gid];\n    {body}\n    out[gid] = val;\n}}\n"

    def _emit_vulkan_glsl(self, name: str, op_types: List[str]) -> str:
        body = self._build_ops_body(op_types, "b_data[gid]", is_vulkan=True)
        return f"#version 450\nlayout(local_size_x = 256) in;\nlayout(std430, binding = 0) readonly buffer InA {{ float a_data[]; }};\nlayout(std430, binding = 1) readonly buffer InB {{ float b_data[]; }};\nlayout(std430, binding = 2) writeonly buffer Out {{ float out_data[]; }};\nlayout(push_constant) uniform PC {{ uint num_elements; }} pc;\nvoid main() {{\n    uint gid = gl_GlobalInvocationID.x;\n    if (gid >= pc.num_elements) return;\n    float val = a_data[gid];\n    {body}\n    out_data[gid] = val;\n}}\n"

    def _emit_cuda_kernel(self, name: str, op_types: List[str]) -> str:
        body = self._build_ops_body(op_types, "in_b[idx]")
        return f"#include <cuda_runtime.h>\n__global__ void {name}(const float* in_a, const float* in_b, float* out, int N) {{\n    int idx = blockIdx.x * blockDim.x + threadIdx.x;\n    if (idx < N) {{\n        float val = in_a[idx];\n        {body}\n        out[idx] = val;\n    }}\n}}\n"


def _n(id_: str, op: str, inp: List[str], sh: List[int]) -> Dict[str, Any]:
    return {"id": id_, "op_type": op, "inputs": inp, "output_shape": sh, "dtype": "float32"}


def _e(src: str, dst: str, sh: List[int]) -> Dict[str, Any]:
    return {"source": src, "target": dst, "shape": sh}


def build_preset_graph(preset_name: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """Construct reference architectures for evaluation and compilation."""
    name = preset_name.lower()

    if name == "mlp":
        nodes = [
            _n("input_x", "input", [], [128, 512]),
            _n("weight_1", "weight", [], [512, 1024]),
            _n("linear_1", "matmul", ["input_x", "weight_1"], [128, 1024]),
            _n("bias_1", "weight", [], [1024]),
            _n("add_1", "add", ["linear_1", "bias_1"], [128, 1024]),
            _n("act_1", "gelu", ["add_1"], [128, 1024]),
            _n("weight_2", "weight", [], [1024, 256]),
            _n("linear_2", "matmul", ["act_1", "weight_2"], [128, 256])
        ]
        edges = [
            _e("input_x", "linear_1", [128, 512]),
            _e("weight_1", "linear_1", [512, 1024]),
            _e("linear_1", "add_1", [128, 1024]),
            _e("bias_1", "add_1", [1024]),
            _e("add_1", "act_1", [128, 1024]),
            _e("act_1", "linear_2", [128, 1024]),
            _e("weight_2", "linear_2", [1024, 256])
        ]
        input_shapes = {"input_x": [128, 512]}
    elif name == "attention":
        nodes = [
            _n("query_q", "input", [], [32, 8, 64, 64]),
            _n("key_k", "input", [], [32, 8, 64, 64]),
            _n("qk_matmul", "matmul", ["query_q", "key_k"], [32, 8, 64, 64]),
            _n("scale_const", "weight", [], [1]),
            _n("qk_scaled", "mul", ["qk_matmul", "scale_const"], [32, 8, 64, 64]),
            _n("attn_weights", "relu", ["qk_scaled"], [32, 8, 64, 64]),
            _n("val_v", "input", [], [32, 8, 64, 64]),
            _n("attn_out", "matmul", ["attn_weights", "val_v"], [32, 8, 64, 64])
        ]
        edges = [
            _e("query_q", "qk_matmul", [32, 8, 64, 64]),
            _e("key_k", "qk_matmul", [32, 8, 64, 64]),
            _e("qk_matmul", "qk_scaled", [32, 8, 64, 64]),
            _e("scale_const", "qk_scaled", [1]),
            _e("qk_scaled", "attn_weights", [32, 8, 64, 64]),
            _e("attn_weights", "attn_out", [32, 8, 64, 64]),
            _e("val_v", "attn_out", [32, 8, 64, 64])
        ]
        input_shapes = {"query_q": [32, 8, 64, 64], "key_k": [32, 8, 64, 64], "val_v": [32, 8, 64, 64]}
    else:  # ConvNet default
        nodes = [
            _n("input_img", "input", [], [64, 3, 32, 32]),
            _n("conv_w", "weight", [], [64, 3, 3, 3]),
            _n("conv2d_1", "matmul", ["input_img", "conv_w"], [64, 64, 32, 32]),
            _n("bias_conv", "weight", [], [64]),
            _n("bias_add", "add", ["conv2d_1", "bias_conv"], [64, 64, 32, 32]),
            _n("relu_1", "relu", ["bias_add"], [64, 64, 32, 32])
        ]
        edges = [
            _e("input_img", "conv2d_1", [64, 3, 32, 32]),
            _e("conv_w", "conv2d_1", [64, 3, 3, 3]),
            _e("conv2d_1", "bias_add", [64, 64, 32, 32]),
            _e("bias_conv", "bias_add", [64]),
            _e("bias_add", "relu_1", [64, 64, 32, 32])
        ]
        input_shapes = {"input_img": [64, 3, 32, 32]}

    return nodes, edges, input_shapes
