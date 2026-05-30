"""
order.py - Order model for the Online Bookstore System.

Represents a customer's purchase, containing books, quantities,
payment details, and coordinating with Invoice.
Follows the CRC design from Assignment 2 (Section 3.3.2).

Coding standard: PEP 8 (https://peps.python.org/pep-0008/)
"""

import json
import os
from datetime import datetime

ORDERS_FILE = "storage/orders.json"

# Valid order status transitions
STATUS_PENDING = "pending"
STATUS_CONFIRMED = "confirmed"
STATUS_PAID = "paid"
STATUS_CANCELLED = "cancelled"


class Order:
    """
    Represents a customer's purchase (combines cart + order per Ass2 CRC).

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

    def __init__(self, order_id, customer_id,
                 items=None, status=STATUS_PENDING,
                 created_at=None, invoice_id=None):
        """
        Initialise an Order.

        Args:
            order_id (str): Unique order identifier.
            customer_id (str): ID of the customer who owns the order.
            items (list[dict], optional): Line items. Each dict has:
                book_id, title, unit_price, quantity.
            status (str): Current order status.
            created_at (str, optional): ISO timestamp.
            invoice_id (str, optional): Linked invoice after confirmation.
        """
        self._order_id = order_id
        self._customer_id = customer_id
        self._items = items if items is not None else []
        self._status = status
        self._created_at = created_at or datetime.now().isoformat()
        self._invoice_id = invoice_id

    # ------------------------------------------------------------------ #
    # Properties                                                           #
    # ------------------------------------------------------------------ #

    @property
    def order_id(self):
        return self._order_id

    @property
    def customer_id(self):
        return self._customer_id

    @property
    def items(self):
        return list(self._items)

    @property
    def status(self):
        return self._status

    @property
    def created_at(self):
        return self._created_at

    @property
    def invoice_id(self):
        return self._invoice_id

    @property
    def subtotal(self):
        """Calculate and return the order subtotal (excl. GST)."""
        return sum(
            item["quantity"] * item["unit_price"]
            for item in self._items
        )

    # ------------------------------------------------------------------ #
    # Responsibilities                                                     #
    # ------------------------------------------------------------------ #

    def add_book(self, book, quantity):
        """
        Add a book (or increase quantity) in the order.

        Args:
            book (Book): The Book to add.
            quantity (int): Quantity to add (>= 1).

        Raises:
            ValueError: If order is not pending, or stock insufficient.
        """
        if self._status != STATUS_PENDING:
            raise ValueError("Cannot modify a non-pending order.")
        if quantity < 1:
            raise ValueError("Quantity must be at least 1.")
        if not book.is_available(quantity):
            raise ValueError(
                f"Only {book.stock} copies of '{book.title}' in stock."
            )

        # Check if book already in order
        for item in self._items:
            if item["book_id"] == book.book_id:
                new_qty = item["quantity"] + quantity
                if not book.is_available(new_qty):
                    raise ValueError(
                        f"Only {book.stock} copies available "
                        f"(you already have {item['quantity']} in cart)."
                    )
                item["quantity"] = new_qty
                return

        # New line item
        self._items.append({
            "book_id": book.book_id,
            "title": book.title,
            "unit_price": book.price,
            "quantity": quantity,
        })

    def remove_book(self, book_id, catalogue):
        """
        Remove a book line item from the order.

        Args:
            book_id (str): The book's ID to remove.
            catalogue (Catalogue): Used to restore stock.

        Raises:
            ValueError: If book not in order or order not pending.
        """
        if self._status != STATUS_PENDING:
            raise ValueError("Cannot modify a non-pending order.")
        for i, item in enumerate(self._items):
            if item["book_id"] == book_id:
                book = catalogue.get_book_by_id(book_id)
                if book:
                    book.restore_stock(item["quantity"])
                self._items.pop(i)
                return
        raise ValueError("Book not found in this order.")

    def update_quantity(self, book_id, new_quantity, catalogue):
        """
        Update the quantity of a book already in the order.

        Args:
            book_id (str): The book's ID.
            new_quantity (int): Desired new quantity (>= 1).
            catalogue (Catalogue): Used to check stock.

        Raises:
            ValueError: If quantity invalid or stock insufficient.
        """
        if self._status != STATUS_PENDING:
            raise ValueError("Cannot modify a non-pending order.")
        if new_quantity < 1:
            raise ValueError("Quantity must be at least 1.")

        book = catalogue.get_book_by_id(book_id)
        for item in self._items:
            if item["book_id"] == book_id:
                old_qty = item["quantity"]
                # Restore old stock first, then check new quantity
                if book:
                    book.restore_stock(old_qty)
                    if not book.is_available(new_quantity):
                        book.reduce_stock(old_qty)  # rollback
                        raise ValueError(
                            f"Only {book.stock + old_qty} copies available."
                        )
                item["quantity"] = new_quantity
                return
        raise ValueError("Book not found in this order.")

    def confirm_order(self, catalogue):
        """
        Confirm the order: deduct stock and set status to confirmed.

        Args:
            catalogue (Catalogue): Used to reduce book stock.

        Raises:
            ValueError: If order is empty or not pending.
        """
        if self._status != STATUS_PENDING:
            raise ValueError("Order is not in pending status.")
        if not self._items:
            raise ValueError("Cannot confirm an empty order.")

        for item in self._items:
            book = catalogue.get_book_by_id(item["book_id"])
            if book is None:
                raise ValueError(
                    f"Book '{item['book_id']}' not found in catalogue."
                )
            book.reduce_stock(item["quantity"])

        self._status = STATUS_CONFIRMED
        catalogue.save_books()

    def process_payment(self):
        """
        Stub payment processing (as per assignment spec).
        Marks the order as paid upon 'confirmation'.

        Returns:
            str: Payment result message.
        """
        if self._status != STATUS_CONFIRMED:
            raise ValueError(
                "Order must be confirmed before payment."
            )
        # Payment gateway interaction stubbed per assignment spec
        self._status = STATUS_PAID
        return (
            "Payment processed successfully via external gateway. "
            "Transaction ID: TXN" + self._order_id[-6:]
        )

    def cancel_order(self, catalogue):
        """
        Cancel the order and restore stock if already confirmed.

        Args:
            catalogue (Catalogue): Used to restore book stock.
        """
        if self._status == STATUS_PAID:
            raise ValueError("A paid order cannot be cancelled.")
        if self._status == STATUS_CONFIRMED:
            for item in self._items:
                book = catalogue.get_book_by_id(item["book_id"])
                if book:
                    book.restore_stock(item["quantity"])
            catalogue.save_books()
        self._status = STATUS_CANCELLED

    def set_invoice_id(self, invoice_id):
        """Link an invoice to this order after generation."""
        self._invoice_id = invoice_id

    def display(self):
        """Print a formatted summary of the order."""
        line = "=" * 62
        thin = "-" * 62
        print(line)
        print(f"  Order ID   : {self._order_id}")
        print(f"  Customer   : {self._customer_id}")
        print(f"  Date       : {self._created_at[:10]}")
        print(f"  Status     : {self._status.upper()}")
        if self._invoice_id:
            print(f"  Invoice    : {self._invoice_id}")
        print(thin)
        if not self._items:
            print("  (No items in this order)")
        else:
            print(f"  {'Title':<36} {'Qty':>4}  {'Unit':>8}  {'Total':>9}")
            print(f"  {'-'*36}  {'-'*4}  {'-'*8}  {'-'*9}")
            for item in self._items:
                title = item["title"]
                if len(title) > 36:
                    title = title[:33] + "..."
                line_total = item["quantity"] * item["unit_price"]
                print(
                    f"  {title:<36} {item['quantity']:>4}  "
                    f"${item['unit_price']:>7.2f}  ${line_total:>8.2f}"
                )
            print(thin)
            print(
                f"  {'Subtotal (excl. GST)':<50} "
                f"${self.subtotal:>8.2f}"
            )
        print(line)

    # ------------------------------------------------------------------ #
    # Serialisation                                                        #
    # ------------------------------------------------------------------ #

    def to_dict(self):
        """Serialise to dictionary for JSON persistence."""
        return {
            "order_id": self._order_id,
            "customer_id": self._customer_id,
            "items": self._items,
            "status": self._status,
            "created_at": self._created_at,
            "invoice_id": self._invoice_id,
        }

    @classmethod
    def from_dict(cls, data):
        """Deserialise an Order from a dictionary."""
        return cls(
            order_id=data["order_id"],
            customer_id=data["customer_id"],
            items=data.get("items", []),
            status=data.get("status", STATUS_PENDING),
            created_at=data.get("created_at"),
            invoice_id=data.get("invoice_id"),
        )

    def __repr__(self):
        return (
            f"Order(id={self._order_id!r}, "
            f"status={self._status!r}, "
            f"items={len(self._items)})"
        )


# ------------------------------------------------------------------ #
# Module-level helpers                                                #
# ------------------------------------------------------------------ #

def _generate_order_id(existing_orders):
    """Generate a sequential order ID (e.g. ORD0001)."""
    count = len(existing_orders) + 1
    return f"ORD{count:04d}"


def load_orders():
    """
    Load all orders from storage.

    Returns:
        dict[str, Order]: order_id -> Order.
    """
    if not os.path.exists(ORDERS_FILE):
        return {}
    with open(ORDERS_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return {item["order_id"]: Order.from_dict(item) for item in raw}


def save_orders(orders):
    """
    Persist all orders to storage.

    Args:
        orders (dict[str, Order]): order_id -> Order.
    """
    os.makedirs(os.path.dirname(ORDERS_FILE), exist_ok=True)
    data = [o.to_dict() for o in orders.values()]
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def create_order(customer, orders):
    """
    Create a new pending Order for the given customer.

    Args:
        customer (Customer): The customer placing the order.
        orders (dict): Existing orders.

    Returns:
        Order: The newly created Order.
    """
    order_id = _generate_order_id(orders)
    order = Order(order_id=order_id, customer_id=customer.customer_id)
    orders[order_id] = order
    save_orders(orders)
    return order
