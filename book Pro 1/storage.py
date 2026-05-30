"""
storage.py - JSON file-based persistence for the Online Bookstore System
Coding standard: PEP 8 (https://peps.python.org/pep-0008/)
"""

import json
import os
from typing import Dict, Optional

from book import Book
from catalogue import Catalogue
from customer import Customer
from order import Order

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CATALOGUE_FILE = os.path.join(DATA_DIR, "catalogue.json")
CUSTOMERS_FILE = os.path.join(DATA_DIR, "customers.json")
ORDERS_FILE = os.path.join(DATA_DIR, "orders.json")


def _ensure_data_dir():
    """Create the data directory if it does not exist."""
    os.makedirs(DATA_DIR, exist_ok=True)


# --- Catalogue ---

def save_catalogue(catalogue: Catalogue):
    """Persist catalogue to JSON."""
    _ensure_data_dir()
    with open(CATALOGUE_FILE, "w", encoding="utf-8") as f:
        json.dump(catalogue.to_dict(), f, indent=2)


def load_catalogue() -> Catalogue:
    """Load catalogue from JSON, or return an empty catalogue."""
    cat = Catalogue()
    if os.path.exists(CATALOGUE_FILE):
        with open(CATALOGUE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        cat.load_from_dict(data)
    return cat


# --- Customers ---

def save_customers(customers: Dict[str, Customer]):
    """Persist all customers to JSON."""
    _ensure_data_dir()
    with open(CUSTOMERS_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {email: c.to_dict() for email, c in customers.items()},
            f, indent=2
        )


def load_customers() -> Dict[str, Customer]:
    """Load customers from JSON, keyed by email."""
    if os.path.exists(CUSTOMERS_FILE):
        with open(CUSTOMERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {email: Customer.from_dict(cdata) for email, cdata in data.items()}
    return {}


# --- Orders ---

def save_orders(orders: Dict[str, Order]):
    """Persist all orders to JSON."""
    _ensure_data_dir()
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {oid: o.to_dict() for oid, o in orders.items()},
            f, indent=2
        )


def load_orders(catalogue: Catalogue,
                customers: Dict[str, Customer]) -> Dict[str, Order]:
    """
    Load all orders from JSON, link to live Book and Customer objects.

    Args:
        catalogue: The loaded Catalogue instance (for book lookups).
        customers: Dict of loaded Customer instances (keyed by email).

    Returns:
        Dict of Order instances keyed by order_id.
    """
    if not os.path.exists(ORDERS_FILE):
        return {}

    with open(ORDERS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Build a lookup by customer_id so we can attach orders
    cust_by_id = {c.customer_id: c for c in customers.values()}
    orders = {}
    for oid, odata in data.items():
        order = Order.from_dict(odata, catalogue)
        orders[oid] = order
        # Re-attach order to its customer's history
        owner = cust_by_id.get(order.customer_id)
        if owner:
            owner._order_history.append(order)
            order.add_observer(owner)
    return orders
