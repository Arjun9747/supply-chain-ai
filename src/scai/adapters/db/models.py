"""SQLAlchemy table definitions. Row classes are persistence details.

They map to and from the pure domain entities (see mappers) and are never
exposed outside the adapters layer.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    false,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from scai.adapters.db.base import Base, enum_column
from scai.domain.enums import (
    DisruptionType,
    PurchaseOrderStatus,
    Severity,
    ShipmentStatus,
    SupplierTier,
    TransportMode,
)

_MONEY = Numeric(14, 2)
_TIMESTAMPTZ = DateTime(timezone=True)
_COUNTRY_RE = "^[A-Z]{2}$"


class SupplierRow(Base):
    __tablename__ = "suppliers"
    __table_args__ = (
        CheckConstraint(f"country ~ '{_COUNTRY_RE}'", name="country_format"),
        CheckConstraint("reliability_score BETWEEN 0 AND 1", name="reliability_range"),
        Index("ix_suppliers_country_region", "country", "region"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    country: Mapped[str] = mapped_column(String(2))
    region: Mapped[str] = mapped_column(String(200))
    tier: Mapped[SupplierTier] = mapped_column(enum_column(SupplierTier, "supplier_tier"))
    reliability_score: Mapped[float] = mapped_column(Float)


class PartRow(Base):
    __tablename__ = "parts"
    __table_args__ = (CheckConstraint("unit_cost >= 0", name="unit_cost_non_negative"),)

    id: Mapped[UUID] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    unit_cost: Mapped[Decimal] = mapped_column(_MONEY)
    is_critical: Mapped[bool] = mapped_column(Boolean, server_default=false())


class SupplierPartRow(Base):
    __tablename__ = "supplier_parts"
    __table_args__ = (
        CheckConstraint("lead_time_days > 0", name="lead_time_positive"),
        CheckConstraint("unit_price >= 0", name="unit_price_non_negative"),
        Index("ix_supplier_parts_part_id", "part_id"),
    )

    supplier_id: Mapped[UUID] = mapped_column(
        ForeignKey("suppliers.id", ondelete="RESTRICT"), primary_key=True
    )
    part_id: Mapped[UUID] = mapped_column(
        ForeignKey("parts.id", ondelete="RESTRICT"), primary_key=True
    )
    lead_time_days: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[Decimal] = mapped_column(_MONEY)
    is_primary: Mapped[bool] = mapped_column(Boolean, server_default=false())


class WarehouseRow(Base):
    __tablename__ = "warehouses"
    __table_args__ = (
        CheckConstraint(f"country ~ '{_COUNTRY_RE}'", name="country_format"),
        Index("ix_warehouses_country_region", "country", "region"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    country: Mapped[str] = mapped_column(String(2))
    region: Mapped[str] = mapped_column(String(200))


class InventoryRow(Base):
    __tablename__ = "inventory"
    __table_args__ = (
        CheckConstraint("quantity_on_hand >= 0", name="quantity_non_negative"),
        CheckConstraint("reorder_point >= 0", name="reorder_point_non_negative"),
        CheckConstraint("daily_demand >= 0", name="daily_demand_non_negative"),
        Index("ix_inventory_part_id", "part_id"),
    )

    warehouse_id: Mapped[UUID] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"), primary_key=True
    )
    part_id: Mapped[UUID] = mapped_column(
        ForeignKey("parts.id", ondelete="RESTRICT"), primary_key=True
    )
    quantity_on_hand: Mapped[int] = mapped_column(Integer)
    reorder_point: Mapped[int] = mapped_column(Integer)
    daily_demand: Mapped[float] = mapped_column(Float)


class PurchaseOrderRow(Base):
    __tablename__ = "purchase_orders"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("unit_price >= 0", name="unit_price_non_negative"),
        CheckConstraint("expected_at >= ordered_at", name="expected_after_ordered"),
        Index("ix_purchase_orders_supplier_id", "supplier_id"),
        Index("ix_purchase_orders_part_id", "part_id"),
        Index("ix_purchase_orders_warehouse_id", "warehouse_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    supplier_id: Mapped[UUID] = mapped_column(ForeignKey("suppliers.id", ondelete="RESTRICT"))
    part_id: Mapped[UUID] = mapped_column(ForeignKey("parts.id", ondelete="RESTRICT"))
    warehouse_id: Mapped[UUID] = mapped_column(ForeignKey("warehouses.id", ondelete="RESTRICT"))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[Decimal] = mapped_column(_MONEY)
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        enum_column(PurchaseOrderStatus, "purchase_order_status")
    )
    ordered_at: Mapped[datetime] = mapped_column(_TIMESTAMPTZ)
    expected_at: Mapped[datetime] = mapped_column(_TIMESTAMPTZ)


class ShipmentRow(Base):
    __tablename__ = "shipments"
    __table_args__ = (
        # Mirrors the domain rule: delivered_at is set if and only if delivered.
        CheckConstraint(
            f"(status = '{ShipmentStatus.DELIVERED.value}') = (delivered_at IS NOT NULL)",
            name="delivered_at_matches_status",
        ),
        Index("ix_shipments_purchase_order_id", "purchase_order_id"),
        Index("ix_shipments_status", "status"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    purchase_order_id: Mapped[UUID] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="RESTRICT")
    )
    mode: Mapped[TransportMode] = mapped_column(enum_column(TransportMode, "transport_mode"))
    status: Mapped[ShipmentStatus] = mapped_column(enum_column(ShipmentStatus, "shipment_status"))
    origin_port: Mapped[str] = mapped_column(String(200))
    destination_port: Mapped[str] = mapped_column(String(200))
    planned_eta: Mapped[datetime] = mapped_column(_TIMESTAMPTZ)
    current_eta: Mapped[datetime] = mapped_column(_TIMESTAMPTZ)
    delivered_at: Mapped[datetime | None] = mapped_column(_TIMESTAMPTZ)


class DisruptionEventRow(Base):
    __tablename__ = "disruption_events"
    __table_args__ = (
        CheckConstraint(f"country ~ '{_COUNTRY_RE}'", name="country_format"),
        CheckConstraint("ended_at IS NULL OR ended_at >= started_at", name="ended_after_started"),
        # Partial index: the Risk agent mostly asks "what is open right now?",
        # so index only the open events instead of the whole history.
        Index(
            "ix_disruption_events_open_country_region",
            "country",
            "region",
            postgresql_where=text("ended_at IS NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    type: Mapped[DisruptionType] = mapped_column(enum_column(DisruptionType, "disruption_type"))
    severity: Mapped[Severity] = mapped_column(enum_column(Severity, "severity"))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, server_default="")
    country: Mapped[str] = mapped_column(String(2))
    region: Mapped[str] = mapped_column(String(200))
    started_at: Mapped[datetime] = mapped_column(_TIMESTAMPTZ)
    ended_at: Mapped[datetime | None] = mapped_column(_TIMESTAMPTZ)
