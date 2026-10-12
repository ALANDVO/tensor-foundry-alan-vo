import "@testing-library/jest-dom/vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { App } from "../App";

describe("TensorFoundry Web Console UI", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((url: string) => {
        if (url.includes("/api/v1/auth/config")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: () =>
              Promise.resolve({
                issuer: "http://127.0.0.1:8080/realms/tensor-foundry",
                client_id: "tensor-foundry-client",
                audience: "tensor-foundry-api",
                jwks_url: "http://127.0.0.1:8080/realms/tensor-foundry/protocol/openid-connect/certs",
                demo_mode_enabled: true,
                author: "Alan Vo",
                author_email: "alanvo@gmail.com"
              })
          });
        }
        if (url.includes("/api/v1/auth/demo-login")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: () =>
              Promise.resolve({
                access_token: "mock-jwt-token-xyz",
                token_type: "Bearer",
                expires_in: 7200,
                user: {
                  id: "demo_user_alan_engineer",
                  email: "alan_engineer@example.com",
                  name: "Demo Alan_engineer",
                  roles: ["operator", "viewer"],
                  is_demo_user: true
                }
              })
          });
        }
        if (url.includes("/api/v1/compiler/graphs")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: () =>
              Promise.resolve({
                items: [
                  {
                    id: "graph_test_1",
                    name: "MLP Fused Model",
                    framework: "tensor-foundry-py",
                    target_backend: "mps",
                    input_shapes: "{}",
                    nodes: [],
                    edges: [],
                    compiled_kernels: [
                      {
                        kernel_id: "kern_1",
                        name: "kernel_mps_0_matmul_add_gelu",
                        target_backend: "mps",
                        fused_ops: ["matmul", "add", "gelu"],
                        source_code: "kernel void fused_mps_test() {}",
                        estimated_flops: 1000000,
                        memory_read_bytes: 4096,
                        memory_write_bytes: 2048
                      }
                    ],
                    metrics: {
                      original_op_count: 5,
                      fused_kernel_count: 1,
                      reduction_ratio: 5.0,
                      total_flops: 1000000,
                      estimated_latency_ms: 0.12,
                      baseline_latency_ms: 0.35,
                      speedup_percentage: 65.7,
                      peak_memory_mb: 2.5
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
              })
          });
        }
        if (url.includes("/api/v1/coverage/matrix")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: () =>
              Promise.resolve([
                {
                  id: "op_1",
                  op_name: "max_pool3d_with_indices",
                  category: "vision_3d",
                  pytorch_symbol: "aten::max_pool3d_with_indices",
                  cpu_status: "supported",
                  cuda_status: "supported",
                  mps_status: "supported",
                  vulkan_status: "planned",
                  rocm_status: "supported",
                  min_mps_version: "2.9",
                  min_vulkan_version: "1.3",
                  request_count: 16,
                  triage_status: "stable",
                  created_at: "2026-10-12T12:00:00Z"
                }
              ])
          });
        }
        if (url.includes("/api/v1/coverage/triage")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: () =>
              Promise.resolve([
                {
                  op_name: "max_pool3d_with_indices",
                  pytorch_symbol: "aten::max_pool3d_with_indices",
                  category: "vision_3d",
                  request_count: 16,
                  triage_status: "stable",
                  priority_score: 24.0,
                  missing_targets: ["vulkan"]
                }
              ])
          });
        }
        if (url.includes("/api/v1/profiler/runs")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: () =>
              Promise.resolve([
                {
                  id: "prof_1",
                  title: "Run: 4 workers",
                  dataset_name: "Dataset",
                  sample_count: 50000,
                  worker_count: 4,
                  batch_size: 128,
                  ipc_mode: "fork_python_list",
                  parent_memory_mb: 200.0,
                  worker_memory_mb: 800.0,
                  total_memory_mb: 1000.0,
                  amplification_ratio: 5.0,
                  zero_copy_verified: false,
                  throughput_samples_sec: 1200.0,
                  notes: "Severe memory leak due to COW dirtying",
                  run_by: "alanvo@gmail.com",
                  created_at: "2026-10-12T12:00:00Z"
                }
              ])
          });
        }
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({})
        });
      })
    );
  });

  it("renders header branding and Alan Vo identity", async () => {
    render(<App />);
    expect(screen.getByText("TensorFoundry")).toBeInTheDocument();
    expect(screen.getByText("Alan Vo")).toBeInTheDocument();
  });

  it("navigates across all four workflow tabs", async () => {
    render(<App />);

    // Check default tab
    expect(screen.getByText("Inductor Graph Tracer & Kernel Compiler Studio")).toBeInTheDocument();

    // Switch to Op Coverage Matrix tab
    const coverageTab = screen.getByRole("button", { name: /Op Coverage Matrix/i });
    fireEvent.click(coverageTab);
    await waitFor(() => {
      expect(screen.getByText("Graph Lowerability & Fallback Analyzer")).toBeInTheDocument();
    });

    // Switch to DataLoader Profiler tab
    const profilerTab = screen.getByRole("button", { name: /DataLoader Profiler/i });
    fireEvent.click(profilerTab);
    await waitFor(() => {
      expect(
        screen.getByText("DataLoader Multi-Worker Memory Replication Profiler")
      ).toBeInTheDocument();
    });

    // Switch to Audit Logs tab
    const auditTab = screen.getByRole("button", { name: /Audit Logs/i });
    fireEvent.click(auditTab);
    await waitFor(() => {
      expect(screen.getByText(/Administrative Privileges/i)).toBeInTheDocument();
    });
  });

  it("displays compiler optimization metrics and fused kernels", async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText(/Optimization Metrics/i)).toBeInTheDocument();
      expect(screen.getByText(/fusion reduction/i)).toBeInTheDocument();
    });
  });
});
