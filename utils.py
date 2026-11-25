"""
utils.py

This file holds small helper functions used across the application:

    - Validation functions that check user input and raise a clear
      error message if something is wrong.
    - Formatting functions that turn raw numbers into nicely
      displayed text (e.g. "4500.0" -> "NGN 4,500.00"), including
      pixel-aligned accounting currency strings for tables.

Keeping these helpers in one file means every page (products.py,
sales.py, etc.) checks input the exact same way. I would never use the
same validation logic twice.
"""


class ValidationError(Exception):
    """
    Raised when user input fails a validation check.

    I use a custom exception (instead of a generic one) so that the
    rest of the program can catch ValidationError specifically and
    show the message to the user in a friendly pop-up, instead of
    letting a confusing traceback appear.
    """

    pass


def validate_product_name(
    name: str,
    existing_names: list[str],
    ignore_name: str | None = None,
) -> str:
    """
    Check that a product name is not blank and not a duplicate.

    Args:
        name: The name typed by the user.
        existing_names: A list of product names already in the inventory.
        ignore_name: Optional existing name to ignore during duplicate checks
            (used when editing an existing product without renaming it).

    Returns:
        The cleaned-up (trimmed) name, ready to be stored.

    Raises:
        ValidationError: If the name is blank or already exists.
    """
    cleaned_name = name.strip()

    if cleaned_name == "":
        raise ValidationError("Please enter a product name.")

    ignore_lower = ignore_name.lower() if ignore_name is not None else None
    lower_existing_names = [
        existing.lower()
        for existing in existing_names
        if existing.lower() != ignore_lower
    ]
    if cleaned_name.lower() in lower_existing_names:
        raise ValidationError(f'"{cleaned_name}" already exists in inventory.')

    return cleaned_name


def validate_price(price_text: str) -> float:
    """
    Check that the price typed by the user is a valid, non-negative number.

    Args:
        price_text: The raw text typed into the price field.

    Returns:
        The price as a float.

    Raises:
        ValidationError: If the text is not a number, or the number is negative.
    """
    cleaned = price_text.strip().replace(",", "")
    try:
        price = float(cleaned)
    except ValueError:
        raise ValidationError("Price must be a number, e.g. 4500.")

    if price < 0:
        raise ValidationError("Price cannot be negative.")

    return price


def validate_quantity(quantity_text: str) -> int:
    """
    Check that the quantity typed by the user is a valid, non-negative whole number.

    Args:
        quantity_text: The raw text typed into the quantity field.

    Returns:
        The quantity as an int.

    Raises:
        ValidationError: If the text is not a whole number, or it is negative.
    """
    try:
        quantity = int(quantity_text.strip())
    except ValueError:
        raise ValidationError("Quantity must be a whole number, e.g. 20.")

    if quantity < 0:
        raise ValidationError("Quantity cannot be negative.")

    return quantity


def validate_sale_quantity(quantity_text: str, stock_available: int) -> int:
    """
    Check that a sale quantity is valid AND that enough stock is available.

    Args:
        quantity_text: The raw text typed into the "quantity sold" field.
        stock_available: How many units are currently in stock.

    Returns:
        The quantity to sell, as an int.

    Raises:
        ValidationError: If the quantity is invalid, zero, or more than
            what is currently in stock.
    """
    quantity = validate_quantity(quantity_text)

    if quantity == 0:
        raise ValidationError("Please enter a quantity greater than zero.")

    if quantity > stock_available:
        raise ValidationError(
            f"Only {stock_available} in stock. Sale not recorded."
        )

    return quantity


def format_currency(amount: float) -> str:
    """
    Format a number as Nigerian Naira currency text.

    Example:
        format_currency(4500) -> "NGN 4,500.00"
    """
    return f"NGN {amount:,.2f}"


def format_currency_aligned(amount: float, reference_amount: float = 0.0) -> str:
    """
    Format Nigerian Naira currency for accounting tables so that EVERY 'NGN'
    prefix aligns vertically on the left AND every decimal/digit aligns
    vertically on the right — regardless of how many digits the amount has.

    Uses Unicode Figure Space (U+2007, exact width of a tabular digit in
    Segoe UI) and Punctuation Space (U+2008, exact width of a comma).
    """
    target = max(abs(amount), abs(reference_amount), 9999.0)
    template = f"{target:,.2f}"
    formatted = f"{amount:,.2f}"

    if len(formatted) >= len(template):
        return f"NGN {formatted}"

    missing = template[: len(template) - len(formatted)]
    padding = "".join("\u2008" if ch == "," else "\u2007" for ch in missing)
    return f"NGN {padding}{formatted}"


def format_quantity(quantity: int) -> str:
    """
    Format a quantity for display. Kept as its own function so that,
    if we ever want to add units (e.g. "15 units"), we only change
    this one place.
    """
    return str(quantity)
