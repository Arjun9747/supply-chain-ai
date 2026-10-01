from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from scai.adapters.db.mappers import supplier_to_entity
from scai.adapters.db.repositories.supplier import SupplierRepository
from scai.api.dependencies import get_db_session
from scai.domain.entities import Supplier

router = APIRouter(prefix="/suppliers", tags=["suppliers"])

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("/")
async def list_suppliers(
    session: SessionDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[Supplier]:
    """Retrieve suppliers."""
    rows = await SupplierRepository(session).list_all(limit=limit, offset=skip)
    return [supplier_to_entity(row) for row in rows]


@router.get("/{supplier_id}")
async def get_supplier(supplier_id: UUID, session: SessionDep) -> Supplier:
    """Retrieve a specific supplier by ID."""
    row = await SupplierRepository(session).get_by_id(supplier_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with id {supplier_id} not found",
        )
    return supplier_to_entity(row)
