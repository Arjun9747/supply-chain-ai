"""Unit tests for synthetic dataset generator (SCAI-12 to SCAI-16)."""

from scai.adapters.db.seed import generate_synthetic_dataset


def test_generate_synthetic_dataset() -> None:
    (
        suppliers,
        parts,
        supplier_parts,
        warehouses,
        inventory_items,
        purchase_orders,
        _shipments,
        disruptions,
    ) = generate_synthetic_dataset(num_pos=10, num_disruptions=5)

    assert len(suppliers) > 0
    assert len(parts) > 0
    assert len(supplier_parts) > 0
    assert len(warehouses) > 0
    assert len(inventory_items) > 0
    assert len(purchase_orders) == 10
    assert len(disruptions) == 5
    assert all(d.started_at is not None for d in disruptions)
