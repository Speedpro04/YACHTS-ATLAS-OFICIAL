import os

from fastapi.testclient import TestClient

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")

from app.main import app


client = TestClient(app)

PROTECTED_GET = [
    "/api/v1/ativos",
    "/api/v1/ativos/YA-TEST-2024-ABCD",
    "/api/v1/documentos/ativo/YA-TEST-2024-ABCD",
    "/api/v1/leads/marina",
    "/api/v1/alertas/alertas/configurar",
    "/api/v1/alertas/alertas/verificar",
    "/api/v1/brokers/brokers",
    "/api/v1/brokers/brokers/user/some-user-id",
    "/api/v1/insurance/companies",
    "/api/v1/admin/maintenance/status",
    "/api/v1/registros/YA-TEST-2024-ABCD",
    "/api/v1/auth/me",
    "/api/v1/payments/subscription/sub_123/status",
]

PROTECTED_POST = [
    "/api/v1/alertas/alertas/enviar",
    "/api/v1/alertas/alertas/testar",
    "/api/v1/owner/secret",
    "/api/v1/payments/subscription/sub_123/cancel",
    "/api/v1/auth/logout",
]


def test_protected_get_endpoints_require_auth():
    for path in PROTECTED_GET:
        response = client.get(path)
        assert response.status_code == 401, f"{path} respondeu {response.status_code} sem token"


def test_protected_post_endpoints_require_auth():
    for path in PROTECTED_POST:
        response = client.post(path, json={})
        assert response.status_code == 401, f"{path} respondeu {response.status_code} sem token"


def test_invalid_bearer_token_rejected():
    response = client.get(
        "/api/v1/ativos",
        headers={"Authorization": "Bearer token-invalido"},
    )
    assert response.status_code == 401


def test_public_endpoints_still_open():
    # Health e plans são públicos por design
    assert client.get("/health").status_code == 200
    assert client.get("/api/v1/payments/plans").status_code == 200
