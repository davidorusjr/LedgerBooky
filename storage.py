"""
storage.py

This file is the only place in the application that reads from or
writes to CSV and settings files. Every other module asks storage.py
for data — no other file should open inventory.csv, sales.csv, or
settings.json directly.

Why this matters:
If I ever change how data is saved (for example, switching from CSV
to a database), I would only need to change this one file.

This file defines:
    InventoryStore        -> keeps track of all Products, loads/saves inventory.csv
    SalesStore            -> keeps track of all Sales, loads/saves sales.csv
    load_theme_preference -> loads saved Light/Dark preference (offline persistence)
    save_theme_preference -> saves Light/Dark preference to settings.json
"""

import csv
import json
import os
from datetime import datetime

from constants import (
    INVENTORY_FILE_PATH,
    INVENTORY_CSV_HEADERS,
    SALES_FILE_PATH,
    SALES_CSV_HEADERS,
    SETTINGS_FILE_PATH,
)
from models import Product, Sale


class InventoryStore:
    """
    Holds every Product in memory and keeps inventory.csv up to date.

    The rest of the application should only talk to InventoryStore -
    never to inventory.csv directly.
    """

    def __init__(self, file_path: str = INVENTORY_FILE_PATH):
        self.file_path = file_path
        self.products: dict[str, Product] = {}
        self.load()

    def load(self) -> None:
        """
        Load all products from the CSV file into memory.

        If the file does not exist yet, create an empty one instead
        of crashing.
        """
        if not os.path.exists(self.file_path):
            self._create_empty_file()
            return

        with open(self.file_path, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                product = Product(
                    name=row["name"],
                    price=float(row["price"]),
                    quantity=int(row["quantity"]),
                )
                self.products[product.name] = product

    def save(self) -> None:
        """
        Write every product currently in memory back to the CSV file,
        sorted alphabetically so the CSV stays neat and readable.

        This is called automatically after any change (add, edit, delete,
        sell, restock) so the user never has to save manually.
        """
        with open(self.file_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(INVENTORY_CSV_HEADERS)
            for product in self.get_all_products():
                writer.writerow([
                    product.name,
                    f"{product.price:.2f}",
                    product.quantity,
                ])

    def _create_empty_file(self) -> None:
        """Create a new CSV file containing only the header row."""
        with open(self.file_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(INVENTORY_CSV_HEADERS)

    def add_product(self, name: str, price: float, quantity: int) -> None:
        """Add a brand new product and save it to disk immediately."""
        self.products[name] = Product(name=name, price=price, quantity=quantity)
        self.save()

    def update_product(
        self,
        original_name: str,
        new_name: str,
        new_price: float,
        new_quantity: int,
    ) -> Product:
        """Update an existing product's name, price, or quantity and save."""
        if original_name in self.products and original_name != new_name:
            del self.products[original_name]
        updated = Product(name=new_name, price=new_price, quantity=new_quantity)
        self.products[new_name] = updated
        self.save()
        return updated

    def delete_product(self, name: str) -> bool:
        """Remove a product from inventory and save immediately."""
        if name not in self.products:
            return False
        del self.products[name]
        self.save()
        return True

    def get_all_products(self) -> list[Product]:
        """Return every product, sorted alphabetically by name."""
        return sorted(self.products.values(), key=lambda product: product.name.lower())

    def get_product_names(self) -> list[str]:
        """Return sorted product names (used for dropdowns and duplicate checks)."""
        return [product.name for product in self.get_all_products()]

    def reduce_stock(self, name: str, quantity_sold: int) -> Product:
        """
        Reduce a product's stock after a sale and save to disk.

        Assumes the caller has already checked that enough stock is
        available (see utils.validate_sale_quantity).
        """
        product = self.products[name]
        product.quantity -= quantity_sold
        self.save()
        return product

    def restock_product(self, name: str, quantity_to_add: int) -> Product:
        """Increase a product's stock (e.g. after a delivery) and save to disk."""
        product = self.products[name]
        product.quantity += quantity_to_add
        self.save()
        return product

    def count_low_stock(self, threshold: int) -> int:
        """Return how many products are currently below the low-stock threshold."""
        return sum(1 for product in self.products.values() if product.is_low_stock(threshold))

    def get_alert_products(self, threshold: int) -> list[Product]:
        """
        Return products that are Out of Stock or Low Stock, ordered with
        the most urgent (lowest quantity, then alphabetical) first.
        """
        alerts = [
            product
            for product in self.products.values()
            if product.is_out_of_stock() or product.is_low_stock(threshold)
        ]
        return sorted(alerts, key=lambda p: (p.quantity, p.name.lower()))

    def total_units_in_stock(self) -> int:
        """Return the total number of units across all products."""
        return sum(product.quantity for product in self.products.values())

    def total_inventory_value(self) -> float:
        """Return the combined monetary value of all stock on hand."""
        return sum(product.total_value() for product in self.products.values())


class SalesStore:
    """
    Holds every Sale ever recorded in memory and keeps sales.csv up to date.
    """

    def __init__(self, file_path: str = SALES_FILE_PATH):
        self.file_path = file_path
        self.sales: list[Sale] = []
        self.load()

    def load(self) -> None:
        """Load every past sale from the CSV file into memory."""
        if not os.path.exists(self.file_path):
            self._create_empty_file()
            return

        with open(self.file_path, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                sale = Sale(
                    date=row["date"],
                    time=row["time"],
                    product_name=row["product"],
                    quantity=int(row["quantity"]),
                    amount=float(row["amount"]),
                )
                self.sales.append(sale)

    def save(self) -> None:
        """Write every sale currently in memory back to the CSV file."""
        with open(self.file_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(SALES_CSV_HEADERS)
            for sale in self.sales:
                writer.writerow([
                    sale.date,
                    sale.time,
                    sale.product_name,
                    sale.quantity,
                    f"{sale.amount:.2f}",
                ])

    def _create_empty_file(self) -> None:
        """Create a new CSV file containing only the header row."""
        with open(self.file_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(SALES_CSV_HEADERS)

    def add_sale(self, product_name: str, quantity: int, amount: float) -> Sale:
        """Create a new Sale record stamped with the current date/time, and save it."""
        now = datetime.now()
        sale = Sale(
            date=now.strftime("%Y-%m-%d"),
            time=now.strftime("%H:%M:%S"),
            product_name=product_name,
            quantity=quantity,
            amount=amount,
        )
        self.sales.append(sale)
        self.save()
        return sale

    def delete_sale(self, target_sale: Sale) -> bool:
        """Remove a specific sale record (e.g. when voiding a mistake) and save."""
        for index, sale in enumerate(self.sales):
            if sale is target_sale or sale == target_sale:
                self.sales.pop(index)
                self.save()
                return True
        return False

    def export_to_csv(self, export_path: str) -> None:
        """Export the full sales log (most recent first) to a chosen CSV file."""
        with open(export_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(SALES_CSV_HEADERS)
            for sale in self.get_all_sales():
                writer.writerow([
                    sale.date,
                    sale.time,
                    sale.product_name,
                    sale.quantity,
                    f"{sale.amount:.2f}",
                ])

    def get_all_sales(self) -> list[Sale]:
        """Return every sale sorted chronologically, most recent first."""
        return sorted(
            self.sales,
            key=lambda sale: (sale.date, sale.time),
            reverse=True,
        )

    def get_today_sales(self) -> list[Sale]:
        """Return only the sales that happened today."""
        today = datetime.now().strftime("%Y-%m-%d")
        return [sale for sale in self.sales if sale.date == today]

    def get_today_total(self) -> float:
        """Return the total amount earned from today's sales."""
        return sum(sale.amount for sale in self.get_today_sales())

    def get_total_revenue(self) -> float:
        """Return the combined amount earned across all recorded sales."""
        return sum(sale.amount for sale in self.sales)

    def get_best_selling_product(self) -> str | None:
        """
        Return the name of the product with the highest total quantity sold.

        Returns None if no sales have been recorded yet.
        """
        if not self.sales:
            return None

        totals_by_product: dict[str, int] = {}
        for sale in self.sales:
            totals_by_product[sale.product_name] = (
                totals_by_product.get(sale.product_name, 0) + sale.quantity
            )

        return max(totals_by_product, key=totals_by_product.get)


def load_theme_preference(file_path: str = SETTINGS_FILE_PATH) -> bool:
    """Return True if Dark Mode was last enabled, defaulting to False (Light Mode)."""
    if not os.path.exists(file_path):
        return False
    try:
        with open(file_path, mode="r", encoding="utf-8") as file:
            data = json.load(file)
            return bool(data.get("dark_mode", False))
    except (OSError, ValueError, TypeError):
        return False


def save_theme_preference(is_dark: bool, file_path: str = SETTINGS_FILE_PATH) -> None:
    """Save the user's Light/Dark theme preference locally for the next launch."""
    try:
        with open(file_path, mode="w", encoding="utf-8") as file:
            json.dump({"dark_mode": is_dark}, file, indent=2)
    except OSError:
        pass
