"""
catalogue.py - Catalogue model for the Online Bookstore System.

Manages the collection of books available for sale.
Follows the CRC design from Assignment 2 (Section 3.3.6).

Coding standard: PEP 8 (https://peps.python.org/pep-0008/)
"""

import json
import os
from models.book import Book


class Catalogue:
    """
    Manages the collection of books available in the online bookstore.

    Responsibilities (from CRC):
        - Maintain collection of available books
        - Search books by keyword (title, author, category)
        - Filter books by category, price range
        - Check if a book is in stock
        - Get book details by ID
    """

    def __init__(self, data_path="data/books.json"):
        """
        Initialise the Catalogue and load books from JSON.

        Args:
            data_path (str): Path to the books JSON file.
        """
        self._data_path = data_path
        self._books = {}  # book_id -> Book
        self._load_books()

    # ------------------------------------------------------------------ #
    # Loading                                                              #
    # ------------------------------------------------------------------ #

    def _load_books(self):
        """Load books from the JSON data file into memory."""
        if not os.path.exists(self._data_path):
            print(f"[WARNING] Books data file not found: {self._data_path}")
            return
        with open(self._data_path, "r", encoding="utf-8") as f:
            book_list = json.load(f)
        for item in book_list:
            book = Book.from_dict(item)
            self._books[book.book_id] = book

    def save_books(self):
        """Persist current book stock levels back to JSON."""
        data = [book.to_dict() for book in self._books.values()]
        with open(self._data_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # ------------------------------------------------------------------ #
    # Responsibilities                                                     #
    # ------------------------------------------------------------------ #

    def get_all_books(self):
        """
        Return all books in the catalogue.

        Returns:
            list[Book]: All Book objects.
        """
        return list(self._books.values())

    def get_book_by_id(self, book_id):
        """
        Retrieve a book by its unique ID.

        Args:
            book_id (str): The book's ISBN or ID.

        Returns:
            Book or None: The matching Book, or None if not found.
        """
        return self._books.get(book_id)

    def search_books(self, keyword):
        """
        Search books by keyword across title, author, and category.

        Args:
            keyword (str): Search term (case-insensitive).

        Returns:
            list[Book]: Books matching the keyword.
        """
        keyword_lower = keyword.strip().lower()
        results = []
        for book in self._books.values():
            if (
                keyword_lower in book.title.lower()
                or keyword_lower in book.author.lower()
                or keyword_lower in book.category.lower()
            ):
                results.append(book)
        return results

    def filter_by_category(self, category):
        """
        Filter books by exact category (case-insensitive).

        Args:
            category (str): Category to filter by.

        Returns:
            list[Book]: Books in the specified category.
        """
        category_lower = category.strip().lower()
        return [
            b for b in self._books.values()
            if b.category.lower() == category_lower
        ]

    def filter_by_price_range(self, min_price, max_price):
        """
        Filter books within a price range.

        Args:
            min_price (float): Minimum price (inclusive).
            max_price (float): Maximum price (inclusive).

        Returns:
            list[Book]: Books within the price range.
        """
        return [
            b for b in self._books.values()
            if min_price <= b.price <= max_price
        ]

    def is_in_stock(self, book_id, quantity=1):
        """
        Check if a specific book has sufficient stock.

        Args:
            book_id (str): The book's ID.
            quantity (int): Required quantity.

        Returns:
            bool: True if available, False otherwise.
        """
        book = self.get_book_by_id(book_id)
        if book is None:
            return False
        return book.is_available(quantity)

    def get_categories(self):
        """
        Return all unique categories in the catalogue.

        Returns:
            list[str]: Sorted list of unique categories.
        """
        return sorted({b.category for b in self._books.values()})

    def display_books(self, books=None):
        """
        Print a numbered list of books.

        Args:
            books (list[Book], optional): Books to display.
                Defaults to all books.
        """
        if books is None:
            books = self.get_all_books()
        if not books:
            print("  No books found.")
            return
        print(f"  {'#':<4} {'Title':<42} {'Author':<25} "
              f"{'Category':<20} {'Price':>8}  {'Stock':>5}")
        print("  " + "-" * 110)
        for i, book in enumerate(books, start=1):
            title = (book.title[:39] + "...") if len(book.title) > 42 else book.title
            author = (book.author[:22] + "...") if len(book.author) > 25 else book.author
            category = (book.category[:17] + "...") if len(book.category) > 20 else book.category
            stock_display = str(book.stock) if book.stock > 0 else "N/A"
            print(f"  {i:<4} {title:<42} {author:<25} "
                  f"{category:<20} ${book.price:>7.2f}  {stock_display:>5}")
