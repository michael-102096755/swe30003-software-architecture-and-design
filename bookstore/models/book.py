"""
book.py - Book model for the Online Bookstore System.

Represents an individual product in the catalogue.
Follows the CRC design from Assignment 2 (Section 3.3.7).

Coding standard: PEP 8 (https://peps.python.org/pep-0008/)
"""


class Book:
    """
    Data-holder class representing an individual product in the catalogue.

    Responsibilities (from CRC):
        - Store book metadata (title, author, ISBN, publisher, year)
        - Store pricing information
        - Store stock quantity
        - Store category/genre
        - Check availability of the book
    """

    def __init__(self, book_id, title, author, publisher,
                 year, category, price, stock):
        """
        Initialise a Book instance.

        Args:
            book_id (str): Unique identifier (ISBN).
            title (str): Title of the book.
            author (str): Author name.
            publisher (str): Publisher name.
            year (int): Publication year.
            category (str): Genre or category.
            price (float): Selling price in AUD.
            stock (int): Current stock quantity.
        """
        self._book_id = book_id
        self._title = title
        self._author = author
        self._publisher = publisher
        self._year = year
        self._category = category
        self._price = price
        self._stock = stock

    # ------------------------------------------------------------------ #
    # Properties                                                           #
    # ------------------------------------------------------------------ #

    @property
    def book_id(self):
        return self._book_id

    @property
    def title(self):
        return self._title

    @property
    def author(self):
        return self._author

    @property
    def publisher(self):
        return self._publisher

    @property
    def year(self):
        return self._year

    @property
    def category(self):
        return self._category

    @property
    def price(self):
        return self._price

    @property
    def stock(self):
        return self._stock

    # ------------------------------------------------------------------ #
    # Responsibilities                                                     #
    # ------------------------------------------------------------------ #

    def is_available(self, quantity=1):
        """
        Check whether sufficient stock is available.

        Args:
            quantity (int): Desired quantity.

        Returns:
            bool: True if stock >= quantity.
        """
        return self._stock >= quantity

    def reduce_stock(self, quantity):
        """
        Deduct stock after a confirmed order.

        Args:
            quantity (int): Quantity to deduct.

        Raises:
            ValueError: If quantity exceeds available stock.
        """
        if quantity > self._stock:
            raise ValueError(
                f"Insufficient stock for '{self._title}'. "
                f"Available: {self._stock}, Requested: {quantity}."
            )
        self._stock -= quantity

    def restore_stock(self, quantity):
        """
        Restore stock when an order item is removed or cancelled.

        Args:
            quantity (int): Quantity to restore.
        """
        self._stock += quantity

    def display(self):
        """Print a formatted summary of the book."""
        print(f"  ISBN      : {self._book_id}")
        print(f"  Title     : {self._title}")
        print(f"  Author    : {self._author}")
        print(f"  Publisher : {self._publisher}")
        print(f"  Year      : {self._year}")
        print(f"  Category  : {self._category}")
        print(f"  Price     : AUD ${self._price:.2f}")
        status = (
            f"In Stock ({self._stock} available)"
            if self._stock > 0 else "Out of Stock"
        )
        print(f"  Stock     : {status}")

    # ------------------------------------------------------------------ #
    # Serialisation                                                        #
    # ------------------------------------------------------------------ #

    def to_dict(self):
        """Serialise to dictionary for JSON persistence."""
        return {
            "book_id": self._book_id,
            "title": self._title,
            "author": self._author,
            "publisher": self._publisher,
            "year": self._year,
            "category": self._category,
            "price": self._price,
            "stock": self._stock,
        }

    @classmethod
    def from_dict(cls, data):
        """Deserialise a Book from a dictionary."""
        return cls(
            book_id=data["book_id"],
            title=data["title"],
            author=data["author"],
            publisher=data["publisher"],
            year=data["year"],
            category=data["category"],
            price=data["price"],
            stock=data["stock"],
        )

    def __repr__(self):
        return (
            f"Book(id={self._book_id!r}, title={self._title!r}, "
            f"price={self._price}, stock={self._stock})"
        )
