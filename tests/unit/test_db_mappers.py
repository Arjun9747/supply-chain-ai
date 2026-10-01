"""Unit tests for DB mappers (adapters/db/mappers.py)."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from scai.adapters.db.mappers import (
    disruption_event_to_entity,
    disruption_event_to_row,
    inventory_to_entity,
    inventory_to_row,
    part_to_entity,
    part_to_row,
    purchase_order_to_entity,
    purchase_order_to_row,
    shipment_to_entity,
    shipment_to_row,
    supplier_part_to_entity,
    supplier_part_to_row,
    supplier_to_entity,
    supplier_to_row,
    warehouse_to_entity,
    warehouse_to_row,
)
from scai.adapters.db.models import (
    PurchaseOrderRow,
    ShipmentRow,
    SupplierRow,
)
from scai.domain.entities import (
    DisruptionEvent,
    InventoryItem,
    Money,
    Part,
    PurchaseOrder,
    Shipment,
    Supplier,
    SupplierPart,
    Warehouse,
)
from scai.domain.enums import (
    DisruptionType,
    PurchaseOrderStatus,
    Severity,
    ShipmentStatus,
    SupplierTier,
    TransportMode,
)


def _now() -> datetime:
    return datetime.now(UTC)


def test_supplier_mapper_roundtrip() -> None:
    entity = Supplier(
        id=uuid4(),
        name="Acme Semi",
        country="TW",
        region="Hsinchu",
        tier=SupplierTier.TIER_1,
        reliability_score=0.95,
    )
    row = supplier_to_row(entity)
    reconstructed = supplier_to_entity(row)
    assert reconstructed == entity


def test_supplier_mapper_corrupt_row_raises() -> None:
    row = SupplierRow(
        id=uuid4(),
        name="Acme",
        country="TW",
        region="Hsinchu",
        tier="tier_9",  # Invalid enum value
        reliability_score=0.95,
    )
    with pytest.raises(ValueError, match="not a valid SupplierTier"):
        supplier_to_entity(row)


def test_part_mapper_roundtrip() -> None:
    entity = Part(
        id=uuid4(),
        sku="MCU-32BIT-001",
        name="32-bit Microcontroller",
        unit_cost=Money("12.50"),
        is_critical=True,
    )
    row = part_to_row(entity)
    reconstructed = part_to_entity(row)
    assert reconstructed == entity


def test_supplier_part_mapper_roundtrip() -> None:
    entity = SupplierPart(
        supplier_id=uuid4(),
        part_id=uuid4(),
        lead_time_days=12,
        unit_price=Money("11.80"),
        is_primary=True,
    )
    row = supplier_part_to_row(entity)
    reconstructed = supplier_part_to_entity(row)
    assert reconstructed == entity


def test_warehouse_mapper_roundtrip() -> None:
    entity = Warehouse(
        id=uuid4(),
        name="East Coast Hub",
        country="US",
        region="New Jersey",
    )
    row = warehouse_to_row(entity)
    reconstructed = warehouse_to_entity(row)
    assert reconstructed == entity


def test_inventory_item_mapper_roundtrip() -> None:
    entity = InventoryItem(
        warehouse_id=uuid4(),
        part_id=uuid4(),
        quantity_on_hand=500,
        reorder_point=100,
        daily_demand=25.0,
    )
    row = inventory_to_row(entity)
    reconstructed = inventory_to_entity(row)
    assert reconstructed == entity


def test_purchase_order_mapper_roundtrip() -> None:
    now = _now()
    entity = PurchaseOrder(
        id=uuid4(),
        supplier_id=uuid4(),
        part_id=uuid4(),
        warehouse_id=uuid4(),
        quantity=1000,
        unit_price=Money("15.00"),
        status=PurchaseOrderStatus.SUBMITTED,
        ordered_at=now,
        expected_at=now,
    )
    row = purchase_order_to_row(entity)
    reconstructed = purchase_order_to_entity(row)
    assert reconstructed == entity


def test_purchase_order_mapper_invalid_dates_raises() -> None:
    now = _now()
    row = PurchaseOrderRow(
        id=uuid4(),
        supplier_id=uuid4(),
        part_id=uuid4(),
        warehouse_id=uuid4(),
        quantity=100,
        unit_price=Money("10.00"),
        status=PurchaseOrderStatus.SUBMITTED,
        ordered_at=now,
        expected_at=datetime(2020, 1, 1, tzinfo=UTC),  # earlier than ordered_at
    )
    with pytest.raises(ValueError, match="expected_at must not be before ordered_at"):
        purchase_order_to_entity(row)


def test_shipment_mapper_roundtrip() -> None:
    now = _now()
    entity = Shipment(
        id=uuid4(),
        purchase_order_id=uuid4(),
        mode=TransportMode.AIR,
        status=ShipmentStatus.IN_TRANSIT,
        origin_port="TPE",
        destination_port="LAX",
        planned_eta=now,
        current_eta=now,
    )
    row = shipment_to_row(entity)
    reconstructed = shipment_to_entity(row)
    assert reconstructed == entity


def test_shipment_mapper_corrupt_row_raises() -> None:
    now = _now()
    row = ShipmentRow(
        id=uuid4(),
        purchase_order_id=uuid4(),
        mode="teleport",  # Invalid transport mode
        status=ShipmentStatus.IN_TRANSIT,
        origin_port="TPE",
        destination_port="LAX",
        planned_eta=now,
        current_eta=now,
        delivered_at=None,
    )
    with pytest.raises(ValueError, match="not a valid TransportMode"):
        shipment_to_entity(row)


def test_shipment_mapper_delivered_without_delivered_at_raises() -> None:
    now = _now()
    row = ShipmentRow(
        id=uuid4(),
        purchase_order_id=uuid4(),
        mode=TransportMode.SEA,
        status=ShipmentStatus.DELIVERED,
        origin_port="TPE",
        destination_port="LAX",
        planned_eta=now,
        current_eta=now,
        delivered_at=None,  # Invalid: delivered status requires delivered_at
    )
    with pytest.raises(ValueError, match="a delivered shipment needs delivered_at"):
        shipment_to_entity(row)


def test_disruption_event_mapper_roundtrip() -> None:
    now = _now()
    entity = DisruptionEvent(
        id=uuid4(),
        type=DisruptionType.PORT_STRIKE,
        severity=Severity.HIGH,
        title="Port Strike",
        description="Major labor action",
        country="US",
        region="California",
        started_at=now,
        ended_at=now,
    )
    row = disruption_event_to_row(entity)
    reconstructed = disruption_event_to_entity(row)
    assert reconstructed == entity


def test_disruption_event_mapper_invalid_ended_at_raises() -> None:
    now = _now()
    open_event = DisruptionEvent(
        id=uuid4(),
        type=DisruptionType.PORT_STRIKE,
        severity=Severity.HIGH,
        title="Port Strike",
        description="Major labor action",
        country="US",
        region="California",
        started_at=now,
    )
    row = disruption_event_to_row(open_event)
    row.ended_at = datetime(2020, 1, 1, tzinfo=UTC)
    with pytest.raises(ValueError, match="ended_at must not be before started_at"):
        disruption_event_to_entity(row)
