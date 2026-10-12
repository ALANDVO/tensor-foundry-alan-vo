import "@testing-library/jest-dom/vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { AuthProvider } from "../context/AuthContext";
import { GraphCompilerView } from "../components/GraphCompilerView";
import { apiClient } from "../api/client";

describe("GraphCompilerView Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loaded graph metrics and kernel source", async () => {
    vi.spyOn(apiClient, "listGraphs").mockResolvedValue({
      items: [
        {
          id: "graph_direct_1",
          name: "Direct MLP Graph",
          framework: "tensor-foundry-py",
          target_backend: "mps",
          input_shapes: "{}",
          nodes: [],
          edges: [],
          compiled_kernels: [
            {
              kernel_id: "kern_direct_1",
              name: "kernel_mps_0_fused",
              target_backend: "mps",
              fused_ops: ["matmul", "gelu"],
              source_code: "kernel void direct_kernel() {}",
              estimated_flops: 500000,
              memory_read_bytes: 1024,
              memory_write_bytes: 512
            }
          ],
          metrics: {
            original_op_count: 4,
            fused_kernel_count: 1,
            reduction_ratio: 4.0,
            total_flops: 500000,
            estimated_latency_ms: 0.08,
            baseline_latency_ms: 0.24,
            speedup_percentage: 66.7,
            peak_memory_mb: 1.5
          },
          created_by: "alanvo@gmail.com",
          created_at: "2026-10-12T12:00:00Z",
          updated_at: "2026-10-12T12:00:00Z"
        }
      ],
      total: 1,
      page: 1,
      page_size: 10,
      pages: 1
    });

    render(
      <AuthProvider>
        <GraphCompilerView />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Optimization Metrics/i)).toBeInTheDocument();
      expect(screen.getByText(/fusion reduction/i)).toBeInTheDocument();
    });
  });
});
