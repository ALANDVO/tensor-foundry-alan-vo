# Changelog

## 1.3.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.3.0 — 2026-11-05

### Enhanced: tensor-engine-core-ops
- Added `Tensor.transpose(*axes)` with full gradient support for arbitrary dimension permutations
- Added `Tensor.reshape(*shape)` with gradient support for view-based shape changes
- Added `Tensor.__truediv__` and `__rtruediv__` element-wise division with gradient support (scalar and tensor)
- All 30 backend tests passing, manual verification of new operations successful

### Completed: hardware-op-coverage-matrix
- Catalog operators across hardware targets (CPU, MPS 2.6+, Vulkan 1.3, CUDA SM_90)
- Analyze graph lowerability and detect unsupported fallback operators
- Calculate community request triage scores and generate op implementation roadmaps
- Frontend: CoverageMatrixView with filtering, search, and lowerability analyzer

### Completed: dataloader-worker-memory-profiler
- Simulate worker pool memory consumption across fork and spawn IPC regimes
- Detect list copying memory amplification versus zero-copy shared memory tensor buffers
- Provide memory savings reports and batch allocation benchmarks
- Frontend: MemoryProfilerView with simulation controls and results

### Completed: oidc-pkce-auth-and-audit
- Verify JWT tokens with issuer, audience, and role checks (viewer, operator, admin)
- Support local demo authentication with localhost restriction
- Track transactional audit log entries for all mutations with UTC timestamps
- Frontend: AuditLogView with log inspection
- Keycloak realm configuration

### Completed: advisory-llm-diagnostics
- Provide grounded optimization advice based on actual compiled graph metrics
- Support OpenAI-compatible, Anthropic, Gemini, and Ollama adapters
- Maintain zero external network dependencies when LLM_API_KEY is unset

## 1.2.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.1.0 — 2026-10-29

### Completed: tensor-engine-and-graph-compiler
- Dynamic tensor engine with multi-dimensional arrays and reverse-mode autograd DAG
- Computational graph tracing extracting IR nodes and execution dependencies
- Inductor-style fusion passes merging pointwise chains and GEMM+activation sequences
- Multi-target kernel codegen: CPU C/OpenMP, Metal MSL, Vulkan GLSL, CUDA
- Execution metrics profiling: FLOPs, memory footprint, compiled speedup ratio
- 30 backend tests passing (6 tensor + 8 compiler + 16 other features)

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to `tensor-foundry-alan-vo` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-12

### Added
- Initial release of TensorFoundry for Alan Vo (`ALANDVO`).
- Dynamic tensor computation engine supporting multi-dimensional tensors and reverse-mode autograd DAGs.
- TorchInductor-inspired computational graph tracer, fusion optimizer, and multi-backend kernel generator (CPU C/OpenMP, Apple Silicon Metal MSL, Vulkan GLSL, and CUDA).
- Hardware operator coverage matrix and lowerability analyzer addressing PyTorch MPS and Vulkan tracker issues.
- DataLoader worker memory replication profiler and zero-copy IPC optimization validator.
- Enterprise Keycloak OIDC authorization code flow with PKCE, bearer token validation, and role-based access control.
- Provider-agnostic advisory LLM diagnostics supporting OpenAI-compatible, Anthropic, Gemini, and Ollama APIs.
- React 19 + TypeScript + Vite interactive frontend with dashboard tabs for graph compilation, coverage analysis, memory profiling, and audit logs.
- Docker compose orchestration with Keycloak, backend, and frontend containers.
- Complete CI workflow on `ubuntu-latest`.

---

Alan Vo · [alanvo.net](https://alanvo.net)
