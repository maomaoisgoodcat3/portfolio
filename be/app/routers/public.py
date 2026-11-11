from collections import defaultdict
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import Block, BlockItem, ExternalStats
from app.schemas import BlockItemResponse, BlockResponse

router = APIRouter(prefix="/api/public", tags=["public"])


@router.get("/blocks", response_model=None)
def get_public_blocks(
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, Any]]:
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
    stats_blocks = [block for block in blocks if block.type == "stats"]
    stats_by_key = {}
    if stats_blocks:
        stats_keys = [
            (block.props.get("provider"), block.props.get("account"))
            for block in stats_blocks
        ]
        stats_rows = db.scalars(
            select(ExternalStats).where(
                or_(
                    *(
                        and_(
                            ExternalStats.provider == provider,
                            ExternalStats.account == account,
                        )
                        for provider, account in stats_keys
                    )
                )
            )
        ).all()
        stats_by_key = {
            (row.provider, row.account): row
            for row in stats_rows
            if row.fetched_at is not None
        }

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

    result = []
    for b in blocks:
        response = BlockResponse(
            id=b.id,
            type=b.type,
            title=b.title,
            position=b.position,
            visibility=b.visibility,
            props=b.props,
            items=items_by_block.get(b.id, []),
            created_at=b.created_at,
            updated_at=b.updated_at,
        ).model_dump(mode="json")
        if b.type == "stats":
            row = stats_by_key.get((b.props.get("provider"), b.props.get("account")))
            response["stats"] = (
                {"data": row.data, "fetched_at": row.fetched_at}
                if row is not None
                else None
            )
        result.append(response)
    return result
