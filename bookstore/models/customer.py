"""
customer.py - Customer model for the Online Bookstore System.

Represents a registered user who can browse, place orders,
and view order history.
Follows the CRC design from Assignment 2 (Section 3.3.1).

Coding standard: PEP 8 (https://peps.python.org/pep-0008/)
"""

import json
import os
import hashlib


# Path to persist customer accounts
CUSTOMERS_FILE = "storage/customers.json"


class Customer:
    """
    Represents a registered user of the online bookstore.

    Responsibilities (from CRC):
        - Register a new account
        - Log into existing account
        - Update personal profile (name, address, email)
        - Browse catalogue  (delegates to Catalogue)
        - Create a new order
        - Add books to Order
        - Confirm checkout
        - View order history
    """

    def __init__(self, customer_id, name, email,
                 password_hash, address, order_ids=None):
        """
        Initialise a Customer instance.

        Args:
            customer_id (str): Unique customer identifier.
            name (str): Full name.
            email (str): Email address (used as login username).
            password_hash (str): SHA-256 hashed password.
            address (str): Delivery address.
            order_ids (list[str], optional): List of past order IDs.
        """
        self._customer_id = customer_id
        self._name = name
        self._email = email
        self._password_hash = password_hash
        self._address = address
        self._order_ids = order_ids if order_ids is not None else []

    # ------------------------------------------------------------------ #
    # Properties                                                           #
    # ------------------------------------------------------------------ #

    @property
    def customer_id(self):
        return self._customer_id

    @property
    def name(self):
        return self._name

    @property
    def email(self):
        return self._email

    @property
    def address(self):
        return self._address

    @property
    def order_ids(self):
        return list(self._order_ids)

    # ------------------------------------------------------------------ #
    # Responsibilities                                                     #
    # ------------------------------------------------------------------ #

    def verify_password(self, plain_password):
        """
        Verify a plain-text password against the stored hash.

        Args:
            plain_password (str): Password entered by the user.

        Returns:
            bool: True if password matches.
        """
        return self._password_hash == _hash_password(plain_password)

    def update_profile(self, name=None, address=None, email=None):
        """
        Update customer profile fields.

        Args:
            name (str, optional): New name.
            address (str, optional): New delivery address.
            email (str, optional): New email address.
        """
        if name:
            self._name = name.strip()
        if address:
            self._address = address.strip()
        if email:
            self._email = email.strip().lower()

    def add_order_id(self, order_id):
        """
        Record a new order ID in this customer's history.

        Args:
            order_id (str): The confirmed order's ID.
        """
        if order_id not in self._order_ids:
            self._order_ids.append(order_id)

    def display_profile(self):
        """Print a formatted summary of the customer's profile."""
        print(f"  Customer ID : {self._customer_id}")
        print(f"  Name        : {self._name}")
        print(f"  Email       : {self._email}")
        print(f"  Address     : {self._address}")
        print(f"  Orders      : {len(self._order_ids)} order(s) placed")

    # ------------------------------------------------------------------ #
    # Serialisation                                                        #
    # ------------------------------------------------------------------ #

    def to_dict(self):
        """Serialise the Customer to a dictionary for JSON persistence."""
        return {
            "customer_id": self._customer_id,
            "name": self._name,
            "email": self._email,
            "password_hash": self._password_hash,
            "address": self._address,
            "order_ids": self._order_ids,
        }

    @classmethod
    def from_dict(cls, data):
        """Deserialise a Customer from a dictionary."""
        return cls(
            customer_id=data["customer_id"],
            name=data["name"],
            email=data["email"],
            password_hash=data["password_hash"],
            address=data["address"],
            order_ids=data.get("order_ids", []),
        )

    def __repr__(self):
        return f"Customer(id={self._customer_id!r}, name={self._name!r})"


# ------------------------------------------------------------------ #
# Module-level helpers                                                #
# ------------------------------------------------------------------ #

def _hash_password(plain_password):
    """
    Hash a plain-text password using SHA-256.

    Args:
        plain_password (str): Plain-text password.

    Returns:
        str: Hexadecimal SHA-256 digest.
    """
    return hashlib.sha256(plain_password.encode("utf-8")).hexdigest()


def _generate_customer_id(existing_ids):
    """
    Generate a new sequential customer ID (e.g. CUST0001).

    Args:
        existing_ids (list[str]): Already used IDs.

    Returns:
        str: A new unique customer ID.
    """
    count = len(existing_ids) + 1
    return f"CUST{count:04d}"


def load_customers():
    """
    Load all customer records from storage.

    Returns:
        dict[str, Customer]: email -> Customer mapping.
    """
    if not os.path.exists(CUSTOMERS_FILE):
        return {}
    with open(CUSTOMERS_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)
    customers = {}
    for item in raw:
        c = Customer.from_dict(item)
        customers[c.email] = c
    return customers


def save_customers(customers):
    """
    Persist all customer records to storage.

    Args:
        customers (dict[str, Customer]): email -> Customer mapping.
    """
    os.makedirs(os.path.dirname(CUSTOMERS_FILE), exist_ok=True)
    data = [c.to_dict() for c in customers.values()]
    with open(CUSTOMERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def register_customer(customers, name, email, password, address):
    """
    Register a new customer account.

    Args:
        customers (dict): Existing customers (email -> Customer).
        name (str): Full name.
        email (str): Email address.
        password (str): Plain-text password.
        address (str): Delivery address.

    Returns:
        tuple[bool, str, Customer|None]:
            (success, message, customer_or_None)
    """
    email = email.strip().lower()
    if email in customers:
        return False, "An account with this email already exists.", None

    new_id = _generate_customer_id(list(customers.keys()))
    hashed = _hash_password(password)
    customer = Customer(new_id, name.strip(), email,
                        hashed, address.strip())
    customers[email] = customer
    save_customers(customers)
    return True, "Account created successfully.", customer


def login_customer(customers, email, password):
    """
    Authenticate a customer by email and password.

    Args:
        customers (dict): Existing customers (email -> Customer).
        email (str): Email address.
        password (str): Plain-text password.

    Returns:
        tuple[bool, str, Customer|None]:
            (success, message, customer_or_None)
    """
    email = email.strip().lower()
    customer = customers.get(email)
    if customer is None:
        return False, "No account found with that email.", None
    if not customer.verify_password(password):
        return False, "Incorrect password.", None
    return True, f"Welcome back, {customer.name}!", customer
