"""
customer.py - SWE30003 - Assignment 3 - Gian Tze Ee, 105220081
"""
import json
import hashlib

# Path to the customers JSON file
DATA_FILE = "data/customers.json"


class Customer:
    """
    Represents a registered customer of the online bookstore.
    Stores personal details, a hashed password, and order history.

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

    def __init__(self, name, email, password_hash, address="",
                 customer_id=None, order_ids=None):
        self.customer_id = customer_id or Customer._generate_id()
        self.name = name
        self.email = email
        self.password_hash = password_hash  # Always stored as a SHA-256 hash
        self.address = address
        self.order_ids = order_ids or []

    @staticmethod
    def _generate_id():
        """Generates the next customer ID in CUST#### format."""
        customers = Customer.load_all()
        if not customers:
            return "CUST0001"
        # Find the highest existing numeric ID and increment it
        nums = []
        for c in customers:
            if c.customer_id.startswith("CUST") and c.customer_id[4:].isdigit():
                nums.append(int(c.customer_id[4:]))
        next_num = max(nums) + 1 if nums else 1
        return f"CUST{next_num:04d}"


    # Password helper
    @staticmethod
    def hash_password(password):
        """Returns the SHA-256 hash of a plaintext password."""
        return hashlib.sha256(password.encode()).hexdigest()

    # Account methods
    @staticmethod
    def register(name, email, password, address=""):
        """
        Creates and saves a new customer account.
        Returns the new Customer, or None if the email is already in use.
        """
        if Customer.find_by_email(email):
            return None

        customer = Customer(
            name=name,
            email=email,
            password_hash=Customer.hash_password(password),
            address=address
        )
        customer.save()
        return customer

    @staticmethod
    def login(email, password):
        """
        Checks email and hashed password against stored customers.
        Returns the matching Customer, or None if credentials are invalid.
        """
        customer = Customer.find_by_email(email)
        if customer and customer.password_hash == Customer.hash_password(password):
            return customer
        return None

    def add_order_id(self, order_id):
        """Links an order ID to this customer's history and saves."""
        self.order_ids.append(order_id)
        self.save()

    # Serialisation
    def to_dict(self):
        """Converts the customer to a dictionary for JSON storage."""
        return {
            "customer_id": self.customer_id,
            "name": self.name,
            "email": self.email,
            "password_hash": self.password_hash,
            "address": self.address,
            "order_ids": self.order_ids
        }

    @classmethod
    def from_dict(cls, data):
        """Creates a Customer instance from a dictionary (e.g. loaded from JSON)."""
        return cls(
            customer_id=data.get("customer_id"),
            name=data.get("name"),
            email=data.get("email"),
            password_hash=data.get("password_hash", ""),
            address=data.get("address", ""),
            order_ids=data.get("order_ids", [])
        )

    # JSON persistence helpers
    @staticmethod
    def load_all():
        """Loads all customers from the JSON file. Returns a list of Customer objects."""
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
            return [Customer.from_dict(c) for c in data]
        except FileNotFoundError:
            return []

    @staticmethod
    def save_all(customers):
        """Saves a list of Customer objects to the JSON file."""
        with open(DATA_FILE, 'w') as f:
            json.dump([c.to_dict() for c in customers], f, indent=2)

    @staticmethod
    def find_by_id(customer_id):
        """Finds and returns a single Customer by ID, or None if not found."""
        for customer in Customer.load_all():
            if customer.customer_id == customer_id:
                return customer
        return None

    @staticmethod
    def find_by_email(email):
        """Finds and returns a single Customer by email, or None if not found."""
        for customer in Customer.load_all():
            if customer.email == email:
                return customer
        return None

    def save(self):
        """Saves or updates this customer in the JSON file."""
        customers = Customer.load_all()

        # Replace existing entry if it exists, otherwise append
        for i, c in enumerate(customers):
            if c.customer_id == self.customer_id:
                customers[i] = self
                Customer.save_all(customers)
                return

        customers.append(self)
        Customer.save_all(customers)
