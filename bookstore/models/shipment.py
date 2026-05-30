"""
shipment.py - Shipment model for the Online Bookstore System.

Represents the delivery of a packaged order, including tracking
information and status updates.
Follows the CRC design from Assignment 2 (Section 3.3.8).

Coding standard: PEP 8 (https://peps.python.org/pep-0008/)
"""

import json
import os
from datetime import datetime, timedelta

SHIPMENTS_FILE = "storage/shipments.json"

# Shipment status constants
STATUS_PENDING = "pending"
STATUS_PACKAGED = "packaged"
STATUS_DISPATCHED = "dispatched"
STATUS_DELIVERED = "delivered"

VALID_STATUSES = [
    STATUS_PENDING,
    STATUS_PACKAGED,
    STATUS_DISPATCHED,
    STATUS_DELIVERED,
]


class Shipment:
    """
    Represents the delivery record for a confirmed, paid order.

    Responsibilities (from CRC):
        - Create shipment record for an order
        - Assign unique shipment ID to each order
        - Store tracking number
        - Update shipment status
        - Show estimated delivery date
        - Store actual delivery date
    """

    def __init__(self, shipment_id, order_id, customer_id,
                 customer_name, customer_address,
                 tracking_number=None,
                 status=STATUS_PENDING,
                 estimated_delivery=None,
                 actual_delivery=None,
                 created_at=None):
        """
        Initialise a Shipment.

        Args:
            shipment_id (str): Unique shipment identifier.
            order_id (str): Associated order ID.
            customer_id (str): Customer receiving the shipment.
            customer_name (str): Recipient name.
            customer_address (str): Delivery address.
            tracking_number (str, optional): Courier tracking code.
            status (str): Current shipment status.
            estimated_delivery (str, optional): ISO date estimate.
            actual_delivery (str, optional): ISO date of delivery.
            created_at (str, optional): ISO timestamp of creation.
        """
        self._shipment_id = shipment_id
        self._order_id = order_id
        self._customer_id = customer_id
        self._customer_name = customer_name
        self._customer_address = customer_address
        self._tracking_number = tracking_number
        self._status = status
        self._estimated_delivery = estimated_delivery
        self._actual_delivery = actual_delivery
        self._created_at = created_at or datetime.now().isoformat()

    # ------------------------------------------------------------------ #
    # Properties                                                           #
    # ------------------------------------------------------------------ #

    @property
    def shipment_id(self):
        return self._shipment_id

    @property
    def order_id(self):
        return self._order_id

    @property
    def customer_id(self):
        return self._customer_id

    @property
    def status(self):
        return self._status

    @property
    def tracking_number(self):
        return self._tracking_number

    @property
    def estimated_delivery(self):
        return self._estimated_delivery

    # ------------------------------------------------------------------ #
    # Responsibilities                                                     #
    # ------------------------------------------------------------------ #

    def assign_tracking_number(self, tracking_number):
        """
        Set the courier tracking number for this shipment.

        Args:
            tracking_number (str): Tracking code from courier.

        Raises:
            ValueError: If tracking number is blank.
        """
        tracking_number = tracking_number.strip()
        if not tracking_number:
            raise ValueError("Tracking number cannot be empty.")
        self._tracking_number = tracking_number

    def update_status(self, new_status):
        """
        Update the shipment status.

        Args:
            new_status (str): One of the VALID_STATUSES.

        Raises:
            ValueError: If the status value is not valid.
        """
        if new_status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status '{new_status}'. "
                f"Valid values: {VALID_STATUSES}"
            )
        self._status = new_status
        if new_status == STATUS_DELIVERED:
            self._actual_delivery = datetime.now().isoformat()

    def display(self):
        """Print a formatted shipment record."""
        line = "=" * 62
        thin = "-" * 62
        print(line)
        print("          FAVOURITE BOOKS - SHIPMENT RECORD")
        print(line)
        print(f"  Shipment ID   : {self._shipment_id}")
        print(f"  Order ID      : {self._order_id}")
        print(f"  Created       : {self._created_at[:10]}")
        print(thin)
        print(f"  Recipient     : {self._customer_name}")
        print(f"  Address       : {self._customer_address}")
        print(thin)
        tracking = self._tracking_number or "Not yet assigned"
        print(f"  Tracking No.  : {tracking}")
        print(f"  Status        : {self._status.upper()}")
        if self._estimated_delivery:
            print(f"  Est. Delivery : {self._estimated_delivery[:10]}")
        if self._actual_delivery:
            print(f"  Delivered On  : {self._actual_delivery[:10]}")
        print(line)

    # ------------------------------------------------------------------ #
    # Serialisation                                                        #
    # ------------------------------------------------------------------ #

    def to_dict(self):
        """Serialise to dictionary for JSON persistence."""
        return {
            "shipment_id": self._shipment_id,
            "order_id": self._order_id,
            "customer_id": self._customer_id,
            "customer_name": self._customer_name,
            "customer_address": self._customer_address,
            "tracking_number": self._tracking_number,
            "status": self._status,
            "estimated_delivery": self._estimated_delivery,
            "actual_delivery": self._actual_delivery,
            "created_at": self._created_at,
        }

    @classmethod
    def from_dict(cls, data):
        """Deserialise a Shipment from a dictionary."""
        return cls(
            shipment_id=data["shipment_id"],
            order_id=data["order_id"],
            customer_id=data["customer_id"],
            customer_name=data["customer_name"],
            customer_address=data["customer_address"],
            tracking_number=data.get("tracking_number"),
            status=data.get("status", STATUS_PENDING),
            estimated_delivery=data.get("estimated_delivery"),
            actual_delivery=data.get("actual_delivery"),
            created_at=data.get("created_at"),
        )

    def __repr__(self):
        return (
            f"Shipment(id={self._shipment_id!r}, "
            f"order={self._order_id!r}, status={self._status!r})"
        )


# ------------------------------------------------------------------ #
# Module-level helpers                                                #
# ------------------------------------------------------------------ #

def _generate_shipment_id(existing_shipments):
    """Generate a sequential shipment ID (e.g. SHIP0001)."""
    count = len(existing_shipments) + 1
    return f"SHIP{count:04d}"


def load_shipments():
    """
    Load all shipments from storage.

    Returns:
        dict[str, Shipment]: shipment_id -> Shipment.
    """
    if not os.path.exists(SHIPMENTS_FILE):
        return {}
    with open(SHIPMENTS_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return {
        item["shipment_id"]: Shipment.from_dict(item)
        for item in raw
    }


def save_shipments(shipments):
    """
    Persist all shipments to storage.

    Args:
        shipments (dict[str, Shipment]): shipment_id -> Shipment.
    """
    os.makedirs(os.path.dirname(SHIPMENTS_FILE), exist_ok=True)
    data = [s.to_dict() for s in shipments.values()]
    with open(SHIPMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def create_shipment_from_order(order, customer, shipments):
    """
    Create a Shipment record from a paid Order.

    Args:
        order (Order): The paid order.
        customer (Customer): The customer who placed the order.
        shipments (dict): Existing shipments.

    Returns:
        Shipment: The newly created Shipment.

    Raises:
        ValueError: If order is not in paid status.
    """
    from models.order import STATUS_PAID
    if order.status != STATUS_PAID:
        raise ValueError("Shipment can only be created for paid orders.")

    estimated = (
        datetime.now() + timedelta(days=5)
    ).strftime("%Y-%m-%d")

    shipment_id = _generate_shipment_id(shipments)
    shipment = Shipment(
        shipment_id=shipment_id,
        order_id=order.order_id,
        customer_id=customer.customer_id,
        customer_name=customer.name,
        customer_address=customer.address,
        estimated_delivery=estimated,
    )
    shipments[shipment_id] = shipment
    save_shipments(shipments)
    return shipment
