import uuid

import pytest

from scai.adapters.db.models import SupplierRow
from scai.adapters.db.repositories.supplier import SupplierRepository
from scai.domain.enums import SupplierTier


@pytest.mark.asyncio
async def test_supplier_repository_create_and_get(db_session):
    repo = SupplierRepository(db_session)
    new_supplier = SupplierRow(
        id=uuid.uuid4(),
        name="Acme Logistics",
        country="US",
        region="NA",
        tier=SupplierTier.TIER_1,
        reliability_score=0.95,
    )
    created = await repo.create(new_supplier)
    assert created.id is not None

    fetched = await repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.name == "Acme Logistics"
