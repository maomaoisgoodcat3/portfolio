import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.config import Settings
from app.db import Base
from app.models import Block, BlockItem


def test_settings_database_url_from_components() -> None:
    settings = Settings(
        postgres_user="test_user",
        postgres_password="test_password",
        postgres_db="test_db",
        postgres_host="test_host",
        postgres_port=5432,
    )
    url = settings.get_database_url()
    assert url.render_as_string(hide_password=False) == (
        "postgresql+psycopg://test_user:test_password@test_host:5432/test_db"
    )
    assert settings.database_url == url


def test_settings_database_url_override() -> None:
    custom_url = "postgresql+psycopg://admin:secret@custom:6543/custom_db"
    settings = Settings(
        DATABASE_URL=custom_url,
        postgres_user="user",
        postgres_password="pw",
        postgres_db="db",
        postgres_host="host",
        postgres_port=5432,
    )
    assert settings.get_database_url() == custom_url
    assert settings.database_url == custom_url


def test_base_metadata_naming_convention() -> None:
    convention = Base.metadata.naming_convention
    assert convention.get("ck") == "ck_%(table_name)s_%(constraint_name)s"
    assert convention.get("fk") == "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
    assert convention.get("pk") == "pk_%(table_name)s"
    assert convention.get("ix") == "ix_%(column_0_label)s"


def test_blocks_table_definition() -> None:
    table = Block.__table__
    assert table.name == "blocks"

    columns = {col.name: col for col in table.columns}
    expected_columns = {
        "id",
        "type",
        "title",
        "position",
        "visibility",
        "props",
        "created_at",
        "updated_at",
    }
    assert set(columns.keys()) == expected_columns

    assert isinstance(columns["id"].type, UUID)
    assert columns["id"].primary_key is True
    assert callable(columns["id"].default.arg)
    assert isinstance(columns["id"].default.arg(None), uuid.UUID)
    assert columns["position"].default.arg == 0
    assert columns["visibility"].default.arg == "admin"
    assert str(columns["visibility"].server_default.arg) == "admin"
    assert isinstance(columns["props"].default.arg(None), dict)
    assert isinstance(columns["props"].type, JSONB)


def test_blocks_constraints_and_indexes() -> None:
    table = Block.__table__
    ck_names = {c.name for c in table.constraints if isinstance(c, CheckConstraint)}
    assert "ck_blocks_type" in ck_names
    assert "ck_blocks_title_length" in ck_names
    assert "ck_blocks_visibility" in ck_names

    index_names = {idx.name for idx in table.indexes}
    assert "ix_blocks_position" in index_names


def test_block_items_table_definition() -> None:
    table = BlockItem.__table__
    assert table.name == "block_items"

    columns = {col.name: col for col in table.columns}
    expected_columns = {
        "id",
        "block_id",
        "position",
        "visibility",
        "data",
        "created_at",
        "updated_at",
    }
    assert set(columns.keys()) == expected_columns

    assert isinstance(columns["id"].type, UUID)
    assert columns["id"].primary_key is True
    assert callable(columns["id"].default.arg)
    assert isinstance(columns["id"].default.arg(None), uuid.UUID)
    assert columns["position"].default.arg == 0
    assert columns["visibility"].default.arg == "admin"
    assert str(columns["visibility"].server_default.arg) == "admin"
    assert isinstance(columns["data"].default.arg(None), dict)
    assert isinstance(columns["data"].type, JSONB)


def test_block_items_constraints_and_indexes() -> None:
    table = BlockItem.__table__
    ck_names = {c.name for c in table.constraints if isinstance(c, CheckConstraint)}
    assert "ck_block_items_visibility" in ck_names

    fk_constraints = [c for c in table.constraints if isinstance(c, ForeignKeyConstraint)]
    assert len(fk_constraints) == 1
    fk = fk_constraints[0]
    assert fk.name == "fk_block_items_block_id_blocks"
    assert fk.ondelete == "CASCADE"

    index_names = {idx.name for idx in table.indexes if isinstance(idx, Index)}
    assert "ix_block_items_block_id_position" in index_names


def test_block_relationship_configuration() -> None:
    block_rel = Block.__mapper__.relationships["items"]
    assert block_rel.back_populates == "block"
    assert block_rel.passive_deletes is True
    assert block_rel.cascade.delete_orphan is True

    item_rel = BlockItem.__mapper__.relationships["block"]
    assert item_rel.back_populates == "items"


def test_model_explicit_instantiation() -> None:
    block_id = uuid.uuid4()
    item_id = uuid.uuid4()
    now = datetime.now()

    block = Block(
        id=block_id,
        type="profile",
        title="My Profile",
        position=1,
        visibility="admin",
        props={"bio": "Developer"},
        created_at=now,
        updated_at=now,
    )
    assert block.id == block_id
    assert block.type == "profile"
    assert block.title == "My Profile"
    assert block.position == 1
    assert block.visibility == "admin"
    assert block.props == {"bio": "Developer"}

    item = BlockItem(
        id=item_id,
        block_id=block.id,
        position=1,
        visibility="admin",
        data={"link": "https://example.com"},
        created_at=now,
        updated_at=now,
    )
    assert item.id == item_id
    assert item.block_id == block.id
    assert item.data == {"link": "https://example.com"}
