"""SQLAlchemy table definitions. Row classes are persistence details.

They map to and from the pure domain entities (see mappers) and are never
exposed outside the adapters layer.
"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    false,
)
from sqlalchemy.orm import Mapped, mapped_column

from scai.adapters.db.base import Base, enum_column
from scai.domain.enums import SupplierTier

_MONEY = Numeric(14, 2)
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
