"""
customer.py - SWE30003 - Assignment 3 - Michael Attardi, 102096755
"""
import json
from datetime import datetime

# Path to the invoices JSON file
DATA_FILE = "data/invoices.json"


class Invoice:
    """
    A permanent record of a confirmed order's transaction details.
    Created from an Order once it is confirmed, and holds a snapshot
    of all pricing so the record never changes even if book prices do.

        Responsibilities (from CRC):
        - Generate invoice from order details
        - Display list of books with quantities and prices
        - Show subtotal, tax, and total amount
        - Reference the associated order ID
        - Provide a unique invoice number
        - Provide invoice data to SalesReport
    """

    def __init__(self, order_id, customer_id, customer_name, customer_address,
                 items, subtotal, gst, total, invoice_id=None, created_at=None,
                 status="unpaid"):
        self.invoice_id = invoice_id or Invoice._generate_id()
        self.order_id = order_id
        self.customer_id = customer_id
        self.customer_name = customer_name
        self.customer_address = customer_address
        self.items = items   # Snapshot: [{book_id, title, unit_price, quantity, line_total}]
        self.subtotal = subtotal
        self.gst = gst
        self.total = total
        self.created_at = created_at or datetime.now().isoformat()
        self.status = status  # unpaid -> paid

    @staticmethod
    def _generate_id():
        """Generates the next invoice ID in INV#### format."""
        invoices = Invoice.load_all()
        if not invoices:
            return "INV0001"
        nums = []
        for inv in invoices:
            if inv.invoice_id.startswith("INV") and inv.invoice_id[3:].isdigit():
                nums.append(int(inv.invoice_id[3:]))
        next_num = max(nums) + 1 if nums else 1
        return f"INV{next_num:04d}"

    @classmethod
    def from_order(cls, order, customer):
        """
        Creates and saves an Invoice from a confirmed Order and its Customer.
        Returns None if the order is not yet confirmed.
        """
        if order.status not in ("confirmed", "paid"):
            return None

        # Build items snapshot with line totals included
        items = [
            {
                "book_id": item["book_id"],
                "title": item["title"],
                "unit_price": item["unit_price"],
                "quantity": item["quantity"],
                "line_total": round(item["unit_price"] * item["quantity"], 2)
            }
            for item in order.items
        ]

        invoice = cls(
            order_id=order.order_id,
            customer_id=order.customer_id,
            customer_name=customer.name,
            customer_address=customer.address,
            items=items,
            subtotal=order.calculate_subtotal(),
            gst=order.calculate_tax(),
            total=order.calculate_total()
        )
        invoice.save()

        # Link the invoice ID back to the order
        order.invoice_id = invoice.invoice_id
        order.save()

        return invoice

    # Serialisation
    def to_dict(self):
        """Converts the invoice to a dictionary for JSON storage."""
        return {
            "invoice_id": self.invoice_id,
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "customer_address": self.customer_address,
            "items": self.items,
            "subtotal": self.subtotal,
            "gst": self.gst,
            "total": self.total,
            "created_at": self.created_at,
            "status": self.status
        }

    @classmethod
    def from_dict(cls, data):
        """Creates an Invoice instance from a dictionary (e.g. loaded from JSON)."""
        return cls(
            invoice_id=data.get("invoice_id"),
            order_id=data.get("order_id"),
            customer_id=data.get("customer_id"),
            customer_name=data.get("customer_name", ""),
            customer_address=data.get("customer_address", ""),
            items=data.get("items", []),
            subtotal=data.get("subtotal"),
            gst=data.get("gst"),
            total=data.get("total"),
            created_at=data.get("created_at"),
            status=data.get("status", "unpaid")
        )

    # JSON persistence helpers
    @staticmethod
    def load_all():
        """Loads all invoices from the JSON file. Returns a list of Invoice objects."""
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
            return [Invoice.from_dict(i) for i in data]
        except FileNotFoundError:
            return []

    @staticmethod
    def save_all(invoices):
        """Saves a list of Invoice objects to the JSON file."""
        with open(DATA_FILE, 'w') as f:
            json.dump([i.to_dict() for i in invoices], f, indent=2)

    @staticmethod
    def find_by_id(invoice_id):
        """Finds and returns a single Invoice by ID, or None if not found."""
        for invoice in Invoice.load_all():
            if invoice.invoice_id == invoice_id:
                return invoice
        return None

    @staticmethod
    def find_by_order(order_id):
        """Returns the invoice associated with a given order, or None."""
        for invoice in Invoice.load_all():
            if invoice.order_id == order_id:
                return invoice
        return None

    def save(self):
        """Saves or updates this invoice in the JSON file."""
        invoices = Invoice.load_all()

        # Replace existing entry if it exists, otherwise append
        for i, inv in enumerate(invoices):
            if inv.invoice_id == self.invoice_id:
                invoices[i] = self
                Invoice.save_all(invoices)
                return

        invoices.append(self)
        Invoice.save_all(invoices)
