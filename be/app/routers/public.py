from collections import defaultdict
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import Block, BlockItem
from app.schemas import BlockItemResponse, BlockResponse

router = APIRouter(prefix="/api/public", tags=["public"])


@router.get("/blocks", response_model=list[BlockResponse])
def get_public_blocks(
    db: Annotated[Session, Depends(get_db)],
) -> list[BlockResponse]:
    # Query only public blocks ordered by position ASC
    blocks = list(
        db.scalars(
            select(Block)
            .where(Block.visibility == "public")
            .order_by(Block.position.asc())
        ).all()
    )

    if not blocks:
        return []

    block_ids = [b.id for b in blocks]

    # Query only public items for these blocks ordered by position ASC
    public_items = list(
        db.scalars(
            select(BlockItem)
            .where(
                BlockItem.block_id.in_(block_ids),
                BlockItem.visibility == "public",
            )
            .order_by(BlockItem.position.asc())
        ).all()
    )

    items_by_block: dict[UUID, list[BlockItemResponse]] = defaultdict(list)
    for item in public_items:
        items_by_block[item.block_id].append(
            BlockItemResponse.model_validate(item)
        )

    return [
        BlockResponse(
            id=b.id,
            type=b.type,
            title=b.title,
            position=b.position,
            visibility=b.visibility,
            props=b.props,
            items=items_by_block.get(b.id, []),
            created_at=b.created_at,
            updated_at=b.updated_at,
        )
        for b in blocks
    ]
