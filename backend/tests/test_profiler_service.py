"""Tests for DataLoader memory replication profiler (PyTorch #13246)."""

import pytest
from app.schemas.domain import ProfilerSimulateRequest
from app.services.profiler_service import ProfilerService


def test_profiler_simulation_fork_python_list(db_session):
    svc = ProfilerService(db_session)
    req = ProfilerSimulateRequest(
        title="Python List Test",
        sample_count=20000,
        worker_count=4,
        ipc_mode="fork_python_list"
    )
    run = svc.run_simulation(req, user_email="operator@test.local")

    assert run.amplification_ratio > 3.0
    assert run.zero_copy_verified is False
    assert run.worker_memory_mb > run.parent_memory_mb


def test_profiler_simulation_spawn_shared_ipc(db_session):
    svc = ProfilerService(db_session)
    req = ProfilerSimulateRequest(
        title="Shared IPC Test",
        sample_count=20000,
        worker_count=4,
        ipc_mode="spawn_shared_ipc"
    )
    run = svc.run_simulation(req, user_email="operator@test.local")

    assert run.amplification_ratio == 1.0
    assert run.zero_copy_verified is True
    assert run.worker_memory_mb < run.parent_memory_mb


def test_profiler_list_and_get(db_session):
    svc = ProfilerService(db_session)
    req = ProfilerSimulateRequest(worker_count=2, ipc_mode="fork_numpy_array")
    run = svc.run_simulation(req)

    fetched = svc.get_run(run.id)
    assert fetched is not None
    assert fetched.id == run.id

    all_runs = svc.list_runs()
    assert len(all_runs) >= 1
