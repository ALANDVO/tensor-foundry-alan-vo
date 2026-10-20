# Changelog

## 1.1.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

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
