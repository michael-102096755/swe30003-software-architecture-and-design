"""
app.py - SWE30003 - Assignment 3 - Michael Attardi, 102096755 - Gian Tze Ee, 105220081
"""
from flask import Flask, request, jsonify
from flask_cors import CORS

from models.book import Book
from models.customer import Customer
from models.order import Order
from models.invoice import Invoice

app = Flask(__name__)
CORS(app)  # Allow requests from the frontend


# Books
@app.route("/books", methods=["GET"])
def get_books():
    """Returns all books in the catalogue."""
    books = Book.load_all()
    return jsonify([b.to_dict() for b in books])


@app.route("/books", methods=["POST"])
def create_book():
    """Creates a new book and adds it to the catalogue."""
    data = request.json

    # Validate required fields
    required = ["title", "author", "isbn", "price", "stock"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"'{field}' is required"}), 400

    book = Book(
        title=data["title"],
        author=data["author"],
        isbn=data["isbn"],
        price=float(data["price"]),
        stock=int(data["stock"]),
        category=data.get("category", ""),
        publisher=data.get("publisher", ""),
        year=data.get("year")
    )
    book.save()
    return jsonify(book.to_dict()), 201


@app.route("/books/<book_id>", methods=["GET"])
def get_book(book_id):
    """Returns a single book by ID."""
    book = Book.find_by_id(book_id)
    if not book:
        return jsonify({"error": "Book not found"}), 404
    return jsonify(book.to_dict())


# Customers
@app.route("/customers", methods=["GET"])
def get_customers():
    """Returns all customers (excludes password hashes)."""
    customers = Customer.load_all()
    # Strip password hash before returning - no need to expose it
    result = []
    for c in customers:
        d = c.to_dict()
        d.pop("password_hash", None)
        result.append(d)
    return jsonify(result)


@app.route("/customers/register", methods=["POST"])
def register_customer():
    """Registers a new customer account."""
    data = request.json

    required = ["name", "email", "password"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"'{field}' is required"}), 400

    customer = Customer.register(
        name=data["name"],
        email=data["email"],
        password=data["password"],
        address=data.get("address", "")
    )

    if not customer:
        return jsonify({"error": "An account with that email already exists"}), 400

    d = customer.to_dict()
    d.pop("password_hash", None)
    return jsonify(d), 201


@app.route("/customers/login", methods=["POST"])
def login_customer():
    """Logs in a customer by email and password."""
    data = request.json

    if not data.get("email") or not data.get("password"):
        return jsonify({"error": "'email' and 'password' are required"}), 400

    customer = Customer.login(data["email"], data["password"])
    if not customer:
        return jsonify({"error": "Invalid email or password"}), 401

    d = customer.to_dict()
    d.pop("password_hash", None)
    return jsonify(d)


@app.route("/customers/<customer_id>", methods=["GET"])
def get_customer(customer_id):
    """Returns a single customer by ID (excludes password hash)."""
    customer = Customer.find_by_id(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    d = customer.to_dict()
    d.pop("password_hash", None)
    return jsonify(d)


# Orders
@app.route("/orders", methods=["GET"])
def get_orders():
    """Returns all orders."""
    orders = Order.load_all()
    return jsonify([o.to_dict() for o in orders])


@app.route("/orders", methods=["POST"])
def create_order():
    """Creates a new empty order for a customer."""
    data = request.json

    if not data.get("customer_id"):
        return jsonify({"error": "'customer_id' is required"}), 400

    customer = Customer.find_by_id(data["customer_id"])
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    order = Order(customer_id=data["customer_id"])
    order.save()

    # Link the order to the customer's history
    customer.add_order_id(order.order_id)

    return jsonify(order.to_dict()), 201


@app.route("/orders/<order_id>", methods=["GET"])
def get_order(order_id):
    """Returns a single order by ID."""
    order = Order.find_by_id(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    return jsonify(order.to_dict())


@app.route("/orders/<order_id>/items", methods=["POST"])
def add_item_to_order(order_id):
    """Adds a book to an order, or increases its quantity if already present."""
    order = Order.find_by_id(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    if order.status != "pending":
        return jsonify({"error": "Cannot modify a confirmed or paid order"}), 400

    data = request.json
    if not data.get("book_id"):
        return jsonify({"error": "'book_id' is required"}), 400

    book = Book.find_by_id(data["book_id"])
    if not book:
        return jsonify({"error": "Book not found"}), 404

    quantity = int(data.get("quantity", 1))
    if not order.add_item(book, quantity):
        return jsonify({"error": f"Not enough stock for '{book.title}' (available: {book.stock})"}), 400
    order.save()
    return jsonify(order.to_dict())


@app.route("/orders/<order_id>/items/<book_id>", methods=["DELETE"])
def remove_item_from_order(order_id, book_id):
    """Removes a book from an order."""
    order = Order.find_by_id(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    if order.status != "pending":
        return jsonify({"error": "Cannot modify a confirmed or paid order"}), 400

    order.remove_item(book_id)
    order.save()
    return jsonify(order.to_dict())


@app.route("/orders/<order_id>/confirm", methods=["POST"])
def confirm_order(order_id):
    """Confirms an order and generates an invoice."""
    order = Order.find_by_id(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    if not order.confirm():
        return jsonify({"error": "Order could not be confirmed — it may be empty or a book is out of stock"}), 400

    order.save()

    # Generate invoice automatically on confirm - pass customer for name/address snapshot
    customer = Customer.find_by_id(order.customer_id)
    invoice = Invoice.from_order(order, customer)
    return jsonify({"order": order.to_dict(), "invoice": invoice.to_dict()})


@app.route("/orders/<order_id>/pay", methods=["POST"])
def pay_order(order_id):
    """Marks a confirmed order as paid. Simulates payment processing."""
    order = Order.find_by_id(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    if order.status != "confirmed":
        return jsonify({"error": "Order must be confirmed before payment"}), 400

    order.mark_as_paid()
    order.save()
    return jsonify({"message": "Payment processed successfully", "order": order.to_dict()})


# Invoices
@app.route("/invoices", methods=["GET"])
def get_invoices():
    """Returns all invoices."""
    invoices = Invoice.load_all()
    return jsonify([i.to_dict() for i in invoices])


@app.route("/invoices/<invoice_id>", methods=["GET"])
def get_invoice(invoice_id):
    """Returns a single invoice by ID."""
    invoice = Invoice.find_by_id(invoice_id)
    if not invoice:
        return jsonify({"error": "Invoice not found"}), 404
    return jsonify(invoice.to_dict())


# Run
if __name__ == "__main__":
    app.run(debug=True)