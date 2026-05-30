"""
main.py - Online Bookstore CLI Application (Favourite Books)
SWE30003 Software Architectures and Design - Assignment 3
Coding standard: PEP 8 (https://peps.python.org/pep-0008/)

Covers 4 business areas (Assignment 3 requirement):
  1. Customer Accounts   (register, login, update profile)
  2. Catalogue Browsing  (search, filter, view details)
  3. Orders              (add/remove/update books, checkout)
  4. Payments & Invoices (process payment, view invoice/history)
"""

import sys
from typing import Dict, Optional

from catalogue import Catalogue
from customer import Customer
from order import Order
from payment import CreditCardPayment, PayPalPayment
import storage

# ── Global state ──────────────────────────────────────────────────────────────
catalogue: Catalogue = Catalogue()
customers: Dict[str, Customer] = {}
orders: Dict[str, Order] = {}
current_customer: Optional[Customer] = None
current_order: Optional[Order] = None


# ── Utility helpers ────────────────────────────────────────────────────────────

def _save_all():
    """Persist all data to JSON files."""
    storage.save_catalogue(catalogue)
    storage.save_customers(customers)
    storage.save_orders(orders)


def _banner(title: str):
    print("\n" + "=" * 55)
    print(f"  {title}")
    print("=" * 55)


def _prompt(msg: str, allow_blank: bool = False) -> str:
    """Read a non-blank string from the user."""
    while True:
        value = input(f"  {msg}: ").strip()
        if value or allow_blank:
            return value
        print("  ✗ This field cannot be blank. Please try again.")


def _prompt_int(msg: str, min_val: int = 1, max_val: int = 9999) -> Optional[int]:
    """Read a validated integer from the user. Returns None on blank/invalid."""
    raw = input(f"  {msg}: ").strip()
    if not raw:
        return None
    try:
        val = int(raw)
        if val < min_val or val > max_val:
            print(f"  ✗ Please enter a number between {min_val} and {max_val}.")
            return None
        return val
    except ValueError:
        print("  ✗ Please enter a valid whole number.")
        return None


def _choose(options: list) -> Optional[int]:
    """
    Display a numbered menu and return the chosen index (0-based).
    Returns None if the user enters an invalid choice.
    """
    for i, opt in enumerate(options, 1):
        print(f"  [{i}] {opt}")
    raw = input("  Your choice: ").strip()
    try:
        choice = int(raw)
        if 1 <= choice <= len(options):
            return choice - 1
    except ValueError:
        pass
    print("  ✗ Invalid choice.")
    return None


# ── Area 1: Customer Accounts ──────────────────────────────────────────────────

def register():
    """Register a new customer account."""
    global current_customer
    _banner("REGISTER NEW ACCOUNT")
    name = _prompt("Full name")
    email = _prompt("Email address")
    if email.lower() in customers:
        print("  ✗ An account with that email already exists.")
        return
    password = _prompt("Password (min 6 characters)")
    address = _prompt("Shipping address")
    try:
        customer = Customer(name, email, password, address)
        customers[customer.email] = customer
        current_customer = customer
        _save_all()
        print(f"\n  ✓ Welcome, {customer.name}! "
              f"Account created (ID: {customer.customer_id}).")
    except ValueError as e:
        print(f"  ✗ {e}")


def login():
    """Log in with an existing customer account."""
    global current_customer
    _banner("LOG IN")
    email = _prompt("Email address")
    password = _prompt("Password")
    customer = customers.get(email.lower())
    if customer and customer.check_password(password):
        current_customer = customer
        print(f"\n  ✓ Welcome back, {customer.name}!")
    else:
        print("  ✗ Incorrect email or password.")


def logout():
    """Log out the current customer."""
    global current_customer, current_order
    if current_customer:
        print(f"\n  Goodbye, {current_customer.name}!")
        current_customer = None
        current_order = None
    else:
        print("  You are not logged in.")


def update_profile():
    """Update the logged-in customer's profile."""
    if not current_customer:
        print("  ✗ Please log in first.")
        return
    _banner("UPDATE PROFILE")
    print("  (Press Enter to keep current value)")
    name = input(f"  Name [{current_customer.name}]: ").strip() or None
    email_input = input(f"  Email [{current_customer.email}]: ").strip() or None
    address = input(f"  Address [{current_customer.address}]: ").strip() or None
    try:
        updated = current_customer.update_profile(name=name,
                                                   email=email_input,
                                                   address=address)
        if updated:
            # Re-key in customers dict if email changed
            customers.clear()
            customers[current_customer.email] = current_customer
            _save_all()
            print(f"  ✓ Updated: {', '.join(updated)}")
        else:
            print("  No changes made.")
    except ValueError as e:
        print(f"  ✗ {e}")


# ── Area 2: Catalogue Browsing ─────────────────────────────────────────────────

def browse_catalogue():
    """Browse and search the book catalogue."""
    _banner("BROWSE CATALOGUE")
    idx = _choose(["Search by keyword (title / author / ISBN)",
                   "Filter by category",
                   "Filter by price range",
                   "Show all books"])
    if idx is None:
        return

    if idx == 0:
        keyword = _prompt("Enter keyword")
        results = catalogue.search(keyword)
    elif idx == 1:
        categories = catalogue.get_categories()
        if not categories:
            print("  No categories available.")
            return
        print("\n  Available categories:")
        cat_idx = _choose(categories)
        if cat_idx is None:
            return
        results = catalogue.filter_by_category(categories[cat_idx])
    elif idx == 2:
        min_p = input("  Min price (AUD, press Enter for 0): ").strip()
        max_p = input("  Max price (AUD, press Enter for 9999): ").strip()
        try:
            min_price = float(min_p) if min_p else 0.0
            max_price = float(max_p) if max_p else 9999.0
            if min_price < 0 or max_price < 0:
                print("  ✗ Prices cannot be negative.")
                return
            results = catalogue.filter_by_price_range(min_price, max_price)
        except ValueError:
            print("  ✗ Please enter valid price values.")
            return
    else:
        results = catalogue.get_all_books()

    if not results:
        print("  No books found.")
        return

    print(f"\n  Found {len(results)} book(s):\n")
    for book in results:
        print(f"  {book.display()}")

    # Offer to add a book to the active order
    if current_customer:
        add = input("\n  Add a book to your order? (y/n): ").strip().lower()
        if add == "y":
            _add_book_to_order_from_list(results)


def _add_book_to_order_from_list(books):
    """Helper: let the user pick a book from a list and add it to the order."""
    global current_order
    isbn = _prompt("Enter ISBN of the book to add")
    book = catalogue.get_book_by_isbn(isbn)
    if not book:
        print("  ✗ ISBN not found in catalogue.")
        return
    if not book.is_available():
        print(f"  ✗ '{book.title}' is currently out of stock.")
        return
    qty = _prompt_int(f"Quantity (max {book.stock})", 1, book.stock)
    if qty is None:
        return

    if current_order is None or current_order.status != Order.STATUS_PENDING:
        # Create a new order
        address = input(
            f"  Shipping address [{current_customer.address}]: "
        ).strip() or current_customer.address
        current_order = current_customer.create_order(address)
        orders[current_order.order_id] = current_order

    if current_customer.add_book_to_order(current_order, book, qty):
        print(f"  ✓ Added {qty}x '{book.title}' to order #{current_order.order_id}.")
        _save_all()
    else:
        print("  ✗ Could not add book to order.")


# ── Area 3: Order Management ───────────────────────────────────────────────────

def manage_order():
    """View and modify the current active order."""
    global current_order
    if not current_customer:
        print("  ✗ Please log in first.")
        return

    _banner("MANAGE ORDER")

    # Find or confirm active order
    if current_order is None or current_order.status != Order.STATUS_PENDING:
        current_order = current_customer.get_active_order()

    if current_order is None:
        print("  You have no active order.")
        start = input("  Start a new order? (y/n): ").strip().lower()
        if start == "y":
            address = input(
                f"  Shipping address [{current_customer.address}]: "
            ).strip() or current_customer.address
            current_order = current_customer.create_order(address)
            orders[current_order.order_id] = current_order
            print(f"  ✓ New order #{current_order.order_id} created.")
            _save_all()
        return

    print(current_order.display_cart())

    idx = _choose([
        "Add a book",
        "Remove a book",
        "Update quantity",
        "Proceed to checkout",
        "Cancel order",
        "Back",
    ])

    if idx == 0:
        _add_book_interactively()
    elif idx == 1:
        _remove_book_from_order()
    elif idx == 2:
        _update_quantity_in_order()
    elif idx == 3:
        checkout()
    elif idx == 4:
        confirm = input("  Are you sure you want to cancel this order? (y/n): ")
        if confirm.lower() == "y":
            current_order.cancel_order()
            _save_all()
            print("  ✓ Order cancelled.")
    # idx 5 = back


def _add_book_interactively():
    """Prompt user to enter ISBN and quantity to add to the current order."""
    isbn = _prompt("Enter ISBN of the book to add")
    book = catalogue.get_book_by_isbn(isbn)
    if not book:
        print("  ✗ ISBN not found.")
        return
    print(f"  {book.display()}")
    if not book.is_available():
        print("  ✗ This book is out of stock.")
        return
    qty = _prompt_int(f"Quantity (max {book.stock})", 1, book.stock)
    if qty is None:
        return
    if current_customer.add_book_to_order(current_order, book, qty):
        print(f"  ✓ Added {qty}x '{book.title}'.")
        _save_all()


def _remove_book_from_order():
    """Remove a book from the current order by ISBN."""
    isbn = _prompt("Enter ISBN of book to remove")
    if current_order.remove_book(isbn):
        print("  ✓ Book removed.")
        _save_all()
    else:
        print("  ✗ That book is not in your order.")


def _update_quantity_in_order():
    """Update quantity of a book in the current order."""
    isbn = _prompt("Enter ISBN of book to update")
    qty = _prompt_int("New quantity (0 to remove)", 0)
    if qty is None:
        return
    if current_order.update_quantity(isbn, qty):
        action = "removed" if qty == 0 else f"updated to {qty}"
        print(f"  ✓ Quantity {action}.")
        _save_all()


# ── Area 4: Checkout, Payment & Invoices ───────────────────────────────────────

def checkout():
    """Confirm the order and process payment."""
    global current_order
    if not current_customer:
        print("  ✗ Please log in first.")
        return

    if current_order is None or current_order.status != Order.STATUS_PENDING:
        current_order = current_customer.get_active_order()

    if current_order is None or not current_order.items:
        print("  ✗ You have no active order to check out.")
        return

    _banner("CHECKOUT")
    print(current_order.display_cart())

    # Confirm order
    confirm = input("\n  Confirm this order? (y/n): ").strip().lower()
    if confirm != "y":
        print("  Checkout cancelled.")
        return

    if not current_order.confirm_order():
        return

    # Payment method selection
    print("\n  Select payment method:")
    pay_idx = _choose(["Credit / Debit Card", "PayPal"])
    if pay_idx is None:
        print("  Payment cancelled.")
        current_order._status = Order.STATUS_PENDING  # revert
        return

    try:
        if pay_idx == 0:
            card_num = _prompt("Card number (16 digits, spaces OK)")
            expiry = _prompt("Expiry date (MM/YY)")
            cvv = _prompt("CVV (3 digits)")
            strategy = CreditCardPayment(
                card_num.replace(" ", ""), expiry, cvv
            )
        else:
            email = _prompt("PayPal email address")
            strategy = PayPalPayment(email)
    except ValueError as e:
        print(f"  ✗ {e}")
        current_order._status = Order.STATUS_PENDING  # revert
        return

    if current_order.process_payment(strategy):
        _save_all()
        print(f"\n  ✓ Order #{current_order.order_id} paid successfully!")
        print("\n" + current_order.invoice.display())
        current_order = None   # clear active order
    else:
        print("  ✗ Payment failed. Please try again.")
        current_order._status = Order.STATUS_PENDING  # revert


def view_order_history():
    """Display all past orders for the logged-in customer."""
    if not current_customer:
        print("  ✗ Please log in first.")
        return
    _banner("ORDER HISTORY")
    history = current_customer.view_order_history()
    if not history:
        print("  No orders placed yet.")
        return
    for order in history:
        print(f"  {order.display_summary()}")

    # Allow viewing invoice for a paid order
    view_inv = input("\n  View invoice for a paid order? (y/n): ").strip().lower()
    if view_inv == "y":
        oid = _prompt("Enter Order ID")
        found = next((o for o in history
                      if o.order_id == oid.upper()), None)
        if found and found.invoice:
            print("\n" + found.invoice.display())
        elif found:
            print("  No invoice available for this order "
                  "(not yet paid or was cancelled).")
        else:
            print("  ✗ Order not found.")


# ── Main menu ──────────────────────────────────────────────────────────────────

def main_menu():
    """Display the top-level menu based on login state."""
    if current_customer:
        print(f"\n  Logged in as: {current_customer.name} "
              f"({current_customer.email})")
        if current_order and current_order.status == Order.STATUS_PENDING:
            total = current_order.calculate_total()
            items = len(current_order.items)
            print(f"  Active order: #{current_order.order_id} "
                  f"| {items} item(s) | ${total:.2f}")
        options = [
            "Browse Catalogue",
            "Manage Order",
            "Checkout",
            "View Order History",
            "Update Profile",
            "Log Out",
            "Exit",
        ]
    else:
        options = [
            "Browse Catalogue (guest)",
            "Register",
            "Log In",
            "Exit",
        ]
    return options


def run():
    """Main application loop."""
    global catalogue, customers, orders, current_customer, current_order

    # Bootstrap: load persisted data
    catalogue = storage.load_catalogue()
    customers = storage.load_customers()
    orders = storage.load_orders(catalogue, customers)

    print("\n" + "=" * 55)
    print("       FAVOURITE BOOKS — Online Bookstore")
    print("       Hawthorn, Victoria — Australia-Wide")
    print("=" * 55)
    print(f"  Catalogue loaded: {len(catalogue)} books available.")

    while True:
        _banner("MAIN MENU")
        options = main_menu()
        idx = _choose(options)
        if idx is None:
            continue

        if current_customer:
            actions = [
                browse_catalogue,
                manage_order,
                checkout,
                view_order_history,
                update_profile,
                logout,
                None,  # Exit
            ]
            if idx == len(actions) - 1:
                print("\n  Thank you for visiting Favourite Books. Goodbye!\n")
                _save_all()
                sys.exit(0)
            action = actions[idx]
            if action:
                action()
        else:
            if idx == 0:
                browse_catalogue()
            elif idx == 1:
                register()
            elif idx == 2:
                login()
            elif idx == 3:
                print("\n  Thank you for visiting Favourite Books. Goodbye!\n")
                sys.exit(0)


if __name__ == "__main__":
    run()
