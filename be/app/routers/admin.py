from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import TypeAdapter, ValidationError
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.deps import get_db, require_admin
from app.models import Block, BlockItem
from app.schemas import (
    BlockCreate,
    BlockItemCreate,
    BlockItemResponse,
    BlockItemUpdate,
    BlockResponse,
    BlockUpdate,
    StatsItemData,
)

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


# ---------------------------------------------------------
# Block Routes
# ---------------------------------------------------------


@router.get("/blocks", response_model=list[BlockResponse])
def list_blocks(
    db: Annotated[Session, Depends(get_db)],
) -> list[BlockResponse]:
    blocks = list(
        db.scalars(select(Block).order_by(Block.position.asc())).all()
    )
    result = []
    for b in blocks:
        sorted_items = sorted(
            [BlockItemResponse.model_validate(it) for it in b.items],
            key=lambda x: x.position,
        )
        result.append(
            BlockResponse(
                id=b.id,
                type=b.type,
                title=b.title,
                position=b.position,
                visibility=b.visibility,
                props=b.props,
                items=sorted_items,
                created_at=b.created_at,
                updated_at=b.updated_at,
            )
        )
    return result


@router.post(
    "/blocks",
    response_model=BlockResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_block(
    payload: BlockCreate,
    db: Annotated[Session, Depends(get_db)],
) -> BlockResponse:
    if payload.type == "profile":
        if db.scalar(select(Block.id).where(Block.type == payload.type)) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Only one {payload.type} block is allowed",
            )

    max_pos = db.scalar(select(func.max(Block.position)))
    new_position = (max_pos + 1) if max_pos is not None else 0

    block = Block(
        type=payload.type,
        title=payload.title,
        visibility=payload.visibility,
        props=payload.props,
        position=new_position,
    )
    db.add(block)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        if payload.type == "profile":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Only one {payload.type} block is allowed",
            ) from None
        raise
    db.refresh(block)

    return BlockResponse(
        id=block.id,
        type=block.type,
        title=block.title,
        position=block.position,
        visibility=block.visibility,
        props=block.props,
        items=[],
        created_at=block.created_at,
        updated_at=block.updated_at,
    )


# CRITICAL: /blocks/order declared before /blocks/{id}
@router.put("/blocks/order", response_model=list[BlockResponse])
def reorder_blocks(
    block_ids: Annotated[list[UUID], Body()],
    db: Annotated[Session, Depends(get_db)],
) -> list[BlockResponse]:
    all_blocks = list(db.scalars(select(Block)).all())
    existing_ids = {b.id for b in all_blocks}

    if set(block_ids) != existing_ids or len(block_ids) != len(existing_ids):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Order list must contain every block ID exactly once",
        )

    block_map = {b.id: b for b in all_blocks}
    for new_pos, b_id in enumerate(block_ids):
        block_map[b_id].position = new_pos

    db.commit()

    # Return refreshed and ordered blocks
    return list_blocks(db=db)


@router.get("/blocks/{id}", response_model=BlockResponse)
def get_block(
    id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> BlockResponse:
    block = db.get(Block, id)
    if not block:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Block not found",
        )
    sorted_items = sorted(
        [BlockItemResponse.model_validate(it) for it in block.items],
        key=lambda x: x.position,
    )
    return BlockResponse(
        id=block.id,
        type=block.type,
        title=block.title,
        position=block.position,
        visibility=block.visibility,
        props=block.props,
        items=sorted_items,
        created_at=block.created_at,
        updated_at=block.updated_at,
    )


@router.patch("/blocks/{id}", response_model=BlockResponse)
def patch_block(
    id: UUID,
    payload: BlockUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> BlockResponse:
    block = db.get(Block, id)
    if not block:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Block not found",
        )

    if payload.title is not None:
        block.title = payload.title
    if payload.visibility is not None:
        block.visibility = payload.visibility
    if payload.props is not None:
        block.props = payload.props

    db.commit()
    db.refresh(block)

    sorted_items = sorted(
        [BlockItemResponse.model_validate(it) for it in block.items],
        key=lambda x: x.position,
    )
    return BlockResponse(
        id=block.id,
        type=block.type,
        title=block.title,
        position=block.position,
        visibility=block.visibility,
        props=block.props,
        items=sorted_items,
        created_at=block.created_at,
        updated_at=block.updated_at,
    )


@router.delete("/blocks/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_block(
    id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    block = db.get(Block, id)
    if not block:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Block not found",
        )
    db.delete(block)
    db.commit()


# ---------------------------------------------------------
# Block Item Routes
# ---------------------------------------------------------


@router.post(
    "/blocks/{block_id}/items",
    response_model=BlockItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_block_item(
    block_id: UUID,
    payload: BlockItemCreate,
    db: Annotated[Session, Depends(get_db)],
) -> BlockItemResponse:
    block = db.get(Block, block_id)
    if not block:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Block not found",
        )

    # Validate stats item data
    if block.type == "stats":
        try:
            validated_data = TypeAdapter(StatsItemData).validate_python(payload.data).model_dump()
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Invalid stats item data: {exc}",
            ) from exc
        item_data = validated_data
    else:
        item_data = payload.data

    # Position: max(position) + 1 within block_id if not provided
    if payload.position is None:
        max_pos = db.scalar(
            select(func.max(BlockItem.position)).where(
                BlockItem.block_id == block_id
            )
        )
        position = (max_pos + 1) if max_pos is not None else 0
    else:
        position = payload.position

    item = BlockItem(
        block_id=block_id,
        visibility=payload.visibility,
        data=item_data,
        position=position,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return BlockItemResponse.model_validate(item)


@router.patch("/items/{id}", response_model=BlockItemResponse)
def patch_block_item(
    id: UUID,
    payload: BlockItemUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> BlockItemResponse:
    item = db.get(BlockItem, id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    if payload.data is not None:
        block = db.get(Block, item.block_id)
        if block and block.type == "stats":
            try:
                validated_data = TypeAdapter(StatsItemData).validate_python(payload.data).model_dump()
            except ValidationError as exc:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=f"Invalid stats item data: {exc}",
                ) from exc
            item.data = validated_data
        else:
            item.data = payload.data

    if payload.visibility is not None:
        item.visibility = payload.visibility

    if payload.position is not None:
        item.position = payload.position

    db.commit()
    db.refresh(item)

    return BlockItemResponse.model_validate(item)


@router.delete("/items/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_block_item(
    id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    item = db.get(BlockItem, id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    db.delete(item)
    db.commit()
