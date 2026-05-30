"""
book.py - Book class for the Online Bookstore System
Coding standard: PEP 8 (https://peps.python.org/pep-0008/)
"""


class Book:
    """
    Data-holder representing an individual product in the catalogue.
    Contains all descriptive and pricing information.
    CRC Reference: Section 3.3.7
    """

    def __init__(self, isbn: str, title: str, author: str, publisher: str,
                 year: int, category: str, price: float, stock: int):
        """
        Initialise a Book with metadata, pricing, and stock information.

        Args:
            isbn: Unique identifier for the book.
            title: Title of the book.
            author: Author of the book.
            publisher: Publisher name.
            year: Publication year.
            category: Genre or category.
            price: Price in AUD.
            stock: Available stock quantity.
        """
        if not isbn or not isbn.strip():
            raise ValueError("ISBN cannot be blank.")
        if not title or not title.strip():
            raise ValueError("Title cannot be blank.")
        if not author or not author.strip():
            raise ValueError("Author cannot be blank.")
        if price < 0:
            raise ValueError("Price cannot be negative.")
        if stock < 0:
            raise ValueError("Stock cannot be negative.")

        self._isbn = isbn.strip()
        self._title = title.strip()
        self._author = author.strip()
        self._publisher = publisher.strip()
        self._year = year
        self._category = category.strip()
        self._price = price
        self._stock = stock

    # --- Getters ---

    @property
    def isbn(self) -> str:
        return self._isbn

    @property
    def title(self) -> str:
        return self._title

    @property
    def author(self) -> str:
        return self._author

    @property
    def publisher(self) -> str:
        return self._publisher

    @property
    def year(self) -> int:
        return self._year

    @property
    def category(self) -> str:
        return self._category

    @property
    def price(self) -> float:
        return self._price

    @property
    def stock(self) -> int:
        return self._stock

    # --- Setters for mutable fields ---

    @price.setter
    def price(self, value: float):
        if value < 0:
            raise ValueError("Price cannot be negative.")
        self._price = value

    @stock.setter
    def stock(self, value: int):
        if value < 0:
            raise ValueError("Stock cannot be negative.")
        self._stock = value

    @property
    def title_lower(self) -> str:
        return self._title.strip()

    def is_available(self) -> bool:
        """Check if the book is currently in stock."""
        return self._stock > 0

    def reduce_stock(self, quantity: int):
        """
        Reduce stock by the given quantity after a confirmed order.

        Args:
            quantity: Number of copies to deduct.

        Raises:
            ValueError: If quantity exceeds available stock.
        """
        if quantity > self._stock:
            raise ValueError(
                f"Insufficient stock for '{self._title}'. "
                f"Available: {self._stock}, Requested: {quantity}."
            )
        self._stock -= quantity

    def restore_stock(self, quantity: int):
        """Restore stock when an order is cancelled."""
        self._stock += quantity

    def to_dict(self) -> dict:
        """Serialise book to a dictionary for JSON storage."""
        return {
            "isbn": self._isbn,
            "title": self._title,
            "author": self._author,
            "publisher": self._publisher,
            "year": self._year,
            "category": self._category,
            "price": self._price,
            "stock": self._stock,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Book":
        """Deserialise a Book from a dictionary."""
        return cls(
            isbn=data["isbn"],
            title=data["title"],
            author=data["author"],
            publisher=data["publisher"],
            year=data["year"],
            category=data["category"],
            price=data["price"],
            stock=data["stock"],
        )

    def display(self) -> str:
        """Return a formatted single-line summary of the book."""
        stock_label = f"{self._stock} in stock" if self._stock > 0 else "OUT OF STOCK"
        return (
            f"[{self._isbn}] {self._title} by {self._author} "
            f"| {self._category} | ${self._price:.2f} | {stock_label}"
        )

    def __repr__(self) -> str:
        return f"Book(isbn={self._isbn!r}, title={self._title!r})"
