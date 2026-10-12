"""Tests for Inductor compiler passes and multi-backend kernel generator."""

import pytest
from app.services.compiler_engine import CompilerEngine, build_preset_graph


@pytest.mark.parametrize("preset", ["mlp", "convnet", "attention"])
def test_preset_graph_construction(preset):
    nodes, edges, input_shapes = build_preset_graph(preset)
    assert len(nodes) > 0
    assert len(edges) > 0
    assert len(input_shapes) > 0


@pytest.mark.parametrize("backend", ["cpu", "mps", "vulkan", "cuda"])
def test_kernel_code_generation_across_backends(backend):
    nodes, edges, _ = build_preset_graph("mlp")
    engine = CompilerEngine(target_backend=backend)
    kernels, metrics = engine.optimize_and_compile(nodes, edges)

    assert len(kernels) > 0
    assert metrics.original_op_count >= len(kernels)
    assert metrics.speedup_percentage >= 0.0

    # Validate generated kernel source includes backend-specific syntax
    all_code = "\n".join(k.source_code for k in kernels)
    if backend == "mps":
        assert "metal" in all_code
        assert "kernel void" in all_code
    elif backend == "vulkan":
        assert "#version 450" in all_code
        assert "gl_GlobalInvocationID" in all_code
    elif backend == "cuda":
        assert "__global__" in all_code
        assert "blockDim" in all_code
    else:  # cpu
        assert "omp parallel" in all_code


def test_dead_code_elimination():
    # Construct graph with an unreferenced dangling node
    nodes = [
        {"id": "input_x", "op_type": "input", "inputs": [], "output_shape": [10, 10]},
        {"id": "dangling_w", "op_type": "weight", "inputs": [], "output_shape": [10, 10]},
        {"id": "dangling_relu", "op_type": "relu", "inputs": ["dangling_w"], "output_shape": [10, 10]},
        {"id": "active_relu", "op_type": "relu", "inputs": ["input_x"], "output_shape": [10, 10]}
    ]
    edges = [
        {"source": "dangling_w", "target": "dangling_relu", "shape": [10, 10]},
        {"source": "input_x", "target": "active_relu", "shape": [10, 10]}
    ]

    engine = CompilerEngine(target_backend="cpu")
    active = engine._eliminate_dead_code(nodes, edges)
    active_ids = [n["id"] for n in active]

    assert "active_relu" in active_ids
    assert "input_x" in active_ids
    assert "dangling_relu" not in active_ids
    assert "dangling_w" not in active_ids
