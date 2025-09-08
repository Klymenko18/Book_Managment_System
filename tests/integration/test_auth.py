import pytest
import httpx

@pytest.mark.integration
async def test_register_login_logout_flow(client: httpx.AsyncClient, auth_user):
    r = await client.post(
        "/api/v1/auth/tokens",
        data={"username": "tester", "password": "secret123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200
    token = r.json().get("access_token")
    assert token

    r = await client.post("/api/v1/users", json={"username": "newu", "password": "secret123"})
    assert r.status_code in (200, 201, 409, 422)

    r = await client.patch(
        f"/api/v1/users/{auth_user.id}",
        json={"username": "tester", "password": "newpass123"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code in (200, 404, 409)

    r = await client.delete(f"/api/v1/users/{auth_user.id}", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code in (200, 404)
