"""Enumerations shared across the supply-chain domain.

All enums are ``StrEnum`` so values serialise cleanly to JSON and to
database text columns without custom converters.
"""

from enum import StrEnum


class SupplierTier(StrEnum):
    """Position of a supplier in the supply chain relative to us."""

    TIER_1 = "tier_1"  # ships directly to us
    TIER_2 = "tier_2"  # supplies our Tier-1 suppliers
    TIER_3 = "tier_3"  # raw materials and sub-components


class TransportMode(StrEnum):
    """How a shipment physically moves."""

    SEA = "sea"
    AIR = "air"
    ROAD = "road"
    RAIL = "rail"


class ShipmentStatus(StrEnum):
    """Lifecycle state of a shipment."""

    PLANNED = "planned"
    IN_TRANSIT = "in_transit"
    AT_PORT = "at_port"
    DELAYED = "delayed"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PurchaseOrderStatus(StrEnum):
    """Lifecycle state of a purchase order."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class DisruptionType(StrEnum):
    """Category of event that can disrupt the supply chain."""

    PORT_STRIKE = "port_strike"
    SEVERE_WEATHER = "severe_weather"
    GEOPOLITICAL = "geopolitical"
    FACTORY_FIRE = "factory_fire"
    CYBER_ATTACK = "cyber_attack"
    CUSTOMS_DELAY = "customs_delay"
    SUPPLIER_INSOLVENCY = "supplier_insolvency"
    CAPACITY_SHORTAGE = "capacity_shortage"


class Severity(StrEnum):
    """How serious a disruption is. Ordered via ``rank``."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def rank(self) -> int:
        """Numeric order (1 = lowest) so severities can be compared."""
        order = {
            Severity.LOW: 1,
            Severity.MEDIUM: 2,
            Severity.HIGH: 3,
            Severity.CRITICAL: 4,
        }
        return order[self]
