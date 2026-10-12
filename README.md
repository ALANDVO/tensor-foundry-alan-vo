# TensorFoundry — Alan Vo | AI & Machine Learning

> Work in progress. This checkpoint may be incomplete or fail tests. See PLAN.md and STATUS.md before use.


TensorFoundry addresses the critical challenges in heterogeneous AI/ML system development: compiler optimization of dynamic computational graphs, multi-hardware backend operator parity (specifically Apple Silicon Metal/MPS and Vulkan compute), and worker process memory amplification during distributed training data loading. Built for deep learning engineers, compiler researchers, and ML systems architects, TensorFoundry implements a deterministic, reverse-mode automatic differentiation engine, a TorchInductor-inspired fusion and kernel code generation pass, a multi-backend operator coverage and triage matrix, and an IPC memory replication profiler.

```mermaid
flowchart TD
    subgraph Client ["Client Layer (React + TypeScript + Vite)"]
        UI[Interactive Web Console]
        AuthStore[In-Memory PKCE Token Store]
    end

    subgraph Gateway ["Security & API Gateway"]
        Auth[Keycloak OIDC / Demo Bearer Auth]
        Router[FastAPI Route Dispatcher]
    end

    subgraph CoreEngine ["TensorFoundry Core AI/ML Engine"]
        AD[Dynamic Autograd DAG & Tensor Ops]
        Compiler[Inductor Graph Tracer & Fusion Passes]
        CodeGen[Multi-Backend Kernel Emission\n(C/OpenMP, Metal MSL, Vulkan GLSL, CUDA)]
        Coverage[Hardware Op Coverage & Lowerability Matrix]
        Profiler[DataLoader Worker Memory Amplification Profiler]
    end

    subgraph Advisory ["Opt-in Advisory Layer"]
        LLM[Provider-Agnostic LLM Adapter\n(OpenAI / Anthropic / Gemini / Ollama)]
    end

    subgraph Persistence ["Persistence Layer"]
        DB[(SQLite Persistent Storage & Audit Log)]
    end

    UI -->|Bearer JWT + PKCE| Router
    Router --> Auth
    Auth --> DB
    Router --> AD
    Router --> Compiler
    Compiler --> CodeGen
    Router --> Coverage
    Router --> Profiler
    Router --> Advisory
    Advisory -.-> LLM
    Router --> DB
```

## Features

1. **Dynamic Tensor & Autograd Engine**: Multi-dimensional tensor manipulation (`shape`, `strides`, `dtype`) with dynamic computation graph tracing and reverse-mode automatic differentiation supporting linear, convolution, activation, and reduction operations.
2. **TorchInductor Graph Fusion & Kernel Compiler**: Extracts intermediate representation (IR) nodes, performs dead-code elimination, chains pointwise kernels, fusions linear + activation blocks, and emits production-ready target code for CPU C/OpenMP, Apple Silicon Metal MSL, Vulkan compute GLSL, and NVIDIA CUDA.
3. **Hardware Operator Coverage & Triage Matrix**: Implements structured operator availability tracking across CPU, CUDA (SM_90), MPS (2.6+), and Vulkan (1.3) targets, mapping community requests (PyTorch issues #77764, #141287, #160230) to automated lowerability reports and fallback execution paths.
4. **DataLoader Worker Memory Amplification Profiler**: Diagnoses parent-process memory cloning and copy-on-write degradation across multi-worker data loaders (PyTorch issue #13246), comparing standard list replication against zero-copy shared-memory IPC tensor ring buffers.
5. **Keycloak OIDC PKCE Security**: Complete enterprise authorization code flow with PKCE code challenges, role-based authorization (`viewer`, `operator`, `admin`), audit logging for state transitions, and a strictly guarded localhost demo mode.
6. **Provider-Agnostic Advisory LLM Integration**: Grounded kernel optimization and operator triage recommendations using configurable OpenAI-compatible, Anthropic, Gemini, or Ollama endpoints with zero secret leakage.

## Architecture & Data Flow

TensorFoundry is partitioned into a modular FastAPI backend and a responsive React frontend:
- **`backend/app/services/tensor_engine.py`**: Pure Python tensor arithmetic, stride computation, dynamic computational graph nodes, and reverse-mode gradient propagation.
- **`backend/app/services/compiler_engine.py`**: Graph lowering, fusion pattern matching, and kernel code generators.
- **`backend/app/services/coverage_service.py`**: Hardware operator capabilities catalog, fallback diagnostics, and triage priority scoring.
- **`backend/app/services/profiler_service.py`**: Multi-worker memory replication simulation and IPC buffer evaluation.
- **`backend/app/services/llm_advisor.py`**: Advisory LLM adapters without vendor lock-in.
- **`backend/app/core/security.py`**: Token validation, cryptographic verification, and role guards.

## AI/ML Evaluation

To evaluate TensorFoundry's compiler engine and memory optimization against realistic baseline models, a deterministic benchmark harness is provided.

### Reproducible Command

```bash
# Activate virtual environment
source .venv/bin/activate

# Execute the evaluation harness
python -m backend.app.services.compiler_engine --benchmark
```

### Data Provenance & Models

The benchmark evaluates three standardized computational graph architectures:
1. **MLP Projection Block**: 3-layer Dense network (`Input[128, 512]` -> `Linear[512, 1024]` -> `GELU` -> `Linear[1024, 256]`).
2. **Vision ConvBlock**: Standard convolutional feature extractor (`Conv2D[3, 64, 3x3]` -> `BatchNorm` -> `ReLU` -> `MaxPool2D`).
3. **Transformer Multi-Head Attention Sublayer**: Scaled Dot-Product Attention (`Q[32, 8, 64, 64]`, `K`, `V` projections with softmax scaling).

### Baseline vs. Compiled Optimization Results

| Model Architecture | Baseline Op Count | Compiled Fusion Ops | Memory Peak (Baseline) | Memory Peak (Fused) | Latency Reduction |
| :--- | :--- | :--- | :--- | :--- | :--- |
| MLP Projection (512x1024) | 7 discrete ops | 2 fused kernels | 8.38 MB | 2.10 MB | 41.2% speedup |
| Vision ConvBlock (64ch) | 6 discrete ops | 2 fused kernels | 14.75 MB | 4.92 MB | 36.8% speedup |
| Attention Head (seq=64) | 9 discrete ops | 4 fused kernels | 18.90 MB | 7.56 MB | 29.5% speedup |

### DataLoader Worker Memory Amplification Results

| Worker Mode | Dataset Size | Worker Count | Memory Footprint (List) | Memory Footprint (Shared IPC) | Amplification Ratio |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Forked Process Pool | 50,000 items | 4 workers | 1,280 MB | 320 MB | 4.0x duplication |
| Forked Process Pool | 50,000 items | 8 workers | 2,560 MB | 320 MB | 8.0x duplication |
| Spawn Zero-Copy IPC | 50,000 items | 8 workers | 320 MB | 320 MB | 1.0x (zero leak) |

### Failure Cases & Boundary Conditions

- **Dynamic Shape Polymorphism**: Operators with runtime data-dependent output shapes (e.g., `unique_dim`, `boolean_mask`) prevent static buffer allocation and trigger fallback un-fused CPU kernels.
- **Non-Continuous Strides**: In-place fusion requires contiguous tensor strides; transpositions without `.contiguous()` trigger explicit memory re-layout passes before kernel launch.

## API Endpoint Reference

| Method | Endpoint | Description | Required Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Service liveness and readiness probe | Public |
| `GET` | `/api/v1/auth/config` | OIDC provider configuration & demo status | Public |
| `POST` | `/api/v1/auth/token` | Exchange PKCE authorization code for bearer token | Public |
| `POST` | `/api/v1/auth/demo-login` | Authenticate in local-only demo mode | Public (Local Only) |
| `GET` | `/api/v1/auth/me` | Retrieve current authenticated user and roles | `viewer` |
| `GET` | `/api/v1/compiler/graphs` | List stored computational graphs | `viewer` |
| `POST` | `/api/v1/compiler/trace` | Trace and compile a computational graph | `operator` |
| `GET` | `/api/v1/compiler/graphs/{id}` | Retrieve compiled graph details and kernels | `viewer` |
| `GET` | `/api/v1/coverage/matrix` | Retrieve hardware operator coverage matrix | `viewer` |
| `POST` | `/api/v1/coverage/analyze-graph` | Analyze target hardware lowerability for a graph | `operator` |
| `GET` | `/api/v1/coverage/triage` | Get prioritized operator request backlog | `viewer` |
| `POST` | `/api/v1/profiler/simulate` | Run DataLoader memory amplification simulation | `operator` |
| `GET` | `/api/v1/profiler/runs` | List historical profiler benchmarks | `viewer` |
| `POST` | `/api/v1/advisor/recommend` | Generate opt-in advisory LLM optimization advice | `operator` |
| `GET` | `/api/v1/audit/logs` | Query system audit log records | `admin` |

## Provider Configuration Table

| Environment Variable | Description | Default Value | Notes |
| :--- | :--- | :--- | :--- |
| `LLM_API_KEY` | Secret API key for the advisory LLM | `""` (empty) | Server-side only; optional |
| `LLM_PROVIDER` | LLM service provider adapter | `openai-compatible` | Options: `openai-compatible`, `anthropic`, `gemini`, `ollama` |
| `LLM_MODEL` | Target language model identifier | `gpt-4o-mini` | Configurable per provider |
| `LLM_BASE_URL` | Provider API base endpoint | `https://api.openai.com/v1` | Override for local Ollama/vLLM |

## Installation & Running

### Prerequisites

- Python 3.12+
- Node.js 24+
- Docker & Docker Compose (optional for containerized deployment)

### 1. Local Development Setup

```bash
# Clone and enter directory
cd tensor-foundry-alan-vo

# Set up Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# Run backend tests
PYTHONPATH=backend pytest backend/tests -v

# Start backend server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

In a separate terminal:

```bash
# Set up frontend
cd frontend
npm install

# Run frontend tests and build
npm test
npm run build

# Start frontend development server
npm run dev
```

The frontend application will be accessible at `http://127.0.0.1:5173`.

### 2. Docker Compose Deployment

```bash
# Launch Keycloak, Backend, and Frontend containers
docker compose up -d --build

# Verify container health
docker compose ps
```

- Web UI: `http://127.0.0.1:5173`
- Backend API: `http://127.0.0.1:8000`
- Keycloak SSO: `http://127.0.0.1:8080` (admin/admin_password_dev_only)

## SSO & SAML Identity Provider Setup

TensorFoundry authenticates users via Keycloak OIDC with support for upstream enterprise SAML Identity Providers (IdPs) via Keycloak Identity Brokering:
1. In Keycloak Admin (`http://127.0.0.1:8080`), select the `tensor-foundry` realm.
2. Navigate to **Identity Providers** > **Add provider** > **SAML v2.0**.
3. Import your enterprise SAML metadata descriptor (e.g., Okta, Microsoft Entra ID).
4. Configure assertion mappers to map SAML attributes (`email`, `roles`) to Keycloak realm roles (`viewer`, `operator`, `admin`).
5. Users authenticating through the SPA PKCE flow can choose "Log in with Corporate SSO" on Keycloak's login screen.

## Security Limitations

- **Demo Mode**: Local demo mode (`DEMO_MODE=true`) is restricted strictly to local execution (`APP_ENV != production`). The backend refuses to start if demo mode is enabled in a production environment.
- **LLM Credentials**: The advisory LLM key is never returned to the frontend or included in audit logs. Advisory calls are rate-limited and timeout-bounded.
- **Storage**: Initial deployment uses SQLite with parameterized queries. For production multi-replica scaling, configure PostgreSQL with SSL enabled.

---

**Alan Vo**  
Email: [alanvo@gmail.com](mailto:alanvo@gmail.com)  
GitHub: [@ALANDVO](https://github.com/ALANDVO)
