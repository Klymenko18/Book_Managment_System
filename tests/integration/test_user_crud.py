import pytest
from httpx import AsyncClient
from uuid import uuid4

def _items(resp_json):
    return resp_json["items"] if isinstance(resp_json, dict) and "items" in resp_json else resp_json

@pytest.mark.integration
async def test_users_crud(client: AsyncClient, auth_headers):
    username = f"user_{uuid4().hex[:6]}"
    password = "TestPass123!"

    r_create = await client.post(
        "/api/v1/users",
        json={"username": username, "password": password},
        headers=auth_headers,
    )
    assert r_create.status_code in (200, 201, 409)

    if r_create.status_code in (200, 201):
        user_id = r_create.json().get("id")
        if not user_id:
            r_list = await client.get("/api/v1/users", params={"username": username, "limit": 1, "offset": 0})
            assert r_list.status_code == 200
            items = _items(r_list.json())
            assert items
            user_id = items[0]["id"]
    else:
        r_list = await client.get("/api/v1/users", params={"username": username, "limit": 1, "offset": 0})
        assert r_list.status_code == 200
        items = _items(r_list.json())
        assert items
        user_id = items[0]["id"]

    r_get = await client.get(f"/api/v1/users/{user_id}")
    assert r_get.status_code == 200
    assert r_get.json().get("username") == username

    new_username = f"{username}_upd"
    r_update = await client.patch(
        f"/api/v1/users/{user_id}",
        json={"username": new_username, "password": password},
        headers=auth_headers,
    )
    assert r_update.status_code in (200, 204)

    r_after_update = await client.get(f"/api/v1/users/{user_id}")
    assert r_after_update.status_code == 200
    assert r_after_update.json().get("username") == new_username

    r_list2 = await client.get("/api/v1/users", params={"username": new_username, "limit": 10, "offset": 0})
    assert r_list2.status_code == 200
    items2 = _items(r_list2.json())
    assert any(u["id"] == user_id for u in items2)

    r_delete = await client.delete(f"/api/v1/users/{user_id}", headers=auth_headers)
    assert r_delete.status_code in (200, 204, 404, 410)

    r_get_deleted = await client.get(f"/api/v1/users/{user_id}")
    assert r_get_deleted.status_code in (404, 410)
