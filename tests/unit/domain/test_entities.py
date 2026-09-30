"""Unit tests for the pure domain entities."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid5

import pytest
from pydantic import ValidationError

from scai.domain.entities import (
    DisruptionEvent,
    InventoryItem,
    PurchaseOrder,
    Shipment,
    Supplier,
)
from scai.domain.enums import (
    DisruptionType,
    PurchaseOrderStatus,
    Severity,
    ShipmentStatus,
    SupplierTier,
    TransportMode,
)

NS = UUID("00000000-0000-0000-0000-000000000001")
T0 = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def uid(label: str) -> UUID:
    """Deterministic UUID so tests never depend on randomness."""
    return uuid5(NS, label)


def supplier_kwargs(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": uid("s1"),
        "name": "Shenzhen Components",
        "country": "CN",
        "region": "Guangdong",
        "tier": SupplierTier.TIER_1,
        "reliability_score": 0.9,
    }
    return {**base, **overrides}


def shipment_kwargs(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": uid("sh1"),
        "purchase_order_id": uid("po1"),
        "mode": TransportMode.SEA,
        "status": ShipmentStatus.IN_TRANSIT,
        "origin_port": "Shenzhen",
        "destination_port": "Chennai",
        "planned_eta": T0,
        "current_eta": T0,
    }
    return {**base, **overrides}


def test_supplier_valid() -> None:
    supplier = Supplier(**supplier_kwargs())
    assert supplier.country == "CN"
    assert supplier.tier is SupplierTier.TIER_1


@pytest.mark.parametrize("bad", ["cn", "CHN", "C", "1N", ""])
def test_supplier_rejects_bad_country_code(bad: str) -> None:
    with pytest.raises(ValidationError):
        Supplier(**supplier_kwargs(country=bad))


@pytest.mark.parametrize("bad", [-0.1, 1.1])
def test_supplier_rejects_out_of_range_reliability(bad: float) -> None:
    with pytest.raises(ValidationError):
        Supplier(**supplier_kwargs(reliability_score=bad))


def test_entities_are_frozen() -> None:
    supplier = Supplier(**supplier_kwargs())
    with pytest.raises(ValidationError):
        supplier.name = "Other"


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(ValidationError):
        Supplier(**supplier_kwargs(colour="red"))


def test_inventory_days_of_cover_and_reorder() -> None:
    item = InventoryItem(
        warehouse_id=uid("w1"),
        part_id=uid("p1"),
        quantity_on_hand=100,
        reorder_point=120,
        daily_demand=20.0,
    )
    assert item.days_of_cover == 5.0
    assert item.needs_reorder is True


def test_inventory_days_of_cover_is_none_without_demand() -> None:
    item = InventoryItem(
        warehouse_id=uid("w1"),
        part_id=uid("p1"),
        quantity_on_hand=100,
        reorder_point=10,
        daily_demand=0.0,
    )
    assert item.days_of_cover is None
    assert item.needs_reorder is False


def test_purchase_order_total_value_uses_decimal() -> None:
    po = PurchaseOrder(
        id=uid("po1"),
        supplier_id=uid("s1"),
        part_id=uid("p1"),
        warehouse_id=uid("w1"),
        quantity=4,
        unit_price=Decimal("12.50"),
        status=PurchaseOrderStatus.CONFIRMED,
        ordered_at=T0,
        expected_at=T0 + timedelta(days=10),
    )
    assert po.total_value == Decimal("50.00")


def test_purchase_order_rejects_expected_before_ordered() -> None:
    with pytest.raises(ValueError, match="expected_at"):
        PurchaseOrder(
            id=uid("po1"),
            supplier_id=uid("s1"),
            part_id=uid("p1"),
            warehouse_id=uid("w1"),
            quantity=1,
            unit_price=Decimal("1.00"),
            status=PurchaseOrderStatus.DRAFT,
            ordered_at=T0,
            expected_at=T0 - timedelta(days=1),
        )


def test_naive_datetime_is_rejected() -> None:
    naive = datetime(2026, 1, 1, 12, 0)  # noqa: DTZ001 - deliberately naive
    with pytest.raises(ValidationError):
        Shipment(**shipment_kwargs(planned_eta=naive, current_eta=naive))


def test_shipment_delay_days() -> None:
    late = Shipment(
        **shipment_kwargs(
            status=ShipmentStatus.DELAYED,
            current_eta=T0 + timedelta(days=3, hours=2),
        )
    )
    on_time = Shipment(**shipment_kwargs())
    assert late.delay_days == 3
    assert on_time.delay_days == 0


def test_delivered_shipment_requires_delivered_at() -> None:
    with pytest.raises(ValueError, match="delivered_at"):
        Shipment(**shipment_kwargs(status=ShipmentStatus.DELIVERED))
    with pytest.raises(ValueError, match="delivered_at"):
        Shipment(**shipment_kwargs(delivered_at=T0))


def test_disruption_active_and_date_validation() -> None:
    event = DisruptionEvent(
        id=uid("d1"),
        type=DisruptionType.PORT_STRIKE,
        severity=Severity.HIGH,
        title="Chennai port strike",
        country="IN",
        region="Tamil Nadu",
        started_at=T0,
    )
    assert event.is_active is True
    with pytest.raises(ValueError, match="ended_at"):
        DisruptionEvent(
            id=uid("d2"),
            type=DisruptionType.PORT_STRIKE,
            severity=Severity.LOW,
            title="Bad dates",
            country="IN",
            region="Tamil Nadu",
            started_at=T0,
            ended_at=T0 - timedelta(days=1),
        )


def test_severity_rank_orders_correctly() -> None:
    shuffled = [Severity.HIGH, Severity.LOW, Severity.CRITICAL, Severity.MEDIUM]
    expected = [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
    assert sorted(shuffled, key=lambda s: s.rank) == expected
