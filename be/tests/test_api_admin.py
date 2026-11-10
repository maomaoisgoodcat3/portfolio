import re
import uuid

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.main import app


def test_all_admin_routes_return_401_without_override(client: TestClient) -> None:
    # Walk all routes registered in app
    for route in app.routes:
        if isinstance(route, APIRoute) and route.path.startswith("/api/admin"):
            for method in route.methods:
                if method in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                    # Replace path parameters like {id} or {block_id} with a dummy UUID
                    dummy_id = str(uuid.uuid4())
                    resolved_path = re.sub(r"\{[^}]+\}", dummy_id, route.path)
                    res = client.request(
                        method, resolved_path, json={} if method in {"POST", "PUT", "PATCH"} else None
                    )
                    assert res.status_code == 401, (
                        f"Expected 401 for {method} {resolved_path}, got {res.status_code}"
                    )


def test_admin_create_block_auto_position(admin_client: TestClient) -> None:
    res1 = admin_client.post(
        "/api/admin/blocks",
        json={"type": "profile", "title": "Profile", "visibility": "public"},
    )
    assert res1.status_code == 201
    b1 = res1.json()
    assert b1["position"] == 0
    assert b1["type"] == "profile"
    assert b1["title"] == "Profile"

    res2 = admin_client.post(
        "/api/admin/blocks",
        json={"type": "about", "title": "About Me"},
    )
    assert res2.status_code == 201
    b2 = res2.json()
    assert b2["position"] == 1
    assert b2["visibility"] == "admin"


def test_admin_create_second_profile_returns_409(admin_client: TestClient) -> None:
    first = admin_client.post(
        "/api/admin/blocks",
        json={"type": "profile", "title": "Profile"},
    )
    assert first.status_code == 201

    second = admin_client.post(
        "/api/admin/blocks",
        json={"type": "profile", "title": "Another profile"},
    )
    assert second.status_code == 409
    assert second.json() == {"detail": "Only one profile block is allowed"}


def test_admin_create_second_links_succeeds(admin_client: TestClient) -> None:
    first = admin_client.post(
        "/api/admin/blocks",
        json={"type": "links", "title": "Links"},
    )
    assert first.status_code == 201

    second = admin_client.post(
        "/api/admin/blocks",
        json={"type": "links", "title": "More links"},
    )
    assert second.status_code == 201


def test_admin_create_second_contact_succeeds(admin_client: TestClient) -> None:
    first = admin_client.post(
        "/api/admin/blocks",
        json={"type": "contact", "title": "Contact"},
    )
    assert first.status_code == 201

    second = admin_client.post(
        "/api/admin/blocks",
        json={"type": "contact", "title": "More contact"},
    )
    assert second.status_code == 201


def test_admin_create_two_projects_blocks_allowed(admin_client: TestClient) -> None:
    first = admin_client.post(
        "/api/admin/blocks",
        json={"type": "projects", "title": "Projects"},
    )
    second = admin_client.post(
        "/api/admin/blocks",
        json={"type": "projects", "title": "More projects"},
    )
    assert first.status_code == 201
    assert second.status_code == 201


def test_admin_create_block_validation_errors(admin_client: TestClient) -> None:
    # Invalid block type
    res = admin_client.post(
        "/api/admin/blocks",
        json={"type": "invalid_type", "title": "Title"},
    )
    assert res.status_code == 422

    # Empty title
    res = admin_client.post(
        "/api/admin/blocks",
        json={"type": "skills", "title": ""},
    )
    assert res.status_code == 422

    # Title exceeding 200 chars
    res = admin_client.post(
        "/api/admin/blocks",
        json={"type": "skills", "title": "a" * 201},
    )
    assert res.status_code == 422


def test_admin_get_and_patch_block(admin_client: TestClient) -> None:
    res = admin_client.post(
        "/api/admin/blocks",
        json={"type": "experience", "title": "Exp", "props": {"company": "Acme"}},
    )
    assert res.status_code == 201
    block_id = res.json()["id"]

    # Get block
    get_res = admin_client.get(f"/api/admin/blocks/{block_id}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Exp"

    # Patch block
    patch_res = admin_client.patch(
        f"/api/admin/blocks/{block_id}",
        json={"title": "Updated Exp", "visibility": "public", "props": {"company": "Corp"}},
    )
    assert patch_res.status_code == 200
    patched = patch_res.json()
    assert patched["title"] == "Updated Exp"
    assert patched["visibility"] == "public"
    assert patched["props"] == {"company": "Corp"}


def test_admin_patch_block_cannot_change_type(admin_client: TestClient) -> None:
    res = admin_client.post(
        "/api/admin/blocks",
        json={"type": "projects", "title": "Projects"},
    )
    block_id = res.json()["id"]

    # Attempting to change type should be ignored
    patch_res = admin_client.patch(
        f"/api/admin/blocks/{block_id}",
        json={"type": "skills", "title": "New Title"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["type"] == "projects"
    assert patch_res.json()["title"] == "New Title"


def test_admin_delete_block_cascade(admin_client: TestClient) -> None:
    res = admin_client.post(
        "/api/admin/blocks",
        json={"type": "research", "title": "Research"},
    )
    block_id = res.json()["id"]

    item_res = admin_client.post(
        f"/api/admin/blocks/{block_id}/items",
        json={"data": {"paper": "Paper 1"}},
    )
    assert item_res.status_code == 201
    item_id = item_res.json()["id"]

    # Delete block
    del_res = admin_client.delete(f"/api/admin/blocks/{block_id}")
    assert del_res.status_code == 204

    # Getting deleted block should return 404
    assert admin_client.get(f"/api/admin/blocks/{block_id}").status_code == 404

    # The item should also be deleted (cascade)
    assert admin_client.patch(f"/api/admin/items/{item_id}", json={}).status_code == 404


def test_admin_reorder_blocks_success(admin_client: TestClient) -> None:
    b1 = admin_client.post("/api/admin/blocks", json={"type": "profile", "title": "B1"}).json()
    b2 = admin_client.post("/api/admin/blocks", json={"type": "about", "title": "B2"}).json()
    b3 = admin_client.post("/api/admin/blocks", json={"type": "contact", "title": "B3"}).json()

    # Reorder to [B3, B1, B2]
    new_order = [b3["id"], b1["id"], b2["id"]]
    reorder_res = admin_client.put("/api/admin/blocks/order", json=new_order)
    assert reorder_res.status_code == 200
    data = reorder_res.json()

    positions = {b["id"]: b["position"] for b in data}
    assert positions[b3["id"]] == 0
    assert positions[b1["id"]] == 1
    assert positions[b2["id"]] == 2


def test_admin_reorder_blocks_missing_or_duplicate_ids_returns_422(
    admin_client: TestClient,
) -> None:
    b1 = admin_client.post("/api/admin/blocks", json={"type": "profile", "title": "B1"}).json()
    b2 = admin_client.post("/api/admin/blocks", json={"type": "about", "title": "B2"}).json()

    # Missing b2
    res_missing = admin_client.put("/api/admin/blocks/order", json=[b1["id"]])
    assert res_missing.status_code == 422

    # Duplicate b1
    res_dup = admin_client.put("/api/admin/blocks/order", json=[b1["id"], b1["id"]])
    assert res_dup.status_code == 422

    # Non-existent ID
    random_id = str(uuid.uuid4())
    res_extra = admin_client.put(
        "/api/admin/blocks/order", json=[b1["id"], b2["id"], random_id]
    )
    assert res_extra.status_code == 422


def test_admin_create_item_auto_position_within_block(
    admin_client: TestClient,
) -> None:
    b = admin_client.post("/api/admin/blocks", json={"type": "skills", "title": "Skills"}).json()
    block_id = b["id"]

    res1 = admin_client.post(
        f"/api/admin/blocks/{block_id}/items",
        json={"data": {"skill": "Rust"}},
    )
    assert res1.status_code == 201
    assert res1.json()["position"] == 0

    res2 = admin_client.post(
        f"/api/admin/blocks/{block_id}/items",
        json={"data": {"skill": "Go"}},
    )
    assert res2.status_code == 201
    assert res2.json()["position"] == 1


def test_admin_stats_item_valid_github(admin_client: TestClient) -> None:
    b = admin_client.post("/api/admin/blocks", json={"type": "stats", "title": "Stats"}).json()
    block_id = b["id"]

    res = admin_client.post(
        f"/api/admin/blocks/{block_id}/items",
        json={
            "data": {
                "provider": "github",
                "account": "octocat",
                "show": ["repos", "stars"],
            }
        },
    )
    assert res.status_code == 201
    assert res.json()["data"]["provider"] == "github"
    assert res.json()["data"]["account"] == "octocat"


def test_admin_stats_item_invalid_provider_returns_422(
    admin_client: TestClient,
) -> None:
    b = admin_client.post("/api/admin/blocks", json={"type": "stats", "title": "Stats"}).json()
    block_id = b["id"]

    # Unsupported provider
    res_wrong_provider = admin_client.post(
        f"/api/admin/blocks/{block_id}/items",
        json={"data": {"provider": "leetcode", "account": "octocat"}},
    )
    assert res_wrong_provider.status_code == 422

    # Missing account
    res_missing_account = admin_client.post(
        f"/api/admin/blocks/{block_id}/items",
        json={"data": {"provider": "github", "account": ""}},
    )
    assert res_missing_account.status_code == 422

    # Without provider
    res_no_provider = admin_client.post(
        f"/api/admin/blocks/{block_id}/items",
        json={"data": {"account": "octocat"}},
    )
    assert res_no_provider.status_code == 422

    # With extra key
    res_extra_key = admin_client.post(
        f"/api/admin/blocks/{block_id}/items",
        json={"data": {"provider": "github", "account": "octocat", "extra_key": "bad"}},
    )
    assert res_extra_key.status_code == 422


def test_admin_stats_item_patch_validation(admin_client: TestClient) -> None:
    b = admin_client.post("/api/admin/blocks", json={"type": "stats", "title": "Stats"}).json()
    item = admin_client.post(
        f"/api/admin/blocks/{b['id']}/items",
        json={"data": {"provider": "github", "account": "octocat"}},
    ).json()

    # Patch with invalid provider
    res_bad = admin_client.patch(
        f"/api/admin/items/{item['id']}",
        json={"data": {"provider": "gitlab", "account": "octocat"}},
    )
    assert res_bad.status_code == 422

    # Patch with valid github data
    res_good = admin_client.patch(
        f"/api/admin/items/{item['id']}",
        json={"data": {"provider": "github", "account": "octocat2", "show": ["commits"]}},
    )
    assert res_good.status_code == 200
    assert res_good.json()["data"]["account"] == "octocat2"


def test_admin_patch_and_delete_item(admin_client: TestClient) -> None:
    b = admin_client.post("/api/admin/blocks", json={"type": "links", "title": "Links"}).json()
    item = admin_client.post(
        f"/api/admin/blocks/{b['id']}/items",
        json={"data": {"url": "https://example.com"}},
    ).json()

    # Patch item
    patch_res = admin_client.patch(
        f"/api/admin/items/{item['id']}",
        json={"visibility": "public", "position": 5},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["visibility"] == "public"
    assert patch_res.json()["position"] == 5

    # Delete item
    del_res = admin_client.delete(f"/api/admin/items/{item['id']}")
    assert del_res.status_code == 204

    # Getting deleted item returns 404
    assert admin_client.patch(f"/api/admin/items/{item['id']}", json={}).status_code == 404


def test_admin_props_exceeding_32kb_returns_422(admin_client: TestClient) -> None:
    large_props = {"huge": "x" * 33000}
    res_post = admin_client.post(
        "/api/admin/blocks",
        json={"type": "profile", "title": "Large Block", "props": large_props},
    )
    assert res_post.status_code == 422

    # Create normal block, then attempt patch with >32 KB props
    b = admin_client.post(
        "/api/admin/blocks",
        json={"type": "profile", "title": "Normal Block"},
    ).json()
    res_patch = admin_client.patch(
        f"/api/admin/blocks/{b['id']}",
        json={"props": large_props},
    )
    assert res_patch.status_code == 422


def test_admin_item_data_exceeding_32kb_returns_422(
    admin_client: TestClient,
) -> None:
    b = admin_client.post("/api/admin/blocks", json={"type": "links", "title": "Links"}).json()
    large_data = {"huge": "x" * 33000}

    res_post = admin_client.post(
        f"/api/admin/blocks/{b['id']}/items",
        json={"data": large_data},
    )
    assert res_post.status_code == 422

    # Create normal item, then attempt patch with >32 KB data
    item = admin_client.post(
        f"/api/admin/blocks/{b['id']}/items",
        json={"data": {"url": "https://example.com"}},
    ).json()
    res_patch = admin_client.patch(
        f"/api/admin/items/{item['id']}",
        json={"data": large_data},
    )
    assert res_patch.status_code == 422


def test_admin_unknown_id_returns_404(admin_client: TestClient) -> None:
    random_id = str(uuid.uuid4())
    assert admin_client.get(f"/api/admin/blocks/{random_id}").status_code == 404
    assert admin_client.patch(f"/api/admin/blocks/{random_id}", json={"title": "foo"}).status_code == 404
    assert admin_client.delete(f"/api/admin/blocks/{random_id}").status_code == 404
    assert admin_client.post(f"/api/admin/blocks/{random_id}/items", json={"data": {}}).status_code == 404
    assert admin_client.patch(f"/api/admin/items/{random_id}", json={"position": 1}).status_code == 404
    assert admin_client.delete(f"/api/admin/items/{random_id}").status_code == 404
