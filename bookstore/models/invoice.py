"""
invoice.py - Invoice model for the Online Bookstore System.

A data-holder representing the pre-payment document generated from an Order.
Follows the CRC design from Assignment 2 (Section 3.3.3).

Coding standard: PEP 8 (https://peps.python.org/pep-0008/)
"""

import json
import os
from datetime import datetime

INVOICES_FILE = "storage/invoices.json"
GST_RATE = 0.10  # Australian GST at 10%


class Invoice:
    """
    Data-holder class for a completed transaction document.

    Responsibilities (from CRC):
        - Generate invoice from order details
        - Display list of books with quantities and prices
        - Show subtotal, tax, and total amount
        - Reference the associated order ID
        - Provide a unique invoice number
        - Provide invoice data to SalesReport
    """

    def __init__(self, invoice_id, order_id, customer_id,
                 customer_name, customer_address,
                 items, subtotal, gst, total,
                 created_at=None, status="unpaid"):
        """
        Initialise an Invoice.

        Args:
            invoice_id (str): Unique invoice identifier.
            order_id (str): Associated order ID.
            customer_id (str): Customer who placed the order.
            customer_name (str): Customer's full name.
            customer_address (str): Delivery address.
            items (list[dict]): Line items with book_id, title,
                                quantity, unit_price, line_total.
            subtotal (float): Total before GST.
            gst (float): GST amount (10%).
            total (float): Grand total including GST.
            created_at (str, optional): ISO timestamp of creation.
            status (str): Payment status ('unpaid' or 'paid').
        """
        self._invoice_id = invoice_id
        self._order_id = order_id
        self._customer_id = customer_id
        self._customer_name = customer_name
        self._customer_address = customer_address
        self._items = items
        self._subtotal = subtotal
        self._gst = gst
        self._total = total
        self._created_at = created_at or datetime.now().isoformat()
        self._status = status

    # ------------------------------------------------------------------ #
    # Properties                                                           #
    # ------------------------------------------------------------------ #

    @property
    def invoice_id(self):
        return self._invoice_id

    @property
    def order_id(self):
        return self._order_id

    @property
    def customer_id(self):
        return self._customer_id

    @property
    def total(self):
        return self._total

    @property
    def status(self):
        return self._status

    @property
    def created_at(self):
        return self._created_at

    # ------------------------------------------------------------------ #
    # Responsibilities                                                     #
    # ------------------------------------------------------------------ #

    def mark_paid(self):
        """Mark the invoice as paid after successful payment."""
        self._status = "paid"

    def display(self):
        """Print a formatted invoice to the console."""
        line = "=" * 62
        thin = "-" * 62
        print(line)
        print("          FAVOURITE BOOKS - ONLINE BOOKSTORE")
        print("               Tax Invoice / Receipt")
        print(line)
        print(f"  Invoice No : {self._invoice_id}")
        print(f"  Order ID   : {self._order_id}")
        created = self._created_at[:10]
        print(f"  Date       : {created}")
        print(f"  Status     : {self._status.upper()}")
        print(thin)
        print(f"  Bill To    : {self._customer_name}")
        print(f"  Address    : {self._customer_address}")
        print(thin)
        print(f"  {'Title':<36} {'Qty':>4}  {'Unit':>8}  {'Total':>9}")
        print(f"  {'-'*36}  {'-'*4}  {'-'*8}  {'-'*9}")
        for item in self._items:
            title = item["title"]
            if len(title) > 36:
                title = title[:33] + "..."
            print(
                f"  {title:<36} {item['quantity']:>4}  "
                f"${item['unit_price']:>7.2f}  "
                f"${item['line_total']:>8.2f}"
            )
        print(thin)
        print(f"  {'Subtotal (excl. GST)':<48} ${self._subtotal:>8.2f}")
        print(f"  {'GST (10%)':<48} ${self._gst:>8.2f}")
        print(f"  {'TOTAL (AUD)':<48} ${self._total:>8.2f}")
        print(line)

    # ------------------------------------------------------------------ #
    # Serialisation                                                        #
    # ------------------------------------------------------------------ #

    def to_dict(self):
        """Serialise to dictionary for JSON persistence."""
        return {
            "invoice_id": self._invoice_id,
            "order_id": self._order_id,
            "customer_id": self._customer_id,
            "customer_name": self._customer_name,
            "customer_address": self._customer_address,
            "items": self._items,
            "subtotal": self._subtotal,
            "gst": self._gst,
            "total": self._total,
            "created_at": self._created_at,
            "status": self._status,
        }

    @classmethod
    def from_dict(cls, data):
        """Deserialise an Invoice from a dictionary."""
        return cls(
            invoice_id=data["invoice_id"],
            order_id=data["order_id"],
            customer_id=data["customer_id"],
            customer_name=data["customer_name"],
            customer_address=data["customer_address"],
            items=data["items"],
            subtotal=data["subtotal"],
            gst=data["gst"],
            total=data["total"],
            created_at=data.get("created_at"),
            status=data.get("status", "unpaid"),
        )

    def __repr__(self):
        return (
            f"Invoice(id={self._invoice_id!r}, "
            f"order={self._order_id!r}, total={self._total:.2f})"
        )


# ------------------------------------------------------------------ #
# Module-level helpers                                                #
# ------------------------------------------------------------------ #

def _generate_invoice_id(existing_invoices):
    """Generate a sequential invoice ID (e.g. INV0001)."""
    count = len(existing_invoices) + 1
    return f"INV{count:04d}"


def load_invoices():
    """
    Load all invoices from storage.

    Returns:
        dict[str, Invoice]: invoice_id -> Invoice.
    """
    if not os.path.exists(INVOICES_FILE):
        return {}
    with open(INVOICES_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return {item["invoice_id"]: Invoice.from_dict(item) for item in raw}


def save_invoices(invoices):
    """
    Persist all invoices to storage.

    Args:
        invoices (dict[str, Invoice]): invoice_id -> Invoice.
    """
    os.makedirs(os.path.dirname(INVOICES_FILE), exist_ok=True)
    data = [inv.to_dict() for inv in invoices.values()]
    with open(INVOICES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def create_invoice_from_order(order, customer, invoices):
    """
    Create and persist an Invoice from a confirmed Order.

    Args:
        order: A confirmed Order instance.
        customer: The Customer who placed the order.
        invoices (dict): Existing invoices.

    Returns:
        Invoice: The newly created Invoice.
    """
    items = []
    for item in order.items:
        line_total = round(item["quantity"] * item["unit_price"], 2)
        items.append({
            "book_id": item["book_id"],
            "title": item["title"],
            "quantity": item["quantity"],
            "unit_price": item["unit_price"],
            "line_total": line_total,
        })

    subtotal = round(order.subtotal, 2)
    gst = round(subtotal * GST_RATE, 2)
    total = round(subtotal + gst, 2)

    invoice_id = _generate_invoice_id(invoices)
    invoice = Invoice(
        invoice_id=invoice_id,
        order_id=order.order_id,
        customer_id=customer.customer_id,
        customer_name=customer.name,
        customer_address=customer.address,
        items=items,
        subtotal=subtotal,
        gst=gst,
        total=total,
    )
    invoices[invoice_id] = invoice
    save_invoices(invoices)
    return invoice
