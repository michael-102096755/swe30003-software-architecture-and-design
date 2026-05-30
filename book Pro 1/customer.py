"""
customer.py - Customer class for the Online Bookstore System
Coding standard: PEP 8 (https://peps.python.org/pep-0008/)

Implements:
  - Observer pattern (Observer side): receives order status notifications
CRC Reference: Section 3.3.1
"""

import hashlib
import uuid
from typing import List, Optional

from order import Order, OrderObserver
from catalogue import Catalogue
from book import Book


class Customer(OrderObserver):
    """
    Represents a registered user of the online bookstore.
    Can browse the catalogue, create orders, and view order history.

    Implements OrderObserver to receive status notifications when
    their order status changes (Observer pattern).

    Relationships:
        - 1:M with Order (a customer can place many orders)
        - Collaborates with Catalogue to browse books
    CRC Reference: Section 3.3.1
    """

    def __init__(self, name: str, email: str, password: str, address: str):
        """
        Register a new customer account.

        Args:
            name: Full name (cannot be blank).
            email: Email address used for login.
            password: Password (stored as hash).
            address: Default shipping address.

        Raises:
            ValueError: If any required field is blank or email is invalid.
        """
        if not name or not name.strip():
            raise ValueError("Name cannot be blank.")
        if not email or "@" not in email or "." not in email:
            raise ValueError("Please enter a valid email address.")
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters.")
        if not address or not address.strip():
            raise ValueError("Address cannot be blank.")

        self._customer_id = str(uuid.uuid4())[:8].upper()
        self._name = name.strip()
        self._email = email.strip().lower()
        self._password_hash = self._hash_password(password)
        self._address = address.strip()
        self._order_history: List[Order] = []
        self._notifications: List[str] = []

    # --- Authentication ---

    @staticmethod
    def _hash_password(password: str) -> str:
        """Return a SHA-256 hash of the password."""
        return hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password: str) -> bool:
        """Verify a given password against the stored hash."""
        return self._password_hash == self._hash_password(password)

    # --- Profile management ---

    def update_profile(self, name: str = None, address: str = None,
                       email: str = None) -> List[str]:
        """
        Update customer profile fields. Only non-None values are changed.

        Args:
            name: New full name (optional).
            address: New shipping address (optional).
            email: New email address (optional).

        Returns:
            List of fields that were successfully updated.

        Raises:
            ValueError: If a provided value fails validation.
        """
        updated = []
        if name is not None:
            if not name.strip():
                raise ValueError("Name cannot be blank.")
            self._name = name.strip()
            updated.append("name")
        if email is not None:
            if "@" not in email or "." not in email:
                raise ValueError("Please enter a valid email address.")
            self._email = email.strip().lower()
            updated.append("email")
        if address is not None:
            if not address.strip():
                raise ValueError("Address cannot be blank.")
            self._address = address.strip()
            updated.append("address")
        return updated

    # --- Catalogue browsing ---

    def browse_catalogue(self, catalogue: Catalogue,
                         keyword: str = "") -> List[Book]:
        """
        Browse the catalogue, optionally filtering by keyword.

        Args:
            catalogue: The store's Catalogue instance.
            keyword: Optional search term for title/author/ISBN.

        Returns:
            List of matching Book objects.
        """
        if keyword:
            return catalogue.search(keyword)
        return catalogue.get_all_books()

    # --- Order management ---

    def create_order(self, shipping_address: str = None) -> Order:
        """
        Create a new pending order for this customer.

        Args:
            shipping_address: Delivery address; defaults to profile address.

        Returns:
            A new Order instance registered to this customer.
        """
        address = shipping_address or self._address
        order = Order(
            customer_id=self._customer_id,
            customer_name=self._name,
            customer_email=self._email,
            shipping_address=address,
        )
        order.add_observer(self)
        self._order_history.append(order)
        return order

    def add_book_to_order(self, order: Order, book: Book,
                          quantity: int) -> bool:
        """
        Add a book with a given quantity to an existing order.

        Args:
            order: The active Order instance.
            book: Book to add.
            quantity: Number of copies.

        Returns:
            True if added successfully.
        """
        return order.add_book(book, quantity)

    def confirm_checkout(self, order: Order) -> bool:
        """
        Confirm the order, moving it from pending to confirmed.

        Returns:
            True if confirmed successfully.
        """
        return order.confirm_order()

    def view_order_history(self) -> List[Order]:
        """Return a list of all orders placed by this customer."""
        return list(self._order_history)

    def get_active_order(self) -> Optional[Order]:
        """
        Return the most recent pending order, if any.

        Returns:
            The latest pending Order, or None.
        """
        for order in reversed(self._order_history):
            if order.status == Order.STATUS_PENDING:
                return order
        return None

    # --- Observer pattern: receive order status notifications ---

    def on_order_status_changed(self, order_id: str, new_status: str):
        """
        Receive and store a notification when an order's status changes.
        Observer Pattern: Concrete Observer. CRC Reference: Section 5.2.2
        """
        message = (f"Order #{order_id} status updated to: "
                   f"{new_status.upper()}")
        self._notifications.append(message)
        print(f"\n  [Notification] {message}")

    def get_notifications(self) -> List[str]:
        """Return all notifications received by this customer."""
        return list(self._notifications)

    # --- Getters ---

    @property
    def customer_id(self) -> str:
        return self._customer_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def email(self) -> str:
        return self._email

    @property
    def address(self) -> str:
        return self._address

    # --- Serialisation ---

    def to_dict(self) -> dict:
        """Serialise customer to a dictionary for JSON storage."""
        return {
            "customer_id": self._customer_id,
            "name": self._name,
            "email": self._email,
            "password_hash": self._password_hash,
            "address": self._address,
            "notifications": self._notifications,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Customer":
        """Deserialise a Customer from a dictionary (bypasses __init__)."""
        c = cls.__new__(cls)
        c._customer_id = data["customer_id"]
        c._name = data["name"]
        c._email = data["email"]
        c._password_hash = data["password_hash"]
        c._address = data["address"]
        c._notifications = data.get("notifications", [])
        c._order_history = []  # orders are loaded separately
        return c

    def __repr__(self) -> str:
        return f"Customer(id={self._customer_id!r}, name={self._name!r})"
