"""
invoice.py - Invoice class for the Online Bookstore System
Coding standard: PEP 8 (https://peps.python.org/pep-0008/)
"""

import uuid
from datetime import datetime
from typing import List, Tuple


class Invoice:
    """
    Data-holder class representing the document generated from a confirmed Order.
    Contains order details, items with quantities and prices, and total amount.
    CRC Reference: Section 3.3.3

    Relationships:
        - 1:1 with Order (generated from one order)
        - Many:1 with SalesReport (a report analyses many invoices)
    """

    TAX_RATE = 0.10  # 10% GST (Australia)

    def __init__(self, order_id: str, customer_name: str,
                 customer_email: str, items: List[Tuple[str, str, int, float]],
                 shipping_address: str):
        """
        Initialise an Invoice from order details.

        Args:
            order_id: The associated order's ID.
            customer_name: Full name of the customer.
            customer_email: Email address of the customer.
            items: List of (isbn, title, quantity, unit_price) tuples.
            shipping_address: Delivery address for the order.
        """
        self._invoice_id = str(uuid.uuid4())[:8].upper()
        self._order_id = order_id
        self._customer_name = customer_name
        self._customer_email = customer_email
        self._items = items  # (isbn, title, qty, unit_price)
        self._shipping_address = shipping_address
        self._created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._subtotal = self._calculate_subtotal()
        self._tax = round(self._subtotal * self.TAX_RATE, 2)
        self._total = round(self._subtotal + self._tax, 2)

    def _calculate_subtotal(self) -> float:
        """Calculate the subtotal from all line items."""
        return round(sum(qty * price for _, _, qty, price in self._items), 2)

    # --- Getters ---

    @property
    def invoice_id(self) -> str:
        return self._invoice_id

    @property
    def order_id(self) -> str:
        return self._order_id

    @property
    def subtotal(self) -> float:
        return self._subtotal

    @property
    def tax(self) -> float:
        return self._tax

    @property
    def total(self) -> float:
        return self._total

    @property
    def created_at(self) -> str:
        return self._created_at

    # --- Display ---

    def display(self) -> str:
        """Return a formatted invoice string for display."""
        lines = [
            "=" * 55,
            "         FAVOURITE BOOKS - TAX INVOICE",
            "=" * 55,
            f"  Invoice #:    {self._invoice_id}",
            f"  Order #:      {self._order_id}",
            f"  Date:         {self._created_at}",
            f"  Customer:     {self._customer_name}",
            f"  Email:        {self._customer_email}",
            f"  Ship to:      {self._shipping_address}",
            "-" * 55,
            f"  {'Title':<28} {'Qty':>4} {'Unit':>7} {'Line':>8}",
            "-" * 55,
        ]
        for isbn, title, qty, price in self._items:
            short_title = title[:26] + ".." if len(title) > 28 else title
            line_total = qty * price
            lines.append(
                f"  {short_title:<28} {qty:>4} ${price:>6.2f} ${line_total:>7.2f}"
            )
        lines += [
            "-" * 55,
            f"  {'Subtotal:':<40} ${self._subtotal:>8.2f}",
            f"  {'GST (10%):':<40} ${self._tax:>8.2f}",
            f"  {'TOTAL (AUD):':<40} ${self._total:>8.2f}",
            "=" * 55,
            "  Payment status: PAID",
            "=" * 55,
        ]
        return "\n".join(lines)

    # --- Serialisation ---

    def to_dict(self) -> dict:
        """Serialise invoice to a dictionary for JSON storage."""
        return {
            "invoice_id": self._invoice_id,
            "order_id": self._order_id,
            "customer_name": self._customer_name,
            "customer_email": self._customer_email,
            "items": [list(i) for i in self._items],
            "shipping_address": self._shipping_address,
            "created_at": self._created_at,
            "subtotal": self._subtotal,
            "tax": self._tax,
            "total": self._total,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Invoice":
        """Deserialise an Invoice from a dictionary."""
        inv = cls.__new__(cls)
        inv._invoice_id = data["invoice_id"]
        inv._order_id = data["order_id"]
        inv._customer_name = data["customer_name"]
        inv._customer_email = data["customer_email"]
        inv._items = [tuple(i) for i in data["items"]]
        inv._shipping_address = data["shipping_address"]
        inv._created_at = data["created_at"]
        inv._subtotal = data["subtotal"]
        inv._tax = data["tax"]
        inv._total = data["total"]
        return inv
