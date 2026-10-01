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
