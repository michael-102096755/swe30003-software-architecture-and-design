"""
payment.py - Payment Strategy pattern for the Online Bookstore System
Coding standard: PEP 8 (https://peps.python.org/pep-0008/)

Implements the Strategy pattern from Assignment 2 Section 5.2.1:
  - PaymentStrategy (abstract base)
  - CreditCardPayment
  - PayPalPayment
"""

from abc import ABC, abstractmethod


class PaymentStrategy(ABC):
    """
    Abstract base class defining the payment-processing interface.
    Strategy Pattern: Context (Order) uses this interface.
    CRC Reference: Section 5.2.1
    """

    @abstractmethod
    def process(self, amount: float, customer_name: str) -> bool:
        """
        Process payment for the given amount.

        Args:
            amount: Total amount to charge in AUD.
            customer_name: Name of the customer for display purposes.

        Returns:
            True if payment succeeded, False otherwise.
        """

    @abstractmethod
    def get_name(self) -> str:
        """Return the display name of this payment method."""


class CreditCardPayment(PaymentStrategy):
    """
    Concrete strategy for credit/debit card payment.
    Simulates payment processing as per assignment spec
    (actual payment processing not required).
    """

    def __init__(self, card_number: str, expiry: str, cvv: str):
        """
        Initialise with card details.

        Args:
            card_number: 16-digit card number (last 4 stored only).
            expiry: Expiry date in MM/YY format.
            cvv: 3-digit CVV (not stored after validation).
        """
        if len(card_number.replace(" ", "")) != 16:
            raise ValueError("Card number must be 16 digits.")
        if not expiry or len(expiry) != 5 or expiry[2] != "/":
            raise ValueError("Expiry must be in MM/YY format.")
        if len(cvv) != 3 or not cvv.isdigit():
            raise ValueError("CVV must be 3 digits.")
        self._last_four = card_number.replace(" ", "")[-4:]
        self._expiry = expiry

    def process(self, amount: float, customer_name: str) -> bool:
        """Simulate credit card payment processing."""
        print(f"\n  [Payment Gateway] Processing credit card payment...")
        print(f"  [Payment Gateway] Card ending in {self._last_four} "
              f"| Expiry: {self._expiry}")
        print(f"  [Payment Gateway] Charging ${amount:.2f} AUD to {customer_name}...")
        print(f"  [Payment Gateway] ✓ Payment authorised successfully.")
        return True

    def get_name(self) -> str:
        return f"Credit Card (ending {self._last_four})"


class PayPalPayment(PaymentStrategy):
    """
    Concrete strategy for PayPal payment.
    Simulates PayPal payment flow as per assignment spec.
    """

    def __init__(self, email: str):
        """
        Initialise with PayPal account email.

        Args:
            email: PayPal account email address.
        """
        if "@" not in email or "." not in email:
            raise ValueError("Please enter a valid PayPal email address.")
        self._email = email

    def process(self, amount: float, customer_name: str) -> bool:
        """Simulate PayPal payment processing."""
        print(f"\n  [PayPal] Connecting to PayPal...")
        print(f"  [PayPal] Account: {self._email}")
        print(f"  [PayPal] Authorising ${amount:.2f} AUD for {customer_name}...")
        print(f"  [PayPal] ✓ Payment approved. Transaction reference: "
              f"PP-{id(self):X}")
        return True

    def get_name(self) -> str:
        return f"PayPal ({self._email})"
