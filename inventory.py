"""
inventory.py

This file defines the Inventory page. It shows every product in a
rounded table card with five columns: Name, Price, Quantity, Stock Value,
and Status.

Features:
    - Live search bar to find any product instantly
    - One-click status filter pills (All / In Stock / Low Stock / Out of Stock)
    - Pixel-aligned NGN currency columns (Price & Stock Value)
    - Clickable column headers for ascending/descending sorting
    - Colour-coded stock status: Green (In Stock), Orange (Low Stock), Red (Out of Stock)
"""

import tkinter as tk
from tkinter import ttk

from constants import (
    FONT_FAMILY_BODY,
    FONT_SIZE_BODY,
    FONT_SIZE_HEADING,
    PADDING_SMALL,
    PADDING_MEDIUM,
    LOW_STOCK_THRESHOLD,
    RADIUS_CARD,
    RADIUS_INPUT,
    STATUS_IN_STOCK,
    STATUS_LOW_STOCK,
    STATUS_OUT_OF_STOCK,
)
from utils import format_currency, format_currency_aligned
from widgets import RoundedButton, RoundedCard, RoundedEntry


FILTER_ALL = "all"
FILTER_IN_STOCK = "in_stock"
FILTER_LOW_STOCK = "low_stock"
FILTER_OUT_OF_STOCK = "out_of_stock"


class InventoryPage(tk.Frame):
    """The Inventory page: searchable, filterable, sortable stock table."""

    def __init__(self, parent: tk.Widget, app):
        self.app = app
        t = app.theme
        super().__init__(parent, bg=t["bg"])

        self._active_filter: str = FILTER_ALL
        self._sort_column: str = "name"
        self._sort_reverse: bool = False
        self._filter_buttons: dict[str, RoundedButton] = {}
        self._bg_frames: list[tk.Frame] = []

        self._build_header_bar()
        self._build_footer_bar()
        self._build_table()

    def _build_header_bar(self) -> None:
        t = self.app.theme
        top_row = tk.Frame(self, bg=t["bg"])
        top_row.pack(fill="x", pady=(0, PADDING_SMALL))
        self._bg_frames.append(top_row)

        self.heading_label = tk.Label(
            top_row,
            text="Inventory",
            font=(FONT_FAMILY_BODY, FONT_SIZE_HEADING, "bold"),
            bg=t["bg"],
            fg=t["heading"],
        )
        self.heading_label.pack(side="left")

        # Live search box on the right
        self.search_entry = RoundedEntry(
            top_row,
            bg_color=t["input_bg"],
            fg_color=t["text"],
            border_color=t["input_border"],
            focus_color=t["input_focus"],
            parent_bg=t["bg"],
            width=26,
            font=(FONT_FAMILY_BODY, FONT_SIZE_BODY),
            radius=RADIUS_INPUT,
            placeholder="🔍  Search products...",
            placeholder_color=t["placeholder"],
        )
        self.search_entry.pack(side="right")
        self.search_entry.bind_entry("<KeyRelease>", lambda _e: self.refresh())

        # Filter pills row
        filter_row = tk.Frame(self, bg=t["bg"])
        filter_row.pack(fill="x", pady=(0, PADDING_SMALL + 2))
        self._bg_frames.append(filter_row)

        filters = [
            (FILTER_ALL, "All Items"),
            (FILTER_IN_STOCK, "⬤ In Stock"),
            (FILTER_LOW_STOCK, "⬤ Low Stock"),
            (FILTER_OUT_OF_STOCK, "⬤ Out of Stock"),
        ]
        for key, label in filters:
            is_active = key == self._active_filter
            btn = RoundedButton(
                filter_row,
                text=label,
                font=(FONT_FAMILY_BODY, 10, "bold"),
                bg_color=t["accent"] if is_active else t["secondary_bg"],
                hover_color=t["accent_hover"] if is_active else t["secondary_hover"],
                fg_color=t["button_text"] if is_active else t["secondary_fg"],
                parent_bg=t["bg"],
                padx=14,
                height=30,
                radius=15,
                command=lambda k=key: self._set_filter(k),
            )
            btn.pack(side="left", padx=(0, PADDING_SMALL))
            self._filter_buttons[key] = btn

    def _build_table(self) -> None:
        t = self.app.theme
        self.table_card = RoundedCard(
            self,
            bg_color=t["card"],
            parent_bg=t["bg"],
            border_color=t["card_border"],
            border_width=1,
            radius=RADIUS_CARD,
            content_pad=10,
        )
        self.table_card.pack(fill="both", expand=True)

        columns = ("name", "price", "quantity", "value", "status")
        self.inventory_table = ttk.Treeview(
            self.table_card.content, columns=columns, show="headings", height=9
        )

        self._col_labels = {
            "name": "Product Name",
            "price": "Unit Price",
            "quantity": "Quantity",
            "value": "Stock Value",
            "status": "Status",
        }
        self._col_anchors = {
            "name": "w",
            "price": "e",
            "quantity": "center",
            "value": "e",
            "status": "center",
        }

        for col in columns:
            self.inventory_table.heading(
                col,
                text=self._col_labels[col],
                anchor=self._col_anchors[col],
                command=lambda c=col: self._sort_by(c),
            )

        self.inventory_table.column("name", anchor="w", width=280)
        self.inventory_table.column("price", anchor="e", width=155)
        self.inventory_table.column("quantity", anchor="center", width=95)
        self.inventory_table.column("value", anchor="e", width=175)
        self.inventory_table.column("status", anchor="center", width=145)

        self._configure_table_tags(t)
        self._update_heading_indicators()

        scrollbar = ttk.Scrollbar(
            self.table_card.content, orient="vertical", command=self.inventory_table.yview
        )
        self.inventory_table.configure(yscrollcommand=scrollbar.set)

        self.inventory_table.pack(
            side="left", fill="both", expand=True, padx=(4, PADDING_SMALL), pady=4
        )
        scrollbar.pack(side="right", fill="y", pady=4)

    def _build_footer_bar(self) -> None:
        """Compact summary footer showing visible product count and stock value."""
        t = self.app.theme
        footer = tk.Frame(self, bg=t["bg"])
        footer.pack(side="bottom", fill="x", pady=(PADDING_SMALL, 0))
        self._bg_frames.append(footer)

        self.count_summary_label = tk.Label(
            footer,
            text="Showing 0 products",
            font=(FONT_FAMILY_BODY, FONT_SIZE_BODY - 1),
            bg=t["bg"],
            fg=t["text_light"],
        )
        self.count_summary_label.pack(side="left")

        self.value_summary_label = tk.Label(
            footer,
            text="Visible Stock Value: NGN 0.00",
            font=(FONT_FAMILY_BODY, FONT_SIZE_BODY - 1, "bold"),
            bg=t["bg"],
            fg=t["heading"],
        )
        self.value_summary_label.pack(side="right")

    # ------------------------------------------------------------------
    # FILTERING & SORTING
    # ------------------------------------------------------------------

    def _set_filter(self, filter_key: str) -> None:
        self._active_filter = filter_key
        self._update_filter_pill_colors()
        self.refresh()

    def _update_filter_pill_colors(self) -> None:
        t = self.app.theme
        for key, btn in self._filter_buttons.items():
            if key == self._active_filter:
                btn.apply_colors(
                    bg_color=t["accent"],
                    hover_color=t["accent_hover"],
                    fg_color=t["button_text"],
                    parent_bg=t["bg"],
                )
            else:
                btn.apply_colors(
                    bg_color=t["secondary_bg"],
                    hover_color=t["secondary_hover"],
                    fg_color=t["secondary_fg"],
                    parent_bg=t["bg"],
                )

    def _sort_by(self, column: str) -> None:
        if self._sort_column == column:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_column = column
            self._sort_reverse = False
        self._update_heading_indicators()
        self.refresh()

    def _update_heading_indicators(self) -> None:
        arrow = " ▼" if self._sort_reverse else " ▲"
        for col, base_label in self._col_labels.items():
            text = f"{base_label}{arrow}" if col == self._sort_column else base_label
            self.inventory_table.heading(col, text=text)

    # ------------------------------------------------------------------
    # THEME
    # ------------------------------------------------------------------

    def _configure_table_tags(self, theme: dict[str, str]) -> None:
        """Apply theme-aware zebra row backgrounds and stock-status text colours."""
        self.inventory_table.tag_configure("even", background=theme["table_row_bg"])
        self.inventory_table.tag_configure("odd", background=theme["table_row_alt_bg"])
        self.inventory_table.tag_configure("in_stock", foreground=theme["success"])
        self.inventory_table.tag_configure("low_stock", foreground=theme["warning"])
        self.inventory_table.tag_configure("out_of_stock", foreground=theme["danger"])

    def apply_theme(self, theme: dict[str, str]) -> None:
        """Update all widgets on this page to match the active theme."""
        self.configure(bg=theme["bg"])
        self.heading_label.configure(bg=theme["bg"], fg=theme["heading"])

        for frame in self._bg_frames:
            frame.configure(bg=theme["bg"])

        self.search_entry.apply_colors(
            bg_color=theme["input_bg"],
            fg_color=theme["text"],
            border_color=theme["input_border"],
            focus_color=theme["input_focus"],
            parent_bg=theme["bg"],
            placeholder_color=theme["placeholder"],
        )
        self._update_filter_pill_colors()

        self.table_card.apply_colors(
            bg_color=theme["card"],
            parent_bg=theme["bg"],
            border_color=theme["card_border"],
        )
        self._configure_table_tags(theme)
        self.count_summary_label.configure(bg=theme["bg"], fg=theme["text_light"])
        self.value_summary_label.configure(bg=theme["bg"], fg=theme["heading"])

    # ------------------------------------------------------------------
    # REFRESH
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Reload the table applying search, filter, sort, and aligned NGN values."""
        self.inventory_table.delete(*self.inventory_table.get_children())

        all_products = self.app.inventory_store.get_all_products()
        query = self.search_entry.get().strip().lower()

        filtered = []
        for product in all_products:
            _, status_tag = self._determine_status(product)
            if self._active_filter != FILTER_ALL and status_tag != self._active_filter:
                continue
            if query and query not in product.name.lower():
                continue
            filtered.append(product)

        status_rank = {
            "out_of_stock": 0,
            "low_stock": 1,
            "in_stock": 2,
        }

        if self._sort_column == "price":
            filtered.sort(key=lambda p: (p.price, p.name.lower()), reverse=self._sort_reverse)
        elif self._sort_column == "quantity":
            filtered.sort(
                key=lambda p: (p.quantity, p.name.lower()), reverse=self._sort_reverse
            )
        elif self._sort_column == "value":
            filtered.sort(
                key=lambda p: (p.total_value(), p.name.lower()),
                reverse=self._sort_reverse,
            )
        elif self._sort_column == "status":
            filtered.sort(
                key=lambda p: (
                    status_rank[self._determine_status(p)[1]],
                    p.quantity,
                    p.name.lower(),
                ),
                reverse=self._sort_reverse,
            )
        else:
            filtered.sort(key=lambda p: p.name.lower(), reverse=self._sort_reverse)

        max_price = max((p.price for p in filtered), default=0.0)
        max_value = max((p.total_value() for p in filtered), default=0.0)

        for index, product in enumerate(filtered):
            status_text, status_tag = self._determine_status(product)
            stripe_tag = "even" if index % 2 == 0 else "odd"

            self.inventory_table.insert(
                "",
                tk.END,
                values=(
                    product.name,
                    format_currency_aligned(product.price, max_price),
                    product.quantity,
                    format_currency_aligned(product.total_value(), max_value),
                    status_text,
                ),
                tags=(stripe_tag, status_tag),
            )

        visible_value = sum(p.total_value() for p in filtered)
        self.count_summary_label.configure(
            text=f"Showing {len(filtered)} of {len(all_products)} products"
        )
        self.value_summary_label.configure(
            text=f"Visible Stock Value: {format_currency(visible_value)}"
        )

    def _determine_status(self, product) -> tuple[str, str]:
        """
        Decide a product's status label and matching colour tag.

        Returns:
            A tuple of (status_text, tag_name).
        """
        if product.is_out_of_stock():
            return f"⬤ {STATUS_OUT_OF_STOCK}", "out_of_stock"
        elif product.is_low_stock(LOW_STOCK_THRESHOLD):
            return f"⬤ {STATUS_LOW_STOCK}", "low_stock"
        else:
            return f"⬤ {STATUS_IN_STOCK}", "in_stock"
