"""
sales.py

This file defines the Sales page. It lets the user:

    - Choose an existing product from an alphabetically sorted rounded dropdown.
    - See the unit price, available stock, and live total BEFORE confirming.
    - Type how many units were sold and press Enter or click "Record Sale".
    - Review the receipt of the last completed sale right beside the preview.
"""

import tkinter as tk
from tkinter import messagebox

from constants import (
    FONT_FAMILY_BODY,
    FONT_SIZE_HEADING,
    FONT_SIZE_BODY,
    LOW_STOCK_THRESHOLD,
    PADDING_SMALL,
    PADDING_MEDIUM,
    PADDING_LARGE,
    RADIUS_BUTTON,
    RADIUS_CARD,
    RADIUS_INPUT,
)
from utils import (
    validate_sale_quantity,
    ValidationError,
    format_currency,
    format_currency_aligned,
)
from widgets import RoundedButton, RoundedCard, RoundedCombobox, RoundedEntry


class SalesPage(tk.Frame):
    """The Sales page: record form + Live Sale Preview + Last Sale Receipt."""

    def __init__(self, parent: tk.Widget, app):
        self.app = app
        t = app.theme
        super().__init__(parent, bg=t["bg"])

        self._form_containers: list[tk.Frame] = []
        self._form_labels: list[tk.Label] = []
        self._last_sale_info: dict | None = None

        self._build_heading()
        self._build_form()
        self._build_cards_section()

    # ------------------------------------------------------------------
    # BUILD UI
    # ------------------------------------------------------------------

    def _build_heading(self) -> None:
        t = self.app.theme
        self.heading_label = tk.Label(
            self,
            text="Record a Sale",
            font=(FONT_FAMILY_BODY, FONT_SIZE_HEADING, "bold"),
            bg=t["bg"],
            fg=t["heading"],
        )
        self.heading_label.pack(anchor="w", pady=(0, PADDING_MEDIUM))

    def _build_form(self) -> None:
        t = self.app.theme
        self.form_frame = tk.Frame(self, bg=t["bg"])
        self.form_frame.pack(fill="x", pady=(0, PADDING_LARGE))
        self._form_containers.append(self.form_frame)

        # --- Product dropdown ---
        product_column = tk.Frame(self.form_frame, bg=t["bg"])
        product_column.pack(side="left", padx=(0, PADDING_MEDIUM))
        self._form_containers.append(product_column)

        product_label = tk.Label(
            product_column,
            text="Product",
            font=(FONT_FAMILY_BODY, FONT_SIZE_BODY - 1),
            bg=t["bg"],
            fg=t["text_light"],
        )
        product_label.pack(anchor="w")
        self._form_labels.append(product_label)

        self.product_dropdown = RoundedCombobox(
            product_column,
            bg_color=t["input_bg"],
            border_color=t["input_border"],
            focus_color=t["input_focus"],
            parent_bg=t["bg"],
            width=30,
            font=(FONT_FAMILY_BODY, FONT_SIZE_BODY),
            state="readonly",
            radius=RADIUS_INPUT,
        )
        self.product_dropdown.pack(pady=(4, 0))
        self.product_dropdown.bind_select(lambda _e: self._update_live_preview())

        # --- Quantity entry ---
        quantity_column = tk.Frame(self.form_frame, bg=t["bg"])
        quantity_column.pack(side="left", padx=(0, PADDING_MEDIUM))
        self._form_containers.append(quantity_column)

        quantity_label = tk.Label(
            quantity_column,
            text="Quantity Sold",
            font=(FONT_FAMILY_BODY, FONT_SIZE_BODY - 1),
            bg=t["bg"],
            fg=t["text_light"],
        )
        quantity_label.pack(anchor="w")
        self._form_labels.append(quantity_label)

        self.quantity_entry = RoundedEntry(
            quantity_column,
            bg_color=t["input_bg"],
            fg_color=t["text"],
            border_color=t["input_border"],
            focus_color=t["input_focus"],
            parent_bg=t["bg"],
            width=12,
            font=(FONT_FAMILY_BODY, FONT_SIZE_BODY),
            radius=RADIUS_INPUT,
        )
        self.quantity_entry.pack(pady=(4, 0))
        self.quantity_entry.bind_entry("<KeyRelease>", lambda _e: self._update_live_preview())
        self.quantity_entry.bind_entry("<Return>", lambda _e: self._handle_record_sale())

        # --- Record Sale button ---
        self.record_button = RoundedButton(
            self.form_frame,
            text="🛒  Record Sale",
            font=(FONT_FAMILY_BODY, FONT_SIZE_BODY, "bold"),
            bg_color=t["primary"],
            hover_color=t["primary_hover"],
            fg_color=t["button_text"],
            parent_bg=t["bg"],
            padx=22,
            height=38,
            radius=RADIUS_BUTTON,
            command=self._handle_record_sale,
        )
        self.record_button.pack(side="left", padx=(PADDING_MEDIUM, 0), pady=(21, 0))

    def _build_cards_section(self) -> None:
        """Build Live Sale Preview (left) and Last Sale Receipt (right)."""
        t = self.app.theme
        self.cards_row = tk.Frame(self, bg=t["bg"])
        self.cards_row.pack(fill="both", expand=True)
        self.cards_row.columnconfigure(0, weight=1, uniform="sale_card")
        self.cards_row.columnconfigure(1, weight=1, uniform="sale_card")
        self._form_containers.append(self.cards_row)

        # --- Left Card: Live Sale Preview ---
        self.preview_card = RoundedCard(
            self.cards_row,
            bg_color=t["card"],
            parent_bg=t["bg"],
            border_color=t["card_border"],
            border_width=1,
            radius=RADIUS_CARD,
            content_pad=16,
        )
        self.preview_card.grid(row=0, column=0, sticky="nsew", padx=(0, PADDING_SMALL))

        self.preview_title = tk.Label(
            self.preview_card.content,
            text="🧮  Live Sale Preview",
            font=(FONT_FAMILY_BODY, FONT_SIZE_BODY + 2, "bold"),
            bg=t["card"],
            fg=t["heading"],
        )
        self.preview_title.pack(anchor="w", pady=(0, 8))

        self.preview_divider = tk.Frame(self.preview_card.content, bg=t["divider"], height=1)
        self.preview_divider.pack(fill="x", pady=(0, 12))

        self.preview_rows: list[tuple[tk.Frame, tk.Label, tk.Label]] = []
        self.preview_price_val = self._add_detail_row(
            self.preview_card.content, "Unit Price", "—", self.preview_rows
        )
        self.preview_stock_val = self._add_detail_row(
            self.preview_card.content, "Available Stock", "—", self.preview_rows
        )
        self.preview_total_val = self._add_detail_row(
            self.preview_card.content,
            "Total to Collect",
            "—",
            self.preview_rows,
            value_bold=True,
            value_size=FONT_SIZE_BODY + 4,
        )

        self.preview_status_label = tk.Label(
            self.preview_card.content,
            text="Select a product and enter a quantity to preview total.",
            font=(FONT_FAMILY_BODY, FONT_SIZE_BODY - 1),
            bg=t["card"],
            fg=t["text_light"],
            anchor="w",
        )
        self.preview_status_label.pack(anchor="w", pady=(14, 0))

        # --- Right Card: Last Sale Receipt ---
        self.summary_card = RoundedCard(
            self.cards_row,
            bg_color=t["card"],
            parent_bg=t["bg"],
            border_color=t["card_border"],
            border_width=1,
            radius=RADIUS_CARD,
            content_pad=16,
        )
        self.summary_card.grid(row=0, column=1, sticky="nsew", padx=(PADDING_SMALL, 0))

        self.summary_title = tk.Label(
            self.summary_card.content,
            text="🧾  Last Sale Summary",
            font=(FONT_FAMILY_BODY, FONT_SIZE_BODY + 2, "bold"),
            bg=t["card"],
            fg=t["heading"],
        )
        self.summary_title.pack(anchor="w", pady=(0, 8))

        self.summary_divider = tk.Frame(self.summary_card.content, bg=t["divider"], height=1)
        self.summary_divider.pack(fill="x", pady=(0, 12))

        self.summary_rows: list[tuple[tk.Frame, tk.Label, tk.Label]] = []
        self.summary_product_val = self._add_detail_row(
            self.summary_card.content, "Product", "—", self.summary_rows
        )
        self.summary_qty_val = self._add_detail_row(
            self.summary_card.content, "Quantity Sold", "—", self.summary_rows
        )
        self.summary_total_val = self._add_detail_row(
            self.summary_card.content,
            "Total Paid",
            "—",
            self.summary_rows,
            value_bold=True,
            value_size=FONT_SIZE_BODY + 4,
        )
        self.summary_remaining_val = self._add_detail_row(
            self.summary_card.content, "Remaining Stock", "—", self.summary_rows
        )

    def _add_detail_row(
        self,
        parent: tk.Widget,
        key_text: str,
        initial_value: str,
        store: list,
        value_bold: bool = False,
        value_size: int = FONT_SIZE_BODY,
    ) -> tk.Label:
        t = self.app.theme
        row = tk.Frame(parent, bg=t["card"])
        row.pack(fill="x", pady=5)

        key_lbl = tk.Label(
            row,
            text=key_text,
            font=(FONT_FAMILY_BODY, FONT_SIZE_BODY),
            bg=t["card"],
            fg=t["text_light"],
            anchor="w",
        )
        key_lbl.pack(side="left")

        weight = "bold" if value_bold else "normal"
        val_lbl = tk.Label(
            row,
            text=initial_value,
            font=(FONT_FAMILY_BODY, value_size, weight),
            bg=t["card"],
            fg=t["card_number"] if value_bold else t["text"],
            anchor="e",
        )
        val_lbl.pack(side="right")

        store.append((row, key_lbl, val_lbl))
        return val_lbl

    # ------------------------------------------------------------------
    # LIVE PREVIEW
    # ------------------------------------------------------------------

    def _update_live_preview(self) -> None:
        """Recalculate unit price, stock indicator, and live total as user types."""
        t = self.app.theme
        product_name = self.product_dropdown.get()
        product = self.app.inventory_store.products.get(product_name)

        if product is None:
            self.preview_price_val.configure(text="—", fg=t["text"])
            self.preview_stock_val.configure(text="—", fg=t["text"])
            self.preview_total_val.configure(text="—", fg=t["card_number"])
            self.preview_status_label.configure(
                text="Select a product and enter a quantity to preview total.",
                fg=t["text_light"],
            )
            return

        # Stock status colour
        if product.is_out_of_stock():
            stock_color = t["danger"]
            stock_text = "0 units (Out of Stock)"
        elif product.is_low_stock(LOW_STOCK_THRESHOLD):
            stock_color = t["warning"]
            stock_text = f"{product.quantity} units (Low Stock)"
        else:
            stock_color = t["success"]
            stock_text = f"{product.quantity} units"

        self.preview_price_val.configure(text=format_currency(product.price), fg=t["text"])
        self.preview_stock_val.configure(text=stock_text, fg=stock_color)

        qty_raw = self.quantity_entry.get().strip()
        if not qty_raw:
            self.preview_total_val.configure(text="—", fg=t["card_number"])
            if product.is_out_of_stock():
                self.preview_status_label.configure(
                    text="This item is out of stock. Restock it on the Products page.",
                    fg=t["danger"],
                )
            else:
                self.preview_status_label.configure(
                    text="Enter quantity sold to calculate total amount.",
                    fg=t["text_light"],
                )
            return

        try:
            qty = int(qty_raw)
        except ValueError:
            self.preview_total_val.configure(text="—", fg=t["card_number"])
            self.preview_status_label.configure(
                text="Quantity must be a whole number (e.g. 2).", fg=t["danger"]
            )
            return

        if qty <= 0:
            self.preview_total_val.configure(text="—", fg=t["card_number"])
            self.preview_status_label.configure(
                text="Enter a quantity greater than zero.", fg=t["danger"]
            )
            return

        estimated_total = product.price * qty
        self.preview_price_val.configure(text=format_currency(product.price))
        self.preview_total_val.configure(text=format_currency(estimated_total))

        if qty > product.quantity:
            self.preview_total_val.configure(fg=t["danger"])
            self.preview_status_label.configure(
                text=f"⚠ Not enough stock: only {product.quantity} unit(s) available.",
                fg=t["danger"],
            )
        else:
            remaining = product.quantity - qty
            self.preview_total_val.configure(fg=t["card_number"])
            self.preview_status_label.configure(
                text=f"✓ Ready to record ({remaining} unit(s) will remain in stock).",
                fg=t["success"],
            )

    # ------------------------------------------------------------------
    # THEME
    # ------------------------------------------------------------------

    def apply_theme(self, theme: dict[str, str]) -> None:
        """Update all widgets on this page to match the active theme."""
        self.configure(bg=theme["bg"])
        self.heading_label.configure(bg=theme["bg"], fg=theme["heading"])

        for frame in self._form_containers:
            frame.configure(bg=theme["bg"])
        for label in self._form_labels:
            label.configure(bg=theme["bg"], fg=theme["text_light"])

        self.product_dropdown.apply_colors(
            bg_color=theme["input_bg"],
            border_color=theme["input_border"],
            focus_color=theme["input_focus"],
            parent_bg=theme["bg"],
        )
        self.quantity_entry.apply_colors(
            bg_color=theme["input_bg"],
            fg_color=theme["text"],
            border_color=theme["input_border"],
            focus_color=theme["input_focus"],
            parent_bg=theme["bg"],
        )
        self.record_button.apply_colors(
            bg_color=theme["primary"],
            hover_color=theme["primary_hover"],
            fg_color=theme["button_text"],
            parent_bg=theme["bg"],
        )

        for card in (self.preview_card, self.summary_card):
            card.apply_colors(
                bg_color=theme["card"],
                parent_bg=theme["bg"],
                border_color=theme["card_border"],
            )

        self.preview_title.configure(bg=theme["card"], fg=theme["heading"])
        self.preview_divider.configure(bg=theme["divider"])
        self.preview_status_label.configure(bg=theme["card"])

        self.summary_title.configure(bg=theme["card"], fg=theme["heading"])
        self.summary_divider.configure(bg=theme["divider"])

        for row, key_lbl, val_lbl in self.preview_rows + self.summary_rows:
            row.configure(bg=theme["card"])
            key_lbl.configure(bg=theme["card"], fg=theme["text_light"])
            val_lbl.configure(bg=theme["card"], fg=theme["text"])

        self.summary_total_val.configure(fg=theme["card_number"])
        self._update_live_preview()

    # ------------------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------------------

    def _handle_record_sale(self) -> None:
        """
        Validate the chosen product and quantity, then record the sale
        if everything checks out.
        """
        product_name = self.product_dropdown.get()

        if not product_name:
            messagebox.showerror("Could Not Record Sale", "Please choose a product.")
            return

        product = self.app.inventory_store.products.get(product_name)
        if product is None:
            messagebox.showerror("Could Not Record Sale", "That product no longer exists.")
            return

        try:
            quantity = validate_sale_quantity(self.quantity_entry.get(), product.quantity)
        except ValidationError as error:
            messagebox.showerror("Could Not Record Sale", str(error))
            return

        total_amount = product.price * quantity
        updated_product = self.app.inventory_store.reduce_stock(product_name, quantity)
        self.app.sales_store.add_sale(product_name, quantity, total_amount)

        self.summary_product_val.configure(text=product_name)
        self.summary_qty_val.configure(text=f"{quantity} unit(s)")
        self.summary_total_val.configure(text=format_currency(total_amount))
        self.summary_remaining_val.configure(text=f"{updated_product.quantity} unit(s)")

        self.quantity_entry.delete(0, tk.END)
        self.app.refresh_all_pages()

    # ------------------------------------------------------------------
    # REFRESH
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Reload the sorted dropdown list and update the live preview."""
        product_names = self.app.inventory_store.get_product_names()
        self.product_dropdown.set_values(product_names)

        # If the previously selected product was removed, clear the selection.
        if self.product_dropdown.get() not in product_names:
            self.product_dropdown.set("")

        self._update_live_preview()
