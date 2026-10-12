"""Tests for the pure Python dynamic tensor and autograd engine."""

import numpy as np
import pytest
from app.services.tensor_engine import Tensor, trace_computational_graph


def test_tensor_initialization_and_attributes():
    t = Tensor([[1.0, 2.0], [3.0, 4.0]], requires_grad=True)
    assert t.shape == (2, 2)
    assert t.dtype == np.float32
    assert t.requires_grad is True
    assert t.grad is None


def test_tensor_addition_and_gradient():
    a = Tensor([2.0, 3.0], requires_grad=True)
    b = Tensor([4.0, 5.0], requires_grad=True)
    c = a + b
    loss = c.sum()
    loss.backward()

    np.testing.assert_allclose(c.data, np.array([6.0, 8.0]))
    np.testing.assert_allclose(a.grad, np.array([1.0, 1.0]))
    np.testing.assert_allclose(b.grad, np.array([1.0, 1.0]))


def test_tensor_multiplication_and_gradient():
    x = Tensor([3.0, -2.0], requires_grad=True)
    y = Tensor([4.0, 5.0], requires_grad=True)
    z = x * y
    loss = z.sum()
    loss.backward()

    np.testing.assert_allclose(z.data, np.array([12.0, -10.0]))
    np.testing.assert_allclose(x.grad, np.array([4.0, 5.0]))
    np.testing.assert_allclose(y.grad, np.array([3.0, -2.0]))


def test_tensor_matmul_and_gradient():
    x = Tensor([[1.0, 2.0], [3.0, 4.0]], requires_grad=True)
    w = Tensor([[0.5, -0.5], [1.0, 2.0]], requires_grad=True)
    out = x @ w
    loss = out.sum()
    loss.backward()

    # Manual analytical gradient: d(sum(X @ W))/dX = 1 @ W^T, d/dW = X^T @ 1
    expected_out = np.array([[2.5, 3.5], [5.5, 6.5]], dtype=np.float32)
    np.testing.assert_allclose(out.data, expected_out)
    assert x.grad is not None
    assert w.grad is not None


def test_tensor_relu_and_gelu_activations():
    x = Tensor([-2.0, 0.0, 3.0], requires_grad=True)
    r = x.relu()
    np.testing.assert_allclose(r.data, np.array([0.0, 0.0, 3.0]))
    r.sum().backward()
    np.testing.assert_allclose(x.grad, np.array([0.0, 0.0, 1.0]))

    # Test GELU forward values
    y = Tensor([0.0, 1.0], requires_grad=True)
    g = y.gelu()
    np.testing.assert_allclose(g.data[0], 0.0, atol=1e-5)
    assert g.data[1] > 0.8  # GELU(1.0) approx 0.8413


def test_computational_graph_tracing():
    inp = Tensor([1.0, 2.0], requires_grad=False)
    w = Tensor([0.5, 0.5], requires_grad=True)
    b = Tensor([0.1, 0.1], requires_grad=True)
    out = (inp * w + b).relu()

    nodes, edges = trace_computational_graph(out)
    assert len(nodes) >= 4
    assert len(edges) >= 3
    op_types = [n["op_type"] for n in nodes]
    assert "relu" in op_types
    assert "add" in op_types
