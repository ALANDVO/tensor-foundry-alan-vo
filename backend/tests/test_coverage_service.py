"""Tests for hardware operator coverage and lowerability matrix."""

import pytest
from app.services.coverage_service import CoverageService


def test_catalog_seeding_and_listing(db_session):
    svc = CoverageService(db_session)
    count = svc.seed_initial_catalog()
    assert count >= 10

    ops = svc.list_operators()
    assert len(ops) >= count

    # Filter by category
    linalg_ops = svc.list_operators(category="linalg")
    assert len(linalg_ops) >= 2


def test_graph_lowerability_analysis(db_session):
    svc = CoverageService(db_session)
    svc.seed_initial_catalog()

    # Graph with supported ops
    resp_supported = svc.analyze_graph_lowerability(
        operator_list=["matmul", "relu", "gelu"],
        target_backend="mps"
    )
    assert resp_supported.can_execute_zero_fallback is True
    assert resp_supported.fallback_transfers_required == 0
    assert resp_supported.lowerability_percentage == 100.0

    # Graph with unsupported op on Vulkan
    resp_vulkan = svc.analyze_graph_lowerability(
        operator_list=["matmul", "linalg_solve_ex", "unique_dim"],
        target_backend="vulkan"
    )
    assert resp_vulkan.can_execute_zero_fallback is False
    assert len(resp_vulkan.unsupported_operators) >= 1
    assert resp_vulkan.fallback_transfers_required > 0


def test_triage_rankings(db_session):
    svc = CoverageService(db_session)
    svc.seed_initial_catalog()

    rankings = svc.get_triage_rankings()
    assert len(rankings) > 0
    # Items should be sorted descending by priority score
    scores = [r.priority_score for r in rankings]
    assert scores == sorted(scores, reverse=True)
