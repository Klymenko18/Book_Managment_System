import pytest
from httpx import AsyncClient
from uuid import uuid4

@pytest.mark.integration
async def test_authors_crud(client: AsyncClient, auth_headers):
    name = f"Author_{uuid4().hex[:6]}"
    r_create = await client.post("/api/v1/authors", json={"name": name}, headers=auth_headers)
    assert r_create.status_code in (201, 409)

    if r_create.status_code == 201:
        author_id = r_create.json()["id"]
    else:
        r_list = await client.get("/api/v1/authors", params={"name": name, "limit": 1, "offset": 0})
        assert r_list.status_code == 200
        author_id = r_list.json()["items"][0]["id"]

    r_get = await client.get(f"/api/v1/authors/{author_id}")
    assert r_get.status_code == 200
    assert r_get.json()["name"] == name

    new_name = f"{name}_upd"
    r_update = await client.patch(f"/api/v1/authors/{author_id}", json={"name": new_name}, headers=auth_headers)
    assert r_update.status_code in (200, 204)

    r_after_update = await client.get(f"/api/v1/authors/{author_id}")
    assert r_after_update.status_code == 200
    assert r_after_update.json()["name"] == new_name

    r_list2 = await client.get("/api/v1/authors", params={"name": new_name, "limit": 10, "offset": 0})
    assert r_list2.status_code == 200
    assert any(a["id"] == author_id for a in r_list2.json().get("items", []))

    r_delete = await client.delete(f"/api/v1/authors/{author_id}", headers=auth_headers)
    assert r_delete.status_code in (200, 204)

    r_get_deleted = await client.get(f"/api/v1/authors/{author_id}")
    assert r_get_deleted.status_code in (404, 410)
