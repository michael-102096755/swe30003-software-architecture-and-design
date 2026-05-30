"""
order.py - Order class for the Online Bookstore System
Coding standard: PEP 8 (https://peps.python.org/pep-0008/)

Implements:
  - Observer pattern (Subject side): notifies observers on status change
  - Strategy pattern (Context): delegates payment to PaymentStrategy
CRC Reference: Section 3.3.2
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional

from book import Book
from invoice import Invoice
from payment import PaymentStrategy


class OrderObserver:
    """
    Abstract observer for order status changes.
    Observer Pattern: Observer role. CRC Reference: Section 5.2.2
    """

    def on_order_status_changed(self, order_id: str, new_status: str):
        """Called when the observed order changes status."""
        raise NotImplementedError


class Order:
    """
    Represents a customer's purchase. Acts as shopping cart until confirmed.
    Manages books/quantities, calculates totals, processes payment,
    and generates an Invoice on confirmation.

    Relationships:
        - Many:1 with Customer (a customer can have many orders)
        - M:M with Book (order contains multiple books)
        - 1:1 with Invoice (generates one invoice on confirmation)

    Design patterns:
        - Observer (Subject): notifies observers on status change
        - Strategy (Context): uses PaymentStrategy for payment
    CRC Reference: Section 3.3.2
    """

    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_PAID = "paid"
    STATUS_CANCELLED = "cancelled"

    SHIPPING_COST = 9.95   # flat-rate shipping (AUD)
    TAX_RATE = 0.10        # 10% GST

    def __init__(self, customer_id: str, customer_name: str,
                 customer_email: str, shipping_address: str):
        """
        Create a new order for the given customer.

        Args:
            customer_id: ID of the owning customer.
            customer_name: Customer's full name (for invoice).
            customer_email: Customer's email (for invoice).
            shipping_address: Delivery address.
        """
        self._order_id = str(uuid.uuid4())[:8].upper()
        self._customer_id = customer_id
        self._customer_name = customer_name
        self._customer_email = customer_email
        self._shipping_address = shipping_address
        self._items: Dict[str, dict] = {}   # isbn -> {book, quantity}
        self._status = self.STATUS_PENDING
        self._created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._invoice: Optional[Invoice] = None
        self._payment_method: Optional[str] = None
        self._observers: List[OrderObserver] = []

    # --- Observer pattern ---

    def add_observer(self, observer: OrderObserver):
        """Register an observer to be notified of status changes."""
        self._observers.append(observer)

    def _notify_observers(self):
        """Notify all registered observers of the current status."""
        for observer in self._observers:
            observer.on_order_status_changed(self._order_id, self._status)

    # --- Item management ---

    def add_book(self, book: Book, quantity: int) -> bool:
        """
        Add a book (or increase its quantity) in the order.

        Args:
            book: Book to add.
            quantity: Number of copies to add (must be >= 1).

        Returns:
            True if added successfully, False if out of stock or wrong status.
        """
        if self._status != self.STATUS_PENDING:
            print("  Cannot modify a confirmed or cancelled order.")
            return False
        if quantity < 1:
            print("  Quantity must be at least 1.")
            return False
        if not book.is_available():
            print(f"  '{book.title}' is currently out of stock.")
            return False

        if book.isbn in self._items:
            new_qty = self._items[book.isbn]["quantity"] + quantity
            if new_qty > book.stock:
                print(f"  Only {book.stock} copies of '{book.title}' available.")
                return False
            self._items[book.isbn]["quantity"] = new_qty
        else:
            if quantity > book.stock:
                print(f"  Only {book.stock} copies of '{book.title}' available.")
                return False
            self._items[book.isbn] = {"book": book, "quantity": quantity}
        return True

    def remove_book(self, isbn: str) -> bool:
        """
        Remove a book entirely from the order.

        Returns:
            True if removed, False if not in order.
        """
        if self._status != self.STATUS_PENDING:
            print("  Cannot modify a confirmed or cancelled order.")
            return False
        if isbn in self._items:
            del self._items[isbn]
            return True
        return False

    def update_quantity(self, isbn: str, quantity: int) -> bool:
        """
        Update the quantity of a book already in the order.
        Setting quantity to 0 removes the item.

        Args:
            isbn: ISBN of the book to update.
            quantity: New quantity (0 to remove).

        Returns:
            True if updated, False if book not in order or invalid quantity.
        """
        if self._status != self.STATUS_PENDING:
            print("  Cannot modify a confirmed or cancelled order.")
            return False
        if isbn not in self._items:
            print("  That book is not in your order.")
            return False
        if quantity < 0:
            print("  Quantity cannot be negative.")
            return False
        if quantity == 0:
            return self.remove_book(isbn)
        book = self._items[isbn]["book"]
        if quantity > book.stock:
            print(f"  Only {book.stock} copies of '{book.title}' available.")
            return False
        self._items[isbn]["quantity"] = quantity
        return True

    # --- Calculations ---

    def calculate_subtotal(self) -> float:
        """Calculate subtotal (before tax and shipping)."""
        return round(
            sum(entry["book"].price * entry["quantity"]
                for entry in self._items.values()), 2
        )

    def calculate_tax(self) -> float:
        """Calculate GST (10%) on the subtotal."""
        return round(self.calculate_subtotal() * self.TAX_RATE, 2)

    def calculate_total(self) -> float:
        """Calculate total including tax and shipping."""
        return round(
            self.calculate_subtotal() + self.calculate_tax() + self.SHIPPING_COST, 2
        )

    # --- Order workflow ---

    def confirm_order(self) -> bool:
        """
        Confirm the order (moves from pending to confirmed).
        Requires at least one item in the order.

        Returns:
            True if confirmed, False if empty or wrong status.
        """
        if self._status != self.STATUS_PENDING:
            print("  Order is not in a pending state.")
            return False
        if not self._items:
            print("  Cannot confirm an empty order.")
            return False
        self._status = self.STATUS_CONFIRMED
        self._notify_observers()
        return True

    def process_payment(self, strategy: PaymentStrategy) -> bool:
        """
        Process payment using the provided PaymentStrategy.
        On success, deducts stock and generates an Invoice.

        Args:
            strategy: A PaymentStrategy instance (Strategy pattern).

        Returns:
            True if payment succeeded and invoice generated.
        """
        if self._status != self.STATUS_CONFIRMED:
            print("  Order must be confirmed before payment.")
            return False

        success = strategy.process(self.calculate_total(), self._customer_name)
        if success:
            self._payment_method = strategy.get_name()
            # Deduct stock from each book
            for entry in self._items.values():
                entry["book"].reduce_stock(entry["quantity"])
            self._status = self.STATUS_PAID
            self._invoice = self._generate_invoice()
            self._notify_observers()
            return True
        return False

    def cancel_order(self) -> bool:
        """
        Cancel the order. If paid, stock is restored.

        Returns:
            True if cancelled, False if already cancelled.
        """
        if self._status == self.STATUS_CANCELLED:
            return False
        if self._status == self.STATUS_PAID:
            # Restore stock
            for entry in self._items.values():
                entry["book"].restore_stock(entry["quantity"])
        self._status = self.STATUS_CANCELLED
        self._notify_observers()
        return True

    def _generate_invoice(self) -> Invoice:
        """Create and return an Invoice for this paid order."""
        items = [
            (isbn,
             entry["book"].title,
             entry["quantity"],
             entry["book"].price)
            for isbn, entry in self._items.items()
        ]
        return Invoice(
            order_id=self._order_id,
            customer_name=self._customer_name,
            customer_email=self._customer_email,
            items=items,
            shipping_address=self._shipping_address,
        )

    # --- Getters ---

    @property
    def order_id(self) -> str:
        return self._order_id

    @property
    def customer_id(self) -> str:
        return self._customer_id

    @property
    def status(self) -> str:
        return self._status

    @property
    def invoice(self) -> Optional[Invoice]:
        return self._invoice

    @property
    def items(self) -> dict:
        return dict(self._items)

    @property
    def created_at(self) -> str:
        return self._created_at

    @property
    def shipping_address(self) -> str:
        return self._shipping_address

    def display_summary(self) -> str:
        """Return a short order summary string."""
        return (
            f"Order #{self._order_id} | Status: {self._status.upper()} "
            f"| {len(self._items)} item(s) | Total: ${self.calculate_total():.2f} "
            f"| {self._created_at}"
        )

    def display_cart(self) -> str:
        """Return a formatted cart/order details string."""
        if not self._items:
            return "  (Your order is empty)"
        lines = [
            "-" * 55,
            f"  Order #{self._order_id}  |  Status: {self._status.upper()}",
            "-" * 55,
            f"  {'Title':<28} {'Qty':>4} {'Unit':>7} {'Line':>8}",
            "-" * 55,
        ]
        for entry in self._items.values():
            b = entry["book"]
            qty = entry["quantity"]
            short = b.title[:26] + ".." if len(b.title) > 28 else b.title
            lines.append(
                f"  {short:<28} {qty:>4} ${b.price:>6.2f} "
                f"${qty * b.price:>7.2f}"
            )
        lines += [
            "-" * 55,
            f"  {'Subtotal:':<40} ${self.calculate_subtotal():>8.2f}",
            f"  {'GST (10%):':<40} ${self.calculate_tax():>8.2f}",
            f"  {'Shipping:':<40} ${self.SHIPPING_COST:>8.2f}",
            f"  {'TOTAL (AUD):':<40} ${self.calculate_total():>8.2f}",
            "-" * 55,
        ]
        return "\n".join(lines)

    # --- Serialisation ---

    def to_dict(self) -> dict:
        """Serialise order to a dictionary for JSON storage."""
        return {
            "order_id": self._order_id,
            "customer_id": self._customer_id,
            "customer_name": self._customer_name,
            "customer_email": self._customer_email,
            "shipping_address": self._shipping_address,
            "status": self._status,
            "created_at": self._created_at,
            "payment_method": self._payment_method,
            "items": [
                {
                    "isbn": isbn,
                    "title": entry["book"].title,
                    "quantity": entry["quantity"],
                    "price": entry["book"].price,
                }
                for isbn, entry in self._items.items()
            ],
            "invoice": self._invoice.to_dict() if self._invoice else None,
        }

    @classmethod
    def from_dict(cls, data: dict, catalogue) -> "Order":
        """
        Deserialise an Order from a dictionary.
        Books are resolved from the catalogue by ISBN.
        """
        order = cls.__new__(cls)
        order._order_id = data["order_id"]
        order._customer_id = data["customer_id"]
        order._customer_name = data["customer_name"]
        order._customer_email = data["customer_email"]
        order._shipping_address = data["shipping_address"]
        order._status = data["status"]
        order._created_at = data["created_at"]
        order._payment_method = data.get("payment_method")
        order._observers = []

        # Rebuild items — attempt to link to live Book objects from catalogue
        order._items = {}
        for item in data.get("items", []):
            book = catalogue.get_book_by_isbn(item["isbn"])
            if book:
                order._items[item["isbn"]] = {
                    "book": book,
                    "quantity": item["quantity"],
                }

        invoice_data = data.get("invoice")
        order._invoice = (Invoice.from_dict(invoice_data)
                          if invoice_data else None)
        return order
