"""Integration tests crossing HTTP boundary, auth guards, OIDC PKCE flow, and API workflows."""

import pytest


def test_unauthenticated_request_rejected(client):
    """Protected endpoints must return 401 Unauthorized when missing Authorization header."""
    resp = client.get("/api/v1/compiler/graphs")
    assert resp.status_code == 401
    assert "Missing Authorization header" in resp.json()["detail"]


def test_role_authorization_denial(client, viewer_token):
    """Viewers must be denied when attempting operator or admin mutations (403 Forbidden)."""
    headers = {"Authorization": f"Bearer {viewer_token}"}
    create_payload = {
        "name": "Unauthorized Test Graph",
        "target_backend": "cpu",
        "architecture_preset": "mlp"
    }
    resp = client.post("/api/v1/compiler/trace", json=create_payload, headers=headers)
    assert resp.status_code == 403
    assert "Forbidden" in resp.json()["detail"]


def test_demo_login_and_token_exchange(client):
    """Verify local demo login endpoint produces valid token with requested role."""
    resp = client.post(
        "/api/v1/auth/demo-login",
        json={"username": "test_engineer", "requested_role": "operator"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "Bearer"
    assert "operator" in data["user"]["roles"]


def test_pkce_token_exchange_rejection_on_invalid_verifier(client):
    """PKCE token exchange must reject malformed or short code_verifiers."""
    resp = client.post(
        "/api/v1/auth/token",
        json={
            "grant_type": "authorization_code",
            "code": "sample_auth_code_123",
            "code_verifier": "short",  # Invalid PKCE verifier length
            "redirect_uri": "http://127.0.0.1:5173/callback"
        }
    )
    assert resp.status_code == 400
    assert "Invalid PKCE code_verifier" in resp.json()["detail"]


def test_pkce_valid_exchange_and_propagation(client):
    """Complete PKCE token exchange and propagate bearer token into authorized API call."""
    # 1. Exchange valid PKCE parameters
    exchange_resp = client.post(
        "/api/v1/auth/token",
        json={
            "grant_type": "authorization_code",
            "code": "valid_pkce_auth_code",
            "code_verifier": "a_valid_high_entropy_code_verifier_string_43_chars_long",
            "redirect_uri": "http://127.0.0.1:5173/callback"
        }
    )
    assert exchange_resp.status_code == 200
    token = exchange_resp.json()["access_token"]

    # 2. Propagate token into authenticated user profile endpoint
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "alanvo@gmail.com"


def test_core_compiler_create_read_workflow(client, operator_token):
    """Test full HTTP boundary workflow: create/trace computational graph, then read it back."""
    headers = {"Authorization": f"Bearer {operator_token}"}

    create_payload = {
        "name": "Integration MLP Graph",
        "description": "Testing create-read HTTP cycle",
        "target_backend": "mps",
        "architecture_preset": "mlp"
    }

    # 1. POST /compiler/trace
    create_resp = client.post("/api/v1/compiler/trace", json=create_payload, headers=headers)
    assert create_resp.status_code == 200
    created_data = create_resp.json()
    graph_id = created_data["id"]
    assert len(created_data["compiled_kernels"]) > 0
    assert created_data["metrics"]["speedup_percentage"] > 0

    # 2. GET /compiler/graphs/{id}
    read_resp = client.get(f"/api/v1/compiler/graphs/{graph_id}", headers=headers)
    assert read_resp.status_code == 200
    read_data = read_resp.json()
    assert read_data["id"] == graph_id
    assert read_data["name"] == "Integration MLP Graph"

    # 3. GET /compiler/graphs listing
    list_resp = client.get("/api/v1/compiler/graphs", headers=headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1


def test_admin_audit_log_inspection(client, admin_token):
    """Admin role can query audit logs containing recorded operations."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = client.get("/api/v1/audit/logs", headers=headers)
    assert resp.status_code == 200
    logs = resp.json()
    assert isinstance(logs, list)
