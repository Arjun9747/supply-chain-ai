from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from scai.adapters.db.models import SupplierRow
from scai.adapters.db.repositories.base import BaseRepository


class SupplierRepository(BaseRepository[SupplierRow]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(SupplierRow, session)

    async def get_by_region(self, country: str, region: str | None = None) -> list[SupplierRow]:
        stmt = select(SupplierRow).where(SupplierRow.country == country)
        if region:
            stmt = stmt.where(SupplierRow.region == region)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
