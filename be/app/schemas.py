import json
from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

BlockType = Literal[
    "profile",
    "about",
    "skills",
    "experience",
    "projects",
    "research",
    "links",
    "stats",
    "contact",
]

VisibilityType = Literal["public", "admin"]


def validate_32kb(v: dict[str, Any] | None) -> dict[str, Any] | None:
    if v is not None:
        encoded = json.dumps(v, ensure_ascii=False, separators=(",", ":")).encode(
            "utf-8"
        )
        if len(encoded) > 32768:
            raise ValueError("Payload size exceeds 32768 bytes limit")
    return v


# Stats item discriminated union
class GithubStatsItemData(BaseModel):
    provider: Literal["github"] = "github"
    account: str = Field(min_length=1, max_length=100)
    show: list[str] = Field(default_factory=list)


StatsItemData = Annotated[GithubStatsItemData, Field(discriminator="provider")]


# Block Schemas
class BlockCreate(BaseModel):
    type: BlockType
    title: str = Field(min_length=1, max_length=200)
    visibility: VisibilityType = "admin"
    props: dict[str, Any] = Field(default_factory=dict)

    @field_validator("props")
    @classmethod
    def check_props_size(cls, v: dict[str, Any]) -> dict[str, Any]:
        result = validate_32kb(v)
        return result if result is not None else {}


class BlockUpdate(BaseModel):
    # 'type' is deliberately omitted: block type cannot change after creation
    title: str | None = Field(default=None, min_length=1, max_length=200)
    visibility: VisibilityType | None = None
    props: dict[str, Any] | None = None

    @field_validator("props")
    @classmethod
    def check_props_size(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        return validate_32kb(v)


# Block Item Schemas
class BlockItemCreate(BaseModel):
    visibility: VisibilityType = "admin"
    data: dict[str, Any] = Field(default_factory=dict)
    position: int | None = None

    @field_validator("data")
    @classmethod
    def check_data_size(cls, v: dict[str, Any]) -> dict[str, Any]:
        result = validate_32kb(v)
        return result if result is not None else {}


class BlockItemUpdate(BaseModel):
    visibility: VisibilityType | None = None
    data: dict[str, Any] | None = None
    position: int | None = None

    @field_validator("data")
    @classmethod
    def check_data_size(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        return validate_32kb(v)


# Response Schemas
class BlockItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    block_id: UUID
    position: int
    visibility: str
    data: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class BlockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: str
    title: str
    position: int
    visibility: str
    props: dict[str, Any]
    items: list[BlockItemResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
