from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from scai.adapters.db.models import InventoryRow
from scai.adapters.db.repositories.base import BaseRepository


class InventoryRepository(BaseRepository[InventoryRow]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(InventoryRow, session)

    async def get_by_part_id(self, part_id: UUID) -> list[InventoryRow]:
        stmt = select(InventoryRow).where(InventoryRow.part_id == part_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_warehouse_id(self, warehouse_id: UUID) -> list[InventoryRow]:
        stmt = select(InventoryRow).where(InventoryRow.warehouse_id == warehouse_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_one(self, warehouse_id: UUID, part_id: UUID) -> InventoryRow | None:
        """Inventory has a composite key: (warehouse_id, part_id)."""
        stmt = select(InventoryRow).where(
            InventoryRow.warehouse_id == warehouse_id,
            InventoryRow.part_id == part_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_filtered(
        self,
        warehouse_id: UUID | None = None,
        part_id: UUID | None = None,
        low_stock_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[InventoryRow]:
        stmt = select(InventoryRow)
        if warehouse_id is not None:
            stmt = stmt.where(InventoryRow.warehouse_id == warehouse_id)
        if part_id is not None:
            stmt = stmt.where(InventoryRow.part_id == part_id)
        if low_stock_only:
            stmt = stmt.where(InventoryRow.quantity_on_hand < InventoryRow.reorder_point)
        stmt = stmt.order_by(InventoryRow.warehouse_id, InventoryRow.part_id)
        result = await self.session.execute(stmt.limit(limit).offset(offset))
        return list(result.scalars().all())
