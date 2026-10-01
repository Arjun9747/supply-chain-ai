from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from scai.adapters.db.models import ShipmentRow
from scai.adapters.db.repositories.base import BaseRepository
from scai.domain.enums import ShipmentStatus


class ShipmentRepository(BaseRepository[ShipmentRow]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ShipmentRow, session)

    async def get_by_status(self, status: ShipmentStatus) -> list[ShipmentRow]:
        stmt = select(ShipmentRow).where(ShipmentRow.status == status)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
