"""Mappers between SQLAlchemy rows and pure domain entities.

Rows are persistence details and never leave the adapters layer. Reading a
row rebuilds the entity through its constructor, so enum coercion and the
entity validators run again: a corrupt row raises instead of leaking bad
data into the domain.
"""

from scai.adapters.db.models import (
    DisruptionEventRow,
    InventoryRow,
    PartRow,
    PurchaseOrderRow,
    ShipmentRow,
    SupplierPartRow,
    SupplierRow,
    WarehouseRow,
)
from scai.domain.entities import (
    DisruptionEvent,
    InventoryItem,
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

# --- Supplier ---------------------------------------------------------------


def supplier_to_row(entity: Supplier) -> SupplierRow:
    return SupplierRow(
        id=entity.id,
        name=entity.name,
        country=entity.country,
        region=entity.region,
        tier=entity.tier,
        reliability_score=entity.reliability_score,
    )


def supplier_to_entity(row: SupplierRow) -> Supplier:
    return Supplier(
        id=row.id,
        name=row.name,
        country=row.country,
        region=row.region,
        tier=SupplierTier(row.tier),
        reliability_score=row.reliability_score,
    )


# --- Part -------------------------------------------------------------------


def part_to_row(entity: Part) -> PartRow:
    return PartRow(
        id=entity.id,
        sku=entity.sku,
        name=entity.name,
        unit_cost=entity.unit_cost,
        is_critical=entity.is_critical,
    )


def part_to_entity(row: PartRow) -> Part:
    return Part(
        id=row.id,
        sku=row.sku,
        name=row.name,
        unit_cost=row.unit_cost,
        is_critical=row.is_critical,
    )


# --- SupplierPart (composite key: supplier_id + part_id) --------------------


def supplier_part_to_row(entity: SupplierPart) -> SupplierPartRow:
    return SupplierPartRow(
        supplier_id=entity.supplier_id,
        part_id=entity.part_id,
        lead_time_days=entity.lead_time_days,
        unit_price=entity.unit_price,
        is_primary=entity.is_primary,
    )


def supplier_part_to_entity(row: SupplierPartRow) -> SupplierPart:
    return SupplierPart(
        supplier_id=row.supplier_id,
        part_id=row.part_id,
        lead_time_days=row.lead_time_days,
        unit_price=row.unit_price,
        is_primary=row.is_primary,
    )


# --- Warehouse --------------------------------------------------------------


def warehouse_to_row(entity: Warehouse) -> WarehouseRow:
    return WarehouseRow(
        id=entity.id,
        name=entity.name,
        country=entity.country,
        region=entity.region,
    )


def warehouse_to_entity(row: WarehouseRow) -> Warehouse:
    return Warehouse(
        id=row.id,
        name=row.name,
        country=row.country,
        region=row.region,
    )


# --- InventoryItem (composite key: warehouse_id + part_id) ------------------


def inventory_to_row(entity: InventoryItem) -> InventoryRow:
    return InventoryRow(
        warehouse_id=entity.warehouse_id,
        part_id=entity.part_id,
        quantity_on_hand=entity.quantity_on_hand,
        reorder_point=entity.reorder_point,
        daily_demand=entity.daily_demand,
    )


def inventory_to_entity(row: InventoryRow) -> InventoryItem:
    return InventoryItem(
        warehouse_id=row.warehouse_id,
        part_id=row.part_id,
        quantity_on_hand=row.quantity_on_hand,
        reorder_point=row.reorder_point,
        daily_demand=row.daily_demand,
    )


# --- PurchaseOrder ----------------------------------------------------------


def purchase_order_to_row(entity: PurchaseOrder) -> PurchaseOrderRow:
    return PurchaseOrderRow(
        id=entity.id,
        supplier_id=entity.supplier_id,
        part_id=entity.part_id,
        warehouse_id=entity.warehouse_id,
        quantity=entity.quantity,
        unit_price=entity.unit_price,
        status=entity.status,
        ordered_at=entity.ordered_at,
        expected_at=entity.expected_at,
    )


def purchase_order_to_entity(row: PurchaseOrderRow) -> PurchaseOrder:
    return PurchaseOrder(
        id=row.id,
        supplier_id=row.supplier_id,
        part_id=row.part_id,
        warehouse_id=row.warehouse_id,
        quantity=row.quantity,
        unit_price=row.unit_price,
        status=PurchaseOrderStatus(row.status),
        ordered_at=row.ordered_at,
        expected_at=row.expected_at,
    )


# --- Shipment ---------------------------------------------------------------


def shipment_to_row(entity: Shipment) -> ShipmentRow:
    return ShipmentRow(
        id=entity.id,
        purchase_order_id=entity.purchase_order_id,
        mode=entity.mode,
        status=entity.status,
        origin_port=entity.origin_port,
        destination_port=entity.destination_port,
        planned_eta=entity.planned_eta,
        current_eta=entity.current_eta,
        delivered_at=entity.delivered_at,
    )


def shipment_to_entity(row: ShipmentRow) -> Shipment:
    return Shipment(
        id=row.id,
        purchase_order_id=row.purchase_order_id,
        mode=TransportMode(row.mode),
        status=ShipmentStatus(row.status),
        origin_port=row.origin_port,
        destination_port=row.destination_port,
        planned_eta=row.planned_eta,
        current_eta=row.current_eta,
        delivered_at=row.delivered_at,
    )


# --- DisruptionEvent --------------------------------------------------------


def disruption_event_to_row(entity: DisruptionEvent) -> DisruptionEventRow:
    return DisruptionEventRow(
        id=entity.id,
        type=entity.type,
        severity=entity.severity,
        title=entity.title,
        description=entity.description,
        country=entity.country,
        region=entity.region,
        started_at=entity.started_at,
        ended_at=entity.ended_at,
    )


def disruption_event_to_entity(row: DisruptionEventRow) -> DisruptionEvent:
    return DisruptionEvent(
        id=row.id,
        type=DisruptionType(row.type),
        severity=Severity(row.severity),
        title=row.title,
        description=row.description,
        country=row.country,
        region=row.region,
        started_at=row.started_at,
        ended_at=row.ended_at,
    )
