"""Pure Python / NumPy-backed dynamic tensor and reverse-mode autograd engine."""

from __future__ import annotations
import math
from typing import Callable, List, Optional, Sequence, Set, Tuple, Union
import numpy as np


def _unbroadcast(grad: np.ndarray, target_shape: Tuple[int, ...]) -> np.ndarray:
    for _ in range(grad.ndim - len(target_shape)):
        grad = grad.sum(axis=0)
    for i, dim in enumerate(target_shape):
        if dim == 1:
            grad = grad.sum(axis=i, keepdims=True)
    return grad


class Tensor:
    """Dynamic multi-dimensional tensor supporting reverse-mode autograd."""

    def __init__(
        self,
        data: Union[int, float, list, np.ndarray],
        requires_grad: bool = False,
        op_name: str = "leaf",
        parents: Optional[Sequence[Tensor]] = None
    ) -> None:
        if isinstance(data, np.ndarray):
            self.data = data.astype(np.float32)
        else:
            self.data = np.array(data, dtype=np.float32)

        self.requires_grad = requires_grad
        self.grad: Optional[np.ndarray] = None
        self.op_name = op_name
        self._parents: List[Tensor] = list(parents) if parents else []
        self._backward_fn: Optional[Callable[[], None]] = None

    @property
    def shape(self) -> Tuple[int, ...]:
        return self.data.shape

    @property
    def strides(self) -> Tuple[int, ...]:
        return self.data.strides

    @property
    def dtype(self) -> np.dtype:
        return self.data.dtype

    def __repr__(self) -> str:
        return f"Tensor(shape={self.shape}, op='{self.op_name}', requires_grad={self.requires_grad})"

    def backward(self, grad_output: Optional[np.ndarray] = None) -> None:
        """Run reverse-mode automatic differentiation through the dynamic computational DAG."""
        if grad_output is None:
            if self.data.size == 1:
                grad_output = np.ones_like(self.data)
            else:
                raise ValueError("Grad can only be created implicitly for scalar outputs")

        self.grad = grad_output

        # Topologically sort computation nodes
        topo: List[Tensor] = []
        visited: Set[Tensor] = set()

        def build_topo(v: Tensor) -> None:
            if v not in visited:
                visited.add(v)
                for parent in v._parents:
                    build_topo(parent)
                topo.append(v)

        build_topo(self)

        # Backpropagate in reverse topological order
        for node in reversed(topo):
            if node._backward_fn is not None:
                node._backward_fn()

    # ================= Elementwise Operations =================

    def __add__(self, other: Union[Tensor, float, int]) -> Tensor:
        other_t = other if isinstance(other, Tensor) else Tensor(other)
        out = Tensor(
            self.data + other_t.data,
            requires_grad=self.requires_grad or other_t.requires_grad,
            op_name="add",
            parents=[self, other_t]
        )

        def _backward():
            if self.requires_grad:
                g = _unbroadcast(out.grad, self.data.shape)
                self.grad = g if self.grad is None else self.grad + g
            if other_t.requires_grad:
                g = _unbroadcast(out.grad, other_t.data.shape)
                other_t.grad = g if other_t.grad is None else other_t.grad + g
        out._backward_fn = _backward
        return out

    def __radd__(self, other: Union[float, int]) -> Tensor:
        return self.__add__(other)

    def __sub__(self, other: Union[Tensor, float, int]) -> Tensor:
        other_t = other if isinstance(other, Tensor) else Tensor(other)
        out = Tensor(
            self.data - other_t.data,
            requires_grad=self.requires_grad or other_t.requires_grad,
            op_name="sub",
            parents=[self, other_t]
        )
        def _backward():
            if self.requires_grad:
                g = _unbroadcast(out.grad, self.data.shape)
                self.grad = g if self.grad is None else self.grad + g
            if other_t.requires_grad:
                g = _unbroadcast(-out.grad, other_t.data.shape)
                other_t.grad = g if other_t.grad is None else other_t.grad + g
        out._backward_fn = _backward
        return out

    def __mul__(self, other: Union[Tensor, float, int]) -> Tensor:
        other_t = other if isinstance(other, Tensor) else Tensor(other)
        out = Tensor(
            self.data * other_t.data,
            requires_grad=self.requires_grad or other_t.requires_grad,
            op_name="mul",
            parents=[self, other_t]
        )
        def _backward():
            if self.requires_grad:
                g = _unbroadcast(out.grad * other_t.data, self.data.shape)
                self.grad = g if self.grad is None else self.grad + g
            if other_t.requires_grad:
                g = _unbroadcast(out.grad * self.data, other_t.data.shape)
                other_t.grad = g if other_t.grad is None else other_t.grad + g
        out._backward_fn = _backward
        return out

    def __rmul__(self, other: Union[float, int]) -> Tensor:
        return self.__mul__(other)

    def __matmul__(self, other: Tensor) -> Tensor:
        """Matrix multiplication supporting batched and 2D operations."""
        if not isinstance(other, Tensor):
            raise TypeError("Matrix multiplication operand must be a Tensor")

        out = Tensor(
            np.matmul(self.data, other.data),
            requires_grad=self.requires_grad or other.requires_grad,
            op_name="matmul",
            parents=[self, other]
        )

        def _backward():
            if self.requires_grad:
                # dL/dA = dL/dOut @ B^T
                b_t = np.swapaxes(other.data, -1, -2)
                grad_a = np.matmul(out.grad, b_t)
                self.grad = grad_a if self.grad is None else self.grad + grad_a

            if other.requires_grad:
                # dL/dB = A^T @ dL/dOut
                a_t = np.swapaxes(self.data, -1, -2)
                grad_b = np.matmul(a_t, out.grad)
                other.grad = grad_b if other.grad is None else other.grad + grad_b

        out._backward_fn = _backward
        return out

    # ================= Nonlinearities & Activations =================

    def relu(self) -> Tensor:
        out = Tensor(
            np.maximum(0, self.data),
            requires_grad=self.requires_grad,
            op_name="relu",
            parents=[self]
        )

        def _backward():
            if self.requires_grad:
                grad = out.grad * (self.data > 0)
                self.grad = grad if self.grad is None else self.grad + grad

        out._backward_fn = _backward
        return out

    def gelu(self) -> Tensor:
        """Gaussian Error Linear Unit with tanh approximation."""
        c = math.sqrt(2.0 / math.pi)
        inner = c * (self.data + 0.044715 * np.power(self.data, 3))
        tanh_out = np.tanh(inner)
        out_data = 0.5 * self.data * (1.0 + tanh_out)

        out = Tensor(
            out_data,
            requires_grad=self.requires_grad,
            op_name="gelu",
            parents=[self]
        )

        def _backward():
            if self.requires_grad:
                dtanh = 1.0 - np.square(tanh_out)
                dinner = c * (1.0 + 3.0 * 0.044715 * np.square(self.data))
                grad_x = 0.5 * (1.0 + tanh_out) + 0.5 * self.data * dtanh * dinner
                grad = out.grad * grad_x
                self.grad = grad if self.grad is None else self.grad + grad

        out._backward_fn = _backward
        return out

    def sum(self, axis: Optional[Union[int, Tuple[int, ...]]] = None, keepdims: bool = False) -> Tensor:
        out_data = np.sum(self.data, axis=axis, keepdims=keepdims)
        out = Tensor(
            out_data,
            requires_grad=self.requires_grad,
            op_name="sum",
            parents=[self]
        )

        def _backward():
            if self.requires_grad:
                grad = out.grad
                if not keepdims and axis is not None:
                    # Reshape grad for broadcasting
                    axes = [axis] if isinstance(axis, int) else list(axis)
                    shape = list(self.data.shape)
                    for a in axes:
                        shape[a] = 1
                    grad = np.reshape(grad, shape)
                grad = np.broadcast_to(grad, self.data.shape)
                self.grad = grad if self.grad is None else self.grad + grad

        out._backward_fn = _backward
        return out

    def mean(self, axis: Optional[Union[int, Tuple[int, ...]]] = None, keepdims: bool = False) -> Tensor:
        count = self.data.size if axis is None else (
            self.data.shape[axis] if isinstance(axis, int) else np.prod([self.data.shape[a] for a in axis])
        )
        return self.sum(axis=axis, keepdims=keepdims) * (1.0 / count)


def trace_computational_graph(root: Tensor) -> Tuple[List[dict], List[dict]]:
    """Extract computational graph nodes and edges from an autograd DAG."""
    nodes: List[dict] = []
    edges: List[dict] = []
    visited: Set[Tensor] = set()
    node_id_map = {}
    counter = 0

    def visit(node: Tensor) -> str:
        nonlocal counter
        if node in visited:
            return node_id_map[node]

        visited.add(node)
        node_id = f"node_{counter}_{node.op_name}"
        node_id_map[node] = node_id
        counter += 1

        parent_ids = []
        for p in node._parents:
            pid = visit(p)
            parent_ids.append(pid)
            edges.append({
                "source": pid,
                "target": node_id,
                "shape": list(p.shape)
            })

        nodes.append({
            "id": node_id,
            "op_type": node.op_name,
            "inputs": parent_ids,
            "output_shape": list(node.shape),
            "dtype": str(node.dtype)
        })
        return node_id

    visit(root)
    return nodes, edges
