# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

tensor-engine-and-graph-compiler

## Roadmap

### tensor-engine-and-graph-compiler — Tensor Dynamic Graph & Inductor Compiler Engine

Status: done

Acceptance:
- Create multi-dimensional tensors with forward and reverse-mode automatic differentiation DAG
- Trace computational graphs and extract Graph IR nodes and execution dependencies
- Execute Inductor compiler fusion passes to merge pointwise activations and linear layers
- Generate multi-target kernel code (C/OpenMP, Metal MSL, Vulkan GLSL, CUDA)
- Profile execution metrics including FLOPs, memory footprint, and compiled speedup ratio

Implementation: `backend/app/services/tensor_engine.py`, `backend/app/services/compiler_engine.py`, `backend/app/api/compiler.py`

Tests: `backend/tests/test_tensor_engine.py`, `backend/tests/test_compiler_engine.py`

### hardware-op-coverage-matrix — Multi-Hardware Operator Coverage & Triage Matrix

Status: planned

Acceptance:
- Catalog operators across hardware targets (CPU, MPS 2.6+, Vulkan 1.3, CUDA SM_90)
- Analyze graph lowerability and detect unsupported fallback operators
- Calculate community request triage scores and generate op implementation roadmaps

Implementation: `backend/app/services/coverage_service.py`, `backend/app/api/coverage.py`

Tests: `backend/tests/test_coverage_service.py`

### dataloader-worker-memory-profiler — DataLoader Multi-Worker Memory Replication Profiler

Status: planned

Acceptance:
- Simulate worker pool memory consumption across fork and spawn IPC regimes
- Detect list copying memory amplification versus zero-copy shared memory tensor buffers
- Provide memory savings reports and batch allocation benchmarks

Implementation: `backend/app/services/profiler_service.py`, `backend/app/api/profiler.py`

Tests: `backend/tests/test_profiler_service.py`

### oidc-pkce-auth-and-audit — Keycloak OIDC PKCE Bearer Authentication & Audit Log

Status: planned

Acceptance:
- Verify JWT tokens with issuer, audience, and role checks (viewer, operator, admin)
- Support local demo authentication with localhost restriction
- Track transactional audit log entries for all mutations with UTC timestamps

Implementation: `backend/app/core/security.py`, `backend/app/api/auth.py`, `backend/app/services/audit_service.py`

Tests: `backend/tests/test_auth.py`, `backend/tests/test_audit.py`

### advisory-llm-diagnostics — Provider-Agnostic Advisory LLM Optimization Engine

Status: planned

Acceptance:
- Provide grounded optimization advice based on actual compiled graph metrics
- Support OpenAI-compatible, Anthropic, Gemini, and Ollama adapters
- Maintain zero external network dependencies when LLM_API_KEY is unset

Implementation: `backend/app/services/llm_advisor.py`, `backend/app/api/advisor.py`

Tests: `backend/tests/test_llm_advisor.py`

