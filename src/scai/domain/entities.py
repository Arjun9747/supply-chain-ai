"""Pure domain entities for supply-chain risk and logistics.

These are immutable Pydantic models with no knowledge of databases, HTTP
or LLMs. Adapters map to and from them. Money is ``Decimal`` and every
timestamp must be timezone-aware.
"""

from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints

from scai.domain.enums import (
    DisruptionType,
    PurchaseOrderStatus,
    Severity,
    ShipmentStatus,
    SupplierTier,
    TransportMode,
)

# ISO 3166-1 alpha-2 shape, e.g. "IN", "CN", "DE".
CountryCode = Annotated[str, StringConstraints(pattern=r"^[A-Z]{2}$")]
Money = Annotated[Decimal, Field(ge=0, max_digits=14, decimal_places=2)]
Name = Annotated[str, StringConstraints(min_length=1, max_length=200)]


class _Entity(BaseModel):
    """Base for all entities: immutable, strict about unknown fields."""

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)


class Supplier(_Entity):
    id: UUID
    name: Name
    country: CountryCode
    region: Name
    tier: SupplierTier
    reliability_score: Annotated[float, Field(ge=0.0, le=1.0)]


class Part(_Entity):
    id: UUID
    sku: Annotated[str, StringConstraints(min_length=1, max_length=64)]
    name: Name
    unit_cost: Money
    is_critical: bool = False


class SupplierPart(_Entity):
    """Which supplier can provide which part, and how fast."""

    supplier_id: UUID
    part_id: UUID
    lead_time_days: Annotated[int, Field(gt=0)]
    unit_price: Money
    is_primary: bool = False


class Warehouse(_Entity):
    id: UUID
    name: Name
    country: CountryCode
    region: Name


class InventoryItem(_Entity):
    warehouse_id: UUID
    part_id: UUID
    quantity_on_hand: Annotated[int, Field(ge=0)]
    reorder_point: Annotated[int, Field(ge=0)]
    daily_demand: Annotated[float, Field(ge=0.0)]

    @property
    def days_of_cover(self) -> float | None:
        """Days until stock runs out at current demand (None if no demand)."""
        if self.daily_demand == 0:
            return None
        return self.quantity_on_hand / self.daily_demand

    @property
    def needs_reorder(self) -> bool:
        return self.quantity_on_hand <= self.reorder_point


class PurchaseOrder(_Entity):
    id: UUID
    supplier_id: UUID
    part_id: UUID
    warehouse_id: UUID
    quantity: Annotated[int, Field(gt=0)]
    unit_price: Money
    status: PurchaseOrderStatus
    ordered_at: AwareDatetime
    expected_at: AwareDatetime

    @property
    def total_value(self) -> Decimal:
        return self.unit_price * self.quantity

    def model_post_init(self, __context: object) -> None:
        if self.expected_at < self.ordered_at:
            raise ValueError("expected_at must not be before ordered_at")


class Shipment(_Entity):
    id: UUID
    purchase_order_id: UUID
    mode: TransportMode
    status: ShipmentStatus
    origin_port: Name
    destination_port: Name
    planned_eta: AwareDatetime
    current_eta: AwareDatetime
    delivered_at: AwareDatetime | None = None

    def model_post_init(self, __context: object) -> None:
        if self.status is ShipmentStatus.DELIVERED and self.delivered_at is None:
            raise ValueError("a delivered shipment needs delivered_at")
        if self.status is not ShipmentStatus.DELIVERED and self.delivered_at is not None:
            raise ValueError("delivered_at is only valid for delivered shipments")

    @property
    def delay_days(self) -> int:
        """Whole days late versus the plan (0 if on time or early)."""
        actual = self.delivered_at or self.current_eta
        return max(0, (actual - self.planned_eta).days)


class DisruptionEvent(_Entity):
    id: UUID
    type: DisruptionType
    severity: Severity
    title: Name
    description: str = ""
    country: CountryCode
    region: Name
    started_at: AwareDatetime
    ended_at: AwareDatetime | None = None

    def model_post_init(self, __context: object) -> None:
        if self.ended_at is not None and self.ended_at < self.started_at:
            raise ValueError("ended_at must not be before started_at")

    @property
    def is_active(self) -> bool:
        return self.ended_at is None
