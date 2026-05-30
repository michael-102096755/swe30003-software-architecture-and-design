"""
main.py - Entry point for the Favourite Books Online Bookstore System.

Provides a textual menu-driven interface supporting:
    1. Customer account management (register, login, update profile)
    2. Catalogue browsing (browse, search, filter, view details)
    3. Order management (create, add/remove/update books, confirm)
    4. Invoice generation (auto-generated on order confirmation)
    5. Shipment tracking (create record, assign tracking, update status)

Assignment: SWE30003 Assignment 3 - Object Design Implementation
Coding standard: PEP 8 (https://peps.python.org/pep-0008/)

Platform: Python 3.8+ | OS: Windows / macOS / Linux
Run:  python main.py  (from the bookstore/ directory)
"""

import os
import sys

# ------------------------------------------------------------------ #
# Path fix: ensure the bookstore/ directory is on sys.path so that  #
# 'models' package is importable regardless of where the user runs  #
# the script from (e.g. python main.py OR python bookstore/main.py) #
# ------------------------------------------------------------------ #
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)

# Change working directory to bookstore/ so relative paths
# (data/, storage/) resolve correctly no matter where python is run.
os.chdir(_BASE_DIR)

# ------------------------------------------------------------------ #
# Bootstrap: ensure storage directory exists before imports          #
# ------------------------------------------------------------------ #
os.makedirs("storage", exist_ok=True)

from models.catalogue import Catalogue
from models.customer import (
    load_customers, save_customers,
    register_customer, login_customer,
)
from models.order import (
    load_orders, save_orders, create_order,
    STATUS_PENDING, STATUS_CONFIRMED, STATUS_PAID,
)
from models.invoice import load_invoices, save_invoices, create_invoice_from_order
from models.shipment import (
    load_shipments, save_shipments,
    create_shipment_from_order, VALID_STATUSES,
)

# ------------------------------------------------------------------ #
# UI helpers                                                          #
# ------------------------------------------------------------------ #

BORDER = "=" * 62
THIN = "-" * 62


def clear():
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def pause():
    """Wait for the user to press Enter."""
    input("\n  Press Enter to continue...")


def print_header(title):
    """Print a formatted section header."""
    print(f"\n{BORDER}")
    print(f"  {title}")
    print(BORDER)


def get_input(prompt, required=True, input_type=str,
              min_val=None, max_val=None):
    """
    Prompt the user and validate input.

    Args:
        prompt (str): Prompt text.
        required (bool): Whether blank input is rejected.
        input_type (type): Expected type (str, int, float).
        min_val: Minimum value (for numeric types).
        max_val: Maximum value (for numeric types).

    Returns:
        The validated value cast to input_type, or None if optional blank.
    """
    while True:
        raw = input(f"  {prompt}: ").strip()
        if not raw:
            if not required:
                return None
            print("  [!] This field cannot be blank. Please try again.")
            continue
        if input_type in (int, float):
            try:
                value = input_type(raw)
            except ValueError:
                print(f"  [!] Please enter a valid {input_type.__name__}.")
                continue
            if min_val is not None and value < min_val:
                print(f"  [!] Value must be at least {min_val}.")
                continue
            if max_val is not None and value > max_val:
                print(f"  [!] Value must be at most {max_val}.")
                continue
            return value
        return raw


def get_menu_choice(options):
    """
    Display a numbered menu and return the validated choice index.

    Args:
        options (list[str]): Menu option labels.

    Returns:
        int: 1-based index of the chosen option.
    """
    for i, opt in enumerate(options, start=1):
        print(f"  [{i}] {opt}")
    return get_input("Enter choice", input_type=int,
                     min_val=1, max_val=len(options))


def pick_book_from_list(books):
    """
    Display a list of books and let the user select one by number.

    Args:
        books (list[Book]): Books to display.

    Returns:
        Book or None: The selected Book, or None if cancelled.
    """
    if not books:
        print("  No books to display.")
        return None
    catalogue_ref.display_books(books)
    print(f"\n  [0] Cancel")
    idx = get_input("Select book number", input_type=int,
                    min_val=0, max_val=len(books))
    if idx == 0:
        return None
    return books[idx - 1]


# ------------------------------------------------------------------ #
# Application state (loaded at startup)                               #
# ------------------------------------------------------------------ #

catalogue_ref = None   # set in main()


# ------------------------------------------------------------------ #
# Section 1: Authentication                                           #
# ------------------------------------------------------------------ #

def screen_register(customers):
    """Register a new customer account."""
    print_header("REGISTER NEW ACCOUNT")
    name = get_input("Full name")
    email = get_input("Email address")
    while True:
        password = get_input("Password (min 6 chars)")
        if len(password) < 6:
            print("  [!] Password must be at least 6 characters.")
            continue
        confirm = get_input("Confirm password")
        if password != confirm:
            print("  [!] Passwords do not match. Please try again.")
            continue
        break
    address = get_input("Delivery address")

    success, msg, customer = register_customer(
        customers, name, email, password, address
    )
    print(f"\n  {'[OK]' if success else '[!]'} {msg}")
    if success:
        print(f"  Your Customer ID: {customer.customer_id}")
    pause()
    return customer if success else None


def screen_login(customers):
    """Log in an existing customer."""
    print_header("CUSTOMER LOGIN")
    email = get_input("Email address")
    password = get_input("Password")
    success, msg, customer = login_customer(customers, email, password)
    print(f"\n  {'[OK]' if success else '[!]'} {msg}")
    pause()
    return customer if success else None


# ------------------------------------------------------------------ #
# Section 2: Catalogue browsing                                       #
# ------------------------------------------------------------------ #

def screen_browse_catalogue():
    """Browse and search the book catalogue."""
    while True:
        print_header("BROWSE CATALOGUE")
        options = [
            "View all books",
            "Search by keyword (title / author / category)",
            "Filter by category",
            "Filter by price range",
            "View book details",
            "Back",
        ]
        choice = get_menu_choice(options)

        if choice == 1:
            print_header("ALL BOOKS")
            catalogue_ref.display_books()
            pause()

        elif choice == 2:
            print_header("KEYWORD SEARCH")
            keyword = get_input("Enter keyword")
            results = catalogue_ref.search_books(keyword)
            print(f"\n  Found {len(results)} result(s):\n")
            catalogue_ref.display_books(results)
            pause()

        elif choice == 3:
            print_header("FILTER BY CATEGORY")
            cats = catalogue_ref.get_categories()
            if not cats:
                print("  No categories available.")
                pause()
                continue
            print("  Available categories:")
            for i, cat in enumerate(cats, 1):
                print(f"    [{i}] {cat}")
            idx = get_input("Select category number", input_type=int,
                            min_val=1, max_val=len(cats))
            results = catalogue_ref.filter_by_category(cats[idx - 1])
            print(f"\n  Books in '{cats[idx - 1]}':\n")
            catalogue_ref.display_books(results)
            pause()

        elif choice == 4:
            print_header("FILTER BY PRICE RANGE")
            min_p = get_input("Minimum price (AUD)", input_type=float,
                              min_val=0.0)
            max_p = get_input("Maximum price (AUD)", input_type=float,
                              min_val=min_p)
            results = catalogue_ref.filter_by_price_range(min_p, max_p)
            print(
                f"\n  Books between ${min_p:.2f} and ${max_p:.2f}:\n"
            )
            catalogue_ref.display_books(results)
            pause()

        elif choice == 5:
            print_header("BOOK DETAILS")
            book = pick_book_from_list(catalogue_ref.get_all_books())
            if book:
                print()
                book.display()
                pause()

        else:
            break


# ------------------------------------------------------------------ #
# Section 3 & 4: Order management + Invoice                          #
# ------------------------------------------------------------------ #

def screen_manage_order(customer, orders, invoices):
    """
    Create and manage an order for the logged-in customer.
    Covers order creation, item management, confirmation,
    payment (stub), and invoice display.
    """
    # Find or create a pending order for this customer
    pending_order = None
    for order in orders.values():
        if (order.customer_id == customer.customer_id
                and order.status == STATUS_PENDING):
            pending_order = order
            break

    if pending_order is None:
        pending_order = create_order(customer, orders)
        print(f"\n  [OK] New order created: {pending_order.order_id}")
        pause()

    while True:
        print_header(f"ORDER: {pending_order.order_id}  "
                     f"[{pending_order.status.upper()}]")
        pending_order.display()

        options = [
            "Add a book",
            "Remove a book",
            "Update book quantity",
            "Confirm order",
            "Cancel order",
            "Back to main menu",
        ]
        choice = get_menu_choice(options)

        if choice == 1:
            _add_book_to_order(pending_order)
            save_orders(orders)

        elif choice == 2:
            _remove_book_from_order(pending_order, orders)

        elif choice == 3:
            _update_book_quantity(pending_order, orders)

        elif choice == 4:
            result = _confirm_and_pay(
                pending_order, customer, orders, invoices
            )
            if result:
                break  # order complete; return to main menu

        elif choice == 5:
            _cancel_order(pending_order, orders)
            break

        else:
            break


def _add_book_to_order(order):
    """Helper: add a book to the given pending order."""
    print_header("ADD BOOK TO ORDER")
    keyword = get_input("Search for book (title/author/category)")
    results = catalogue_ref.search_books(keyword)
    if not results:
        print("  No books found for that keyword.")
        pause()
        return
    book = pick_book_from_list(results)
    if book is None:
        return
    print()
    book.display()
    qty = get_input(
        f"Quantity (available: {book.stock})",
        input_type=int, min_val=1, max_val=book.stock
    )
    try:
        order.add_book(book, qty)
        print(f"\n  [OK] Added {qty}x '{book.title}' to order.")
    except ValueError as err:
        print(f"\n  [!] {err}")
    pause()


def _remove_book_from_order(order, orders):
    """Helper: remove a book from the pending order."""
    if not order.items:
        print("\n  [!] Your order is empty.")
        pause()
        return
    print_header("REMOVE BOOK FROM ORDER")
    items = order.items
    for i, item in enumerate(items, 1):
        print(f"  [{i}] {item['title']}  x{item['quantity']}")
    print("  [0] Cancel")
    idx = get_input("Select item to remove", input_type=int,
                    min_val=0, max_val=len(items))
    if idx == 0:
        return
    book_id = items[idx - 1]["book_id"]
    try:
        order.remove_book(book_id, catalogue_ref)
        print(f"\n  [OK] Item removed from order.")
        save_orders(orders)
    except ValueError as err:
        print(f"\n  [!] {err}")
    pause()


def _update_book_quantity(order, orders):
    """Helper: update quantity of an item in the pending order."""
    if not order.items:
        print("\n  [!] Your order is empty.")
        pause()
        return
    print_header("UPDATE QUANTITY")
    items = order.items
    for i, item in enumerate(items, 1):
        print(f"  [{i}] {item['title']}  (current qty: {item['quantity']})")
    print("  [0] Cancel")
    idx = get_input("Select item", input_type=int,
                    min_val=0, max_val=len(items))
    if idx == 0:
        return
    book_id = items[idx - 1]["book_id"]
    book = catalogue_ref.get_book_by_id(book_id)
    max_qty = (book.stock + items[idx - 1]["quantity"]) if book else 99
    new_qty = get_input(
        f"New quantity (max available: {max_qty})",
        input_type=int, min_val=1, max_val=max_qty
    )
    try:
        order.update_quantity(book_id, new_qty, catalogue_ref)
        print(f"\n  [OK] Quantity updated.")
        save_orders(orders)
    except ValueError as err:
        print(f"\n  [!] {err}")
    pause()


def _confirm_and_pay(order, customer, orders, invoices):
    """
    Helper: confirm order, process stub payment, generate invoice.

    Returns:
        bool: True if completed successfully.
    """
    if not order.items:
        print("\n  [!] Cannot confirm an empty order.")
        pause()
        return False

    print_header("ORDER CONFIRMATION")
    order.display()
    confirm = get_input("Confirm this order? (yes/no)").lower()
    if confirm != "yes":
        print("  Order confirmation cancelled.")
        pause()
        return False

    try:
        order.confirm_order(catalogue_ref)
        save_orders(orders)
    except ValueError as err:
        print(f"\n  [!] {err}")
        pause()
        return False

    print("\n  [OK] Order confirmed. Proceeding to payment...")
    print("\n  --- Payment Gateway (Stub) ---")
    print("  Supported methods: Credit Card | PayPal | Bank Transfer")
    print("  [Note: Actual payment processing is handled externally]")

    options = ["Proceed with payment", "Cancel"]
    if get_menu_choice(options) == 2:
        print("  Payment cancelled.")
        pause()
        return False

    msg = order.process_payment()
    save_orders(orders)
    print(f"\n  [OK] {msg}")

    # Generate invoice
    invoice = create_invoice_from_order(order, customer, invoices)
    order.set_invoice_id(invoice.invoice_id)
    save_orders(orders)

    # Link order to customer history
    customer.add_order_id(order.order_id)

    print(f"\n  [OK] Invoice generated: {invoice.invoice_id}")
    print()
    invoice.display()
    pause()
    return True


def _cancel_order(order, orders):
    """Helper: cancel the pending order."""
    confirm = get_input(
        "Are you sure you want to cancel this order? (yes/no)"
    ).lower()
    if confirm == "yes":
        try:
            order.cancel_order(catalogue_ref)
            save_orders(orders)
            print("\n  [OK] Order cancelled.")
        except ValueError as err:
            print(f"\n  [!] {err}")
    else:
        print("  Cancellation aborted.")
    pause()


# ------------------------------------------------------------------ #
# Section 5: Shipment tracking                                        #
# ------------------------------------------------------------------ #

def screen_shipment(customer, orders, shipments):
    """
    View and manage shipments for the logged-in customer.
    Customer can view shipment status and update tracking.
    """
    while True:
        print_header("MY SHIPMENTS")

        # Gather customer's paid orders
        customer_shipments = [
            s for s in shipments.values()
            if s.customer_id == customer.customer_id
        ]

        # Auto-create shipments for paid orders that don't have one yet
        paid_orders = [
            o for o in orders.values()
            if (o.customer_id == customer.customer_id
                and o.status == STATUS_PAID)
        ]
        existing_order_ids = {s.order_id for s in customer_shipments}
        for paid_order in paid_orders:
            if paid_order.order_id not in existing_order_ids:
                new_shipment = create_shipment_from_order(
                    paid_order, customer, shipments
                )
                customer_shipments.append(new_shipment)
                print(
                    f"  [OK] Shipment created for order "
                    f"{paid_order.order_id}: {new_shipment.shipment_id}"
                )

        if not customer_shipments:
            print("  You have no shipments yet.")
            pause()
            break

        options = (
            [f"{s.shipment_id} | Order {s.order_id} "
             f"| Status: {s.status.upper()}"
             for s in customer_shipments]
            + ["Back"]
        )
        print("\n  Select a shipment to view:")
        choice = get_menu_choice(options)

        if choice > len(customer_shipments):
            break

        shipment = customer_shipments[choice - 1]
        _manage_single_shipment(shipment, shipments)


def _manage_single_shipment(shipment, shipments):
    """Helper: view and update a single shipment."""
    while True:
        print_header(f"SHIPMENT: {shipment.shipment_id}")
        shipment.display()

        options = [
            "Enter / update tracking number",
            "Update shipment status",
            "Back",
        ]
        choice = get_menu_choice(options)

        if choice == 1:
            tracking = get_input("Enter tracking number")
            try:
                shipment.assign_tracking_number(tracking)
                save_shipments(shipments)
                print(f"\n  [OK] Tracking number saved: {tracking}")
            except ValueError as err:
                print(f"\n  [!] {err}")
            pause()

        elif choice == 2:
            print(
                "\n  Valid statuses: "
                + ", ".join(VALID_STATUSES)
            )
            new_status = get_input("Enter new status").lower()
            try:
                shipment.update_status(new_status)
                save_shipments(shipments)
                print(f"\n  [OK] Status updated to: {new_status.upper()}")
            except ValueError as err:
                print(f"\n  [!] {err}")
            pause()

        else:
            break


# ------------------------------------------------------------------ #
# Section: View order history + invoices                              #
# ------------------------------------------------------------------ #

def screen_order_history(customer, orders, invoices):
    """Display past orders and their invoices for the customer."""
    print_header("ORDER HISTORY")
    customer_orders = [
        o for o in orders.values()
        if o.customer_id == customer.customer_id
    ]
    if not customer_orders:
        print("  You have no orders yet.")
        pause()
        return

    for order in customer_orders:
        order.display()
        if order.invoice_id and order.invoice_id in invoices:
            inv = invoices[order.invoice_id]
            print(f"\n  --- Invoice: {inv.invoice_id} ---")
            inv.display()
        print()
    pause()


# ------------------------------------------------------------------ #
# Logged-in customer menu                                             #
# ------------------------------------------------------------------ #

def screen_customer_menu(customer, customers, orders,
                         invoices, shipments):
    """Main menu for a logged-in customer."""
    while True:
        print_header(
            f"MAIN MENU  |  Logged in as: {customer.name}"
        )
        options = [
            "Browse catalogue",
            "My order (create / manage)",
            "My order history & invoices",
            "My shipments",
            "Update my profile",
            "Logout",
        ]
        choice = get_menu_choice(options)

        if choice == 1:
            screen_browse_catalogue()

        elif choice == 2:
            screen_manage_order(customer, orders, invoices)
            save_customers(customers)

        elif choice == 3:
            screen_order_history(customer, orders, invoices)

        elif choice == 4:
            screen_shipment(customer, orders, shipments)

        elif choice == 5:
            _update_profile(customer, customers)

        else:
            print(f"\n  Goodbye, {customer.name}!")
            pause()
            break


def _update_profile(customer, customers):
    """Helper: update customer profile fields."""
    print_header("UPDATE PROFILE")
    customer.display_profile()
    print(
        "\n  Leave a field blank to keep the current value.\n"
    )
    name = get_input("New name", required=False)
    address = get_input("New delivery address", required=False)
    email = get_input("New email", required=False)

    if name or address or email:
        customer.update_profile(name=name, address=address, email=email)
        save_customers(customers)
        print("\n  [OK] Profile updated successfully.")
        customer.display_profile()
    else:
        print("\n  No changes made.")
    pause()


# ------------------------------------------------------------------ #
# Home screen                                                         #
# ------------------------------------------------------------------ #

def screen_home():
    """Display the application home/welcome screen."""
    clear()
    print(BORDER)
    print("                                                              ")
    print("         FAVOURITE BOOKS - ONLINE BOOKSTORE                  ")
    print("              Hawthorn, Victoria, Australia                   ")
    print("                                                              ")
    print(BORDER)
    print("    Welcome! Shop from thousands of books delivered           ")
    print("    Australia-wide.                                           ")
    print(BORDER)


# ------------------------------------------------------------------ #
# Main entry point                                                     #
# ------------------------------------------------------------------ #

def main():
    """Bootstrap the system and run the main application loop."""
    global catalogue_ref

    # Bootstrap sequence (per Assignment 2, Section 6)
    catalogue_ref = Catalogue(data_path="data/books.json")
    customers = load_customers()
    orders = load_orders()
    invoices = load_invoices()
    shipments = load_shipments()

    while True:
        screen_home()
        print()
        options = [
            "Login",
            "Register new account",
            "Browse catalogue (no login required)",
            "Exit",
        ]
        choice = get_menu_choice(options)

        if choice == 1:
            customer = screen_login(customers)
            if customer:
                screen_customer_menu(
                    customer, customers, orders, invoices, shipments
                )

        elif choice == 2:
            customer = screen_register(customers)
            if customer:
                screen_customer_menu(
                    customer, customers, orders, invoices, shipments
                )

        elif choice == 3:
            screen_browse_catalogue()

        else:
            clear()
            print("\n  Thank you for visiting Favourite Books!")
            print("  Goodbye.\n")
            sys.exit(0)


if __name__ == "__main__":
    main()
