from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from scai.adapters.db.mappers import inventory_to_entity
from scai.adapters.db.repositories.inventory import InventoryRepository
from scai.api.dependencies import get_db_session
from scai.domain.entities import InventoryItem

router = APIRouter(prefix="/inventory", tags=["Inventory"])

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("/")
async def list_inventory_items(
    session: SessionDep,
    warehouse_id: Annotated[UUID | None, Query(description="Filter by warehouse")] = None,
    part_id: Annotated[UUID | None, Query(description="Filter by part")] = None,
    low_stock_only: Annotated[bool, Query(description="Only items below reorder point")] = False,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[InventoryItem]:
    """Retrieve inventory items with optional filters."""
    rows = await InventoryRepository(session).list_filtered(
        warehouse_id=warehouse_id,
        part_id=part_id,
        low_stock_only=low_stock_only,
        limit=limit,
        offset=skip,
    )
    return [inventory_to_entity(row) for row in rows]


@router.get("/{warehouse_id}/{part_id}")
async def get_inventory_item(
    warehouse_id: UUID, part_id: UUID, session: SessionDep
) -> InventoryItem:
    """Get one inventory record by its (warehouse, part) key."""
    row = await InventoryRepository(session).get_one(warehouse_id, part_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No inventory for warehouse {warehouse_id} and part {part_id}",
        )
    return inventory_to_entity(row)
