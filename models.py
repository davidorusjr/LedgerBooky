"""
models.py

This file defines the two kinds of data our application works with:

    Product  -> something a shop sells (e.g. "Indomie (carton)")
    Sale     -> a single record of a product being sold

These classes only hold data and a few small helper methods. They do not
read or write files, and they do not build any user interface. Keeping
them simple makes them easy to explain and easy to test.
"""

from dataclasses import dataclass


@dataclass
class Product:
    """
    Represents one product in the shop's inventory.

    Attributes:
        name: The product's name, e.g. "Indomie (carton)".
        price: The price of one unit, in Naira.
        quantity: How many units are currently in stock.
    """

    name: str
    price: float
    quantity: int

    def total_value(self) -> float:
        """Return the total value of this product's stock (price x quantity)."""
        return self.price * self.quantity

    def is_out_of_stock(self) -> bool:
        """Return True if there are zero units left."""
        return self.quantity <= 0

    def is_low_stock(self, threshold: int) -> bool:
        """
        Return True if the quantity is below the given threshold,
        but still greater than zero (zero means "out of stock", not "low").
        """
        return 0 < self.quantity < threshold


@dataclass
class Sale:
    """
    Represents one completed sale.

    Attributes:
        date: The date the sale happened, formatted as YYYY-MM-DD.
        time: The time the sale happened, formatted as HH:MM:SS.
        product_name: The name of the product that was sold.
        quantity: How many units were sold in this transaction.
        amount: The total amount paid (price x quantity at time of sale).
    """

    date: str
    time: str
    product_name: str
    quantity: int
    amount: float
