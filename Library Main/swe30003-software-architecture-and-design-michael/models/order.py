"""
order.py - SWE30003 - Assignment 3 - Michael Attardi, 102096755
"""
import json
from datetime import datetime

# Path to the orders JSON file
DATA_FILE = "data/orders.json"

# Tax rate applied to all orders
TAX_RATE = 0.10


class Order:
    """
    Represents a customer's purchase.
    Holds the list of books being bought, tracks order status,
    and calculates pricing including tax.

        Responsibilities (from CRC):
        - Create new order
        - Add book with quantity to order
        - Remove book from order
        - Update quantity of a book in order
        - Calculate order subtotal and total
        - Confirm order
        - Process payment (stubbed as per assignment spec)
        - Update payment status
    """

    def __init__(self, customer_id, order_id=None, items=None,
                 status="pending", created_at=None, invoice_id=None):
        self.order_id = order_id or Order._generate_id()
        self.customer_id = customer_id
        self.items = items or []  # Each item: {book_id, title, unit_price, quantity}
        self.status = status      # pending -> confirmed -> paid
        self.created_at = created_at or datetime.now().isoformat()
        self.invoice_id = invoice_id  # Set once an invoice is generated

    @staticmethod
    def _generate_id():
        """Generates the next order ID in ORD#### format."""
        orders = Order.load_all()
        if not orders:
            return "ORD0001"
        nums = []
        for o in orders:
            if o.order_id.startswith("ORD") and o.order_id[3:].isdigit():
                nums.append(int(o.order_id[3:]))
        next_num = max(nums) + 1 if nums else 1
        return f"ORD{next_num:04d}"

    # Item management
    def add_item(self, book, quantity=1):
        """
        Adds a book to the order, or increases quantity if already present.
        Expects a Book object and an integer quantity.
        Returns False if there is insufficient stock, True on success.
        """
        for item in self.items:
            if item["book_id"] == book.book_id:
                if book.stock < item["quantity"] + quantity:
                    return False
                item["quantity"] += quantity
                return True

        if book.stock < quantity:
            return False

        self.items.append({
            "book_id": book.book_id,
            "title": book.title,
            "unit_price": book.price,
            "quantity": quantity
        })
        return True

    def remove_item(self, book_id):
        """Removes an item from the order by book ID."""
        self.items = [item for item in self.items if item["book_id"] != book_id]

    def update_quantity(self, book_id, quantity):
        """Updates the quantity of an existing item. Removes it if quantity is 0."""
        if quantity <= 0:
            self.remove_item(book_id)
            return

        for item in self.items:
            if item["book_id"] == book_id:
                item["quantity"] = quantity
                return

    # Pricing
    def calculate_subtotal(self):
        """Returns the total price of all items before tax."""
        return sum(item["unit_price"] * item["quantity"] for item in self.items)

    def calculate_tax(self):
        """Returns the tax amount based on the subtotal."""
        return round(self.calculate_subtotal() * TAX_RATE, 2)

    def calculate_total(self):
        """Returns the final total including tax."""
        return round(self.calculate_subtotal() + self.calculate_tax(), 2)

    # Status transitions

    def confirm(self):
        """Marks the order as confirmed. Returns False if the order has no items or stock is insufficient."""
        if not self.items:
            return False

        from models.book import Book

        for item in self.items:
            book = Book.find_by_id(item["book_id"])
            if not book or book.stock < item["quantity"]:
                return False

        for item in self.items:
            book = Book.find_by_id(item["book_id"])
            book.stock -= item["quantity"]
            book.save()

        self.status = "confirmed"
        return True

    def mark_as_paid(self):
        """Marks a confirmed order as paid."""
        self.status = "paid"

    # Serialisation
    def to_dict(self):
        """Converts the order to a dictionary for JSON storage."""
        return {
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "items": self.items,
            "status": self.status,
            "created_at": self.created_at,
            "invoice_id": self.invoice_id
        }

    @classmethod
    def from_dict(cls, data):
        """Creates an Order instance from a dictionary (e.g. loaded from JSON)."""
        return cls(
            order_id=data.get("order_id"),
            customer_id=data.get("customer_id"),
            items=data.get("items", []),
            status=data.get("status", "pending"),
            created_at=data.get("created_at"),
            invoice_id=data.get("invoice_id")
        )

    # JSON persistence helpers
    @staticmethod
    def load_all():
        """Loads all orders from the JSON file. Returns a list of Order objects."""
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
            return [Order.from_dict(o) for o in data]
        except FileNotFoundError:
            return []

    @staticmethod
    def save_all(orders):
        """Saves a list of Order objects to the JSON file."""
        with open(DATA_FILE, 'w') as f:
            json.dump([o.to_dict() for o in orders], f, indent=2)

    @staticmethod
    def find_by_id(order_id):
        """Finds and returns a single Order by ID, or None if not found."""
        for order in Order.load_all():
            if order.order_id == order_id:
                return order
        return None

    @staticmethod
    def find_by_customer(customer_id):
        """Returns all orders belonging to a given customer."""
        return [o for o in Order.load_all() if o.customer_id == customer_id]

    def save(self):
        """Saves or updates this order in the JSON file."""
        orders = Order.load_all()

        # Replace existing entry if it exists, otherwise append
        for i, o in enumerate(orders):
            if o.order_id == self.order_id:
                orders[i] = self
                Order.save_all(orders)
                return

        orders.append(self)
        Order.save_all(orders)