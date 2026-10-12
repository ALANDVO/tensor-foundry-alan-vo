"""Tests for advisory LLM engine and provider adapters with mocked networking."""

import pytest
from app.schemas.domain import AdvisorRequest
from app.services.llm_advisor import LLMAdvisorService


@pytest.mark.asyncio
async def test_deterministic_offline_advisor_when_no_key():
    """Service returns deterministic rule-based advice when no API key is provided."""
    svc = LLMAdvisorService()
    svc.api_key = None  # Ensure key is blank

    req = AdvisorRequest(
        target_backend="mps",
        focus_area="fusion_and_memory"
    )
    grounded = {
        "speedup_percentage": 42.5,
        "reduction_ratio": 1.3
    }

    resp = await svc.generate_advice(req, grounded_data=grounded)
    assert resp.status == "DETERMINISTIC_OFFLINE"
    assert resp.provider == "deterministic-offline-engine"
    assert len(resp.recommendations) >= 3
    assert "MPS" in resp.analysis


@pytest.mark.asyncio
async def test_mocked_llm_provider_network_adapter(monkeypatch):
    """External LLM calls are mocked and never access external network."""
    svc = LLMAdvisorService()
    # Generate synthetic key at runtime: provider prefix plus repeated character (no credential literals)
    synthetic_key = "testprovider_" + ("0" * 32)
    svc.api_key = synthetic_key
    svc.provider = "openai-compatible"

    # Mock _call_openai
    async def mock_call_openai(prompt):
        return (
            "Mocked analysis: Recommend enabling in-place buffer recycling.",
            ["Add contiguous check", "Enable SIMD alignment", "Verify kernel dispatch bounds"]
        )

    monkeypatch.setattr(svc, "_call_openai", mock_call_openai)

    req = AdvisorRequest(target_backend="cuda", focus_area="fusion_and_memory")
    resp = await svc.generate_advice(req, grounded_data={"test": 1})

    assert resp.status == "ADVISORY_GROUNDED"
    assert "Mocked analysis" in resp.analysis
    assert len(resp.recommendations) == 3


@pytest.mark.asyncio
async def test_error_redaction_with_synthetic_key(monkeypatch):
    """Verify provider error handles failure safely and falls back without leaking key."""
    svc = LLMAdvisorService()
    synthetic_key = "synthetic_key_" + ("a" * 24)
    svc.api_key = synthetic_key
    svc.provider = "openai-compatible"

    async def mock_failing_call(prompt):
        raise RuntimeError(f"Connection timeout to upstream provider with auth {synthetic_key}")

    monkeypatch.setattr(svc, "_call_openai", mock_failing_call)

    req = AdvisorRequest(target_backend="cpu", focus_area="data_loading")
    resp = await svc.generate_advice(req, grounded_data={"amplification_ratio": 4.0})

    assert "deterministic" in resp.analysis.lower()
    assert synthetic_key not in resp.analysis
