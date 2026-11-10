from app.models import Block, BlockItem
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_get_public_blocks_empty(client: TestClient) -> None:
    response = client.get("/api/public/blocks")
    assert response.status_code == 200
    assert response.json() == []


def test_get_public_blocks_excludes_admin_blocks(
    client: TestClient, db_session: Session
) -> None:
    admin_block = Block(
        type="about",
        title="Admin Only Block",
        position=0,
        visibility="admin",
    )
    public_block = Block(
        type="profile",
        title="Public Profile Block",
        position=1,
        visibility="public",
    )
    db_session.add_all([admin_block, public_block])
    db_session.commit()

    response = client.get("/api/public/blocks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == str(public_block.id)
    assert data[0]["title"] == "Public Profile Block"


def test_get_public_blocks_excludes_admin_items_from_public_blocks(
    client: TestClient, db_session: Session
) -> None:
    block = Block(
        type="skills",
        title="Skills Block",
        position=0,
        visibility="public",
    )
    db_session.add(block)
    db_session.commit()

    pub_item = BlockItem(
        block_id=block.id,
        position=0,
        visibility="public",
        data={"skill": "Python"},
    )
    adm_item = BlockItem(
        block_id=block.id,
        position=1,
        visibility="admin",
        data={"skill": "Internal tool"},
    )
    db_session.add_all([pub_item, adm_item])
    db_session.commit()

    response = client.get("/api/public/blocks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    items = data[0]["items"]
    assert len(items) == 1
    assert items[0]["id"] == str(pub_item.id)
    assert items[0]["data"] == {"skill": "Python"}


def test_get_public_blocks_ordered_by_position(
    client: TestClient, db_session: Session
) -> None:
    b2 = Block(type="contact", title="Block 2", position=2, visibility="public")
    b0 = Block(type="profile", title="Block 0", position=0, visibility="public")
    b1 = Block(type="about", title="Block 1", position=1, visibility="public")
    db_session.add_all([b2, b0, b1])
    db_session.commit()

    item_b0_2 = BlockItem(
        block_id=b0.id, position=2, visibility="public", data={"idx": 2}
    )
    item_b0_0 = BlockItem(
        block_id=b0.id, position=0, visibility="public", data={"idx": 0}
    )
    item_b0_1 = BlockItem(
        block_id=b0.id, position=1, visibility="public", data={"idx": 1}
    )
    db_session.add_all([item_b0_2, item_b0_0, item_b0_1])
    db_session.commit()

    response = client.get("/api/public/blocks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert [d["title"] for d in data] == ["Block 0", "Block 1", "Block 2"]
    assert [it["data"]["idx"] for it in data[0]["items"]] == [0, 1, 2]


def test_get_public_blocks_does_not_require_auth(client: TestClient) -> None:
    # client fixture has no require_admin override
    response = client.get("/api/public/blocks")
    assert response.status_code == 200
