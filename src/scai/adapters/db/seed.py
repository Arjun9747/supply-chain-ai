"""Synthetic data generation and database seeding for the supply-chain domain.

Generates realistic relational domain entities and maps them into SQL rows:
- SCAI-12: Synthetic Suppliers and Parts (SupplierPart links)
- SCAI-13: Warehouses and Inventory Items
- SCAI-14: Purchase Orders and Shipments
- SCAI-15: Historical & Active Disruption Events
- SCAI-16: Seed Pipeline execution logic
"""

import random
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from scai.adapters.db.mappers import (
    disruption_event_to_row,
    inventory_to_row,
    part_to_row,
    purchase_order_to_row,
    shipment_to_row,
    supplier_part_to_row,
    supplier_to_row,
    warehouse_to_row,
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

# Seed parameters for deterministic reproducible generation
RANDOM_SEED = 42

SUPPLIER_NAMES = [
    ("Taiwan Semiconductor Corp", "TW", "Hsinchu"),
    ("Bavarian Precision Motors", "DE", "Bavaria"),
    ("Shenzhen Microelectronics Co", "CN", "Guangdong"),
    ("Tokyo Robotics & Sensor Corp", "JP", "Kanto"),
    ("Bengaluru Tech Components", "IN", "Karnataka"),
    ("Seoul Display Tech", "KR", "Gyeonggi"),
    ("Texas Precision Foundry", "US", "Texas"),
    ("Rotterdam Maritime Components", "NL", "South Holland"),
]

PARTS_CATALOG = [
    ("MCU-32BIT-001", "32-bit Microcontroller", "24.50", True),
    ("SENS-TEMP-002", "Precision Temperature Sensor", "4.15", False),
    ("DISP-OLED-003", "Industrial OLED Display Module", "45.00", True),
    ("BATT-LION-004", "Lithium-Ion Battery Pack 5000mAh", "18.75", True),
    ("CAP-CER-005", "Multilayer Ceramic Capacitor", "0.12", False),
    ("POWER-IC-006", "PMIC Power Management Module", "8.90", False),
]

WAREHOUSES_CATALOG = [
    ("North America Main Hub", "US", "California"),
    ("European Central Logistics Center", "DE", "Hesse"),
    ("Asia-Pacific Distribution Hub", "SG", "Central Region"),
]


def generate_synthetic_dataset(
    num_pos: int = 15,
    num_disruptions: int = 8,
) -> tuple[
    list[Supplier],
    list[Part],
    list[SupplierPart],
    list[Warehouse],
    list[InventoryItem],
    list[PurchaseOrder],
    list[Shipment],
    list[DisruptionEvent],
]:
    """Generates a complete, relational synthetic dataset for supply chain evaluation."""
    rng = random.Random(RANDOM_SEED)  # noqa: S311  # nosec B311 - deterministic synthetic data
    now = datetime.now(UTC)

    # 1. SCAI-12: Suppliers & Parts
    suppliers = [
        Supplier(
            id=uuid4(),
            name=name,
            country=country,
            region=region,
            tier=rng.choice(list(SupplierTier)),
            reliability_score=round(rng.uniform(0.70, 0.99), 2),
        )
        for name, country, region in SUPPLIER_NAMES
    ]

    parts = [
        Part(
            id=uuid4(),
            sku=sku,
            name=name,
            unit_cost=Money(cost),
            is_critical=is_critical,
        )
        for sku, name, cost, is_critical in PARTS_CATALOG
    ]

    supplier_parts: list[SupplierPart] = []
    for part in parts:
        selected_suppliers = rng.sample(suppliers, k=rng.randint(1, 3))
        for idx, supplier in enumerate(selected_suppliers):
            supplier_parts.append(
                SupplierPart(
                    supplier_id=supplier.id,
                    part_id=part.id,
                    lead_time_days=rng.randint(5, 30),
                    unit_price=Money(str(round(float(part.unit_cost) * rng.uniform(0.9, 1.1), 2))),
                    is_primary=(idx == 0),
                )
            )

    # 2. SCAI-13: Warehouses & Inventory
    warehouses = [
        Warehouse(
            id=uuid4(),
            name=name,
            country=country,
            region=region,
        )
        for name, country, region in WAREHOUSES_CATALOG
    ]

    inventory_items: list[InventoryItem] = []
    for warehouse in warehouses:
        for part in parts:
            inventory_items.append(
                InventoryItem(
                    warehouse_id=warehouse.id,
                    part_id=part.id,
                    quantity_on_hand=rng.randint(50, 2000),
                    reorder_point=rng.randint(100, 300),
                    daily_demand=round(rng.uniform(5.0, 50.0), 1),
                )
            )

    # 3. SCAI-14: Purchase Orders & Shipments
    purchase_orders: list[PurchaseOrder] = []
    shipments: list[Shipment] = []

    for _ in range(num_pos):
        sp = rng.choice(supplier_parts)
        wh = rng.choice(warehouses)
        ordered_at = now - timedelta(days=rng.randint(1, 60))
        expected_at = ordered_at + timedelta(days=sp.lead_time_days)
        po_status = rng.choice(list(PurchaseOrderStatus))

        po = PurchaseOrder(
            id=uuid4(),
            supplier_id=sp.supplier_id,
            part_id=sp.part_id,
            warehouse_id=wh.id,
            quantity=rng.randint(100, 1000),
            unit_price=sp.unit_price,
            status=po_status,
            ordered_at=ordered_at,
            expected_at=expected_at,
        )
        purchase_orders.append(po)

        if po_status in (
            PurchaseOrderStatus.CONFIRMED,
            PurchaseOrderStatus.PARTIALLY_RECEIVED,
            PurchaseOrderStatus.RECEIVED,
        ):
            shipment_status = rng.choice(list(ShipmentStatus))
            planned_eta = expected_at
            delay_days = rng.choice([0, 0, 0, 2, 5, 10])
            current_eta = planned_eta + timedelta(days=delay_days)

            delivered_at = current_eta if shipment_status == ShipmentStatus.DELIVERED else None

            shipments.append(
                Shipment(
                    id=uuid4(),
                    purchase_order_id=po.id,
                    mode=rng.choice(list(TransportMode)),
                    status=shipment_status,
                    origin_port="Port of " + rng.choice(["Shanghai", "Tainan", "Hamburg", "Busan"]),
                    destination_port="Port of "
                    + rng.choice(["Los Angeles", "Rotterdam", "Singapore"]),
                    planned_eta=planned_eta,
                    current_eta=current_eta,
                    delivered_at=delivered_at,
                )
            )

    # 4. SCAI-15: Disruption Events
    disruptions: list[DisruptionEvent] = []
    for _ in range(num_disruptions):
        started_at = now - timedelta(days=rng.randint(1, 90))
        is_active = rng.choice([True, False])
        ended_at = None if is_active else started_at + timedelta(days=rng.randint(2, 14))

        disruptions.append(
            DisruptionEvent(
                id=uuid4(),
                type=rng.choice(list(DisruptionType)),
                severity=rng.choice(list(Severity)),
                title=f"{rng.choice(['Typhoon Alert', 'Port Strike', 'Customs Delays', 'Factory Shutdown'])} in Region",
                description="Severe logistical backlog impacting primary freight corridors.",
                country=rng.choice(["US", "TW", "CN", "DE", "SG", "IN", "JP", "KR"]),
                region=rng.choice(["East Coast", "Hsinchu", "Guangdong", "Bavaria", "Central"]),
                started_at=started_at,
                ended_at=ended_at,
            )
        )

    return (
        suppliers,
        parts,
        supplier_parts,
        warehouses,
        inventory_items,
        purchase_orders,
        shipments,
        disruptions,
    )


def seed_database(session: Session) -> dict[str, int]:
    """SCAI-16: Seeds the database session with generated entities using mappers."""
    (
        suppliers,
        parts,
        supplier_parts,
        warehouses,
        inventory_items,
        purchase_orders,
        shipments,
        disruptions,
    ) = generate_synthetic_dataset()

    for s in suppliers:
        session.add(supplier_to_row(s))
    for p in parts:
        session.add(part_to_row(p))
    for sp in supplier_parts:
        session.add(supplier_part_to_row(sp))
    for w in warehouses:
        session.add(warehouse_to_row(w))
    for inv in inventory_items:
        session.add(inventory_to_row(inv))
    for po in purchase_orders:
        session.add(purchase_order_to_row(po))
    for sh in shipments:
        session.add(shipment_to_row(sh))
    for d in disruptions:
        session.add(disruption_event_to_row(d))

    session.commit()

    return {
        "suppliers": len(suppliers),
        "parts": len(parts),
        "supplier_parts": len(supplier_parts),
        "warehouses": len(warehouses),
        "inventory_items": len(inventory_items),
        "purchase_orders": len(purchase_orders),
        "shipments": len(shipments),
        "disruption_events": len(disruptions),
    }
