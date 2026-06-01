"""
book.py - SWE30003 - Assignment 3 - Gian Tze Ee, 105220081
"""
import json
import uuid

# Path to the books JSON file
DATA_FILE = "data/books.json"


class Book:
    """
    Represents a single book product in the catalogue.
    Acts as a data holder for book metadata, pricing, and stock.

        Responsibilities (from CRC):
        - Store book metadata (title, author, ISBN, publisher, year)
        - Store pricing information
        - Store stock quantity
        - Store category/genre
        - Check availability of the book
    """

    def __init__(self, title, author, isbn, price, stock,
                 category="", publisher="", year=None, book_id=None):
        self.book_id = book_id or str(uuid.uuid4())
        self.title = title
        self.author = author
        self.isbn = isbn
        self.publisher = publisher
        self.year = year
        self.price = price
        self.stock = stock
        self.category = category

    def is_available(self):
        """Returns True if the book has stock remaining."""
        return self.stock > 0

    def to_dict(self):
        """Converts the book to a dictionary for JSON storage."""
        return {
            "book_id": self.book_id,
            "title": self.title,
            "author": self.author,
            "isbn": self.isbn,
            "publisher": self.publisher,
            "year": self.year,
            "price": self.price,
            "stock": self.stock,
            "category": self.category
        }

    @classmethod
    def from_dict(cls, data):
        """Creates a Book instance from a dictionary (e.g. loaded from JSON)."""
        return cls(
            book_id=data.get("book_id"),
            title=data.get("title"),
            author=data.get("author"),
            isbn=data.get("isbn"),
            publisher=data.get("publisher", ""),
            year=data.get("year"),
            price=data.get("price"),
            stock=data.get("stock", 0),
            category=data.get("category", "")
        )

    # JSON persistence helpers
    @staticmethod
    def load_all():
        """Loads all books from the JSON file. Returns a list of Book objects."""
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
            return [Book.from_dict(b) for b in data]
        except FileNotFoundError:
            return []

    @staticmethod
    def save_all(books):
        """Saves a list of Book objects to the JSON file."""
        with open(DATA_FILE, 'w') as f:
            json.dump([b.to_dict() for b in books], f, indent=2)

    @staticmethod
    def find_by_id(book_id):
        """Finds and returns a single Book by its ID, or None if not found."""
        for book in Book.load_all():
            if book.book_id == book_id:
                return book
        return None

    def save(self):
        """Saves or updates this book in the JSON file."""
        books = Book.load_all()

        # Replace existing entry if it exists, otherwise append
        for i, b in enumerate(books):
            if b.book_id == self.book_id:
                books[i] = self
                Book.save_all(books)
                return

        books.append(self)
        Book.save_all(books)
