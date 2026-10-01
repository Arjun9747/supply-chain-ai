from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from scai.adapters.db.mappers import shipment_to_entity
from scai.adapters.db.repositories.shipment import ShipmentRepository
from scai.api.dependencies import get_db_session
from scai.domain.entities import Shipment
from scai.domain.enums import ShipmentStatus

router = APIRouter(prefix="/shipments", tags=["shipments"])

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("/")
async def list_shipments(
    session: SessionDep,
    shipment_status: Annotated[ShipmentStatus | None, Query(alias="status")] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[Shipment]:
    """Retrieve shipments, optionally filtered by status."""
    repo = ShipmentRepository(session)
    if shipment_status is not None:
        filtered = await repo.get_by_status(shipment_status)
        rows = filtered[skip : skip + limit]
    else:
        rows = await repo.list_all(limit=limit, offset=skip)
    return [shipment_to_entity(row) for row in rows]


@router.get("/{shipment_id}")
async def get_shipment(shipment_id: UUID, session: SessionDep) -> Shipment:
    """Retrieve a specific shipment by ID."""
    row = await ShipmentRepository(session).get_by_id(shipment_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shipment with id {shipment_id} not found",
        )
    return shipment_to_entity(row)
