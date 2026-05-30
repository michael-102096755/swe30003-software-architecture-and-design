"""
catalogue.py - Catalogue class for the Online Bookstore System
Coding standard: PEP 8 (https://peps.python.org/pep-0008/)
"""

from typing import List, Optional
from book import Book


class Catalogue:
    """
    Manages the collection of books available for sale.
    Supports search by keyword, filter by category/price, and stock checks.
    CRC Reference: Section 3.3.6
    """

    def __init__(self):
        """Initialise an empty catalogue."""
        self._books: dict[str, Book] = {}  # keyed by ISBN

    # --- Book management (called via Manage class) ---

    def add_book(self, book: Book) -> bool:
        """
        Add a new book to the catalogue.

        Args:
            book: Book instance to add.

        Returns:
            True if added, False if ISBN already exists.
        """
        if book.isbn in self._books:
            return False
        self._books[book.isbn] = book
        return True

    def remove_book(self, isbn: str) -> bool:
        """
        Remove a book from the catalogue by ISBN.

        Returns:
            True if removed, False if not found.
        """
        if isbn in self._books:
            del self._books[isbn]
            return True
        return False

    def update_book(self, isbn: str, **kwargs) -> bool:
        """
        Update fields of an existing book.

        Args:
            isbn: ISBN of the book to update.
            **kwargs: Fields to update (price, stock, title, etc.)

        Returns:
            True if updated, False if not found.
        """
        book = self._books.get(isbn)
        if not book:
            return False
        if "price" in kwargs:
            book.price = kwargs["price"]
        if "stock" in kwargs:
            book.stock = kwargs["stock"]
        return True

    # --- Customer-facing methods ---

    def get_book_by_isbn(self, isbn: str) -> Optional[Book]:
        """Retrieve a book by its ISBN."""
        return self._books.get(isbn)

    def search(self, keyword: str) -> List[Book]:
        """
        Search books by keyword matching title, author, or ISBN.

        Args:
            keyword: Search string (case-insensitive).

        Returns:
            List of matching Book objects.
        """
        keyword = keyword.strip().lower()
        if not keyword:
            return list(self._books.values())
        results = []
        for book in self._books.values():
            if (keyword in book.title.lower()
                    or keyword in book.author.lower()
                    or keyword in book.isbn.lower()):
                results.append(book)
        return results

    def filter_by_category(self, category: str) -> List[Book]:
        """Filter books by category (case-insensitive)."""
        category = category.strip().lower()
        return [b for b in self._books.values()
                if b.category.lower() == category]

    def filter_by_price_range(self, min_price: float,
                               max_price: float) -> List[Book]:
        """Filter books within a price range (inclusive)."""
        return [b for b in self._books.values()
                if min_price <= b.price <= max_price]

    def get_all_books(self) -> List[Book]:
        """Return all books in the catalogue."""
        return list(self._books.values())

    def get_available_books(self) -> List[Book]:
        """Return only books currently in stock."""
        return [b for b in self._books.values() if b.is_available()]

    def get_categories(self) -> List[str]:
        """Return a sorted list of unique categories in the catalogue."""
        return sorted(set(b.category for b in self._books.values()))

    def is_in_stock(self, isbn: str, quantity: int = 1) -> bool:
        """Check if a specific quantity of a book is available."""
        book = self._books.get(isbn)
        return book is not None and book.stock >= quantity

    # --- Serialisation ---

    def to_dict(self) -> dict:
        """Serialise catalogue to a dictionary for JSON storage."""
        return {isbn: book.to_dict() for isbn, book in self._books.items()}

    def load_from_dict(self, data: dict):
        """Load catalogue from a dictionary (e.g., from JSON)."""
        self._books = {
            isbn: Book.from_dict(book_data)
            for isbn, book_data in data.items()
        }

    def __len__(self) -> int:
        return len(self._books)
