"""
dashboard.py

This file defines the Dashboard page: the first thing the user sees.
It shows:
    - Four equal-width rounded KPI cards (Products, Items in Stock,
      Today's Sales, Low Stock Items).
    - A two-column actionable overview below:
        * Left:  Stock Alerts (Out of Stock & Low Stock products)
        * Right: Recent Sales & Total Inventory Value
"""

import tkinter as tk

from constants import (
    FONT_FAMILY_BODY,
    FONT_SIZE_BODY,
    FONT_SIZE_CARD_NUMBER,
    FONT_SIZE_CARD_LABEL,
    FONT_SIZE_HEADING,
    PADDING_SMALL,
    PADDING_MEDIUM,
    PADDING_LARGE,
    LOW_STOCK_THRESHOLD,
    PAGE_PRODUCTS,
    RADIUS_BUTTON,
    RADIUS_CARD,
)
from utils import format_currency, format_currency_aligned
from widgets import RoundedButton, RoundedCard


class DashboardPage(tk.Frame):
    """The Dashboard page: KPI summary cards plus Stock Alerts and Recent Sales."""

    def __init__(self, parent: tk.Widget, app):
        self.app = app
        t = app.theme
        super().__init__(parent, bg=t["bg"])

        self._cards: list[RoundedCard] = []
        self._number_labels: list[tk.Label] = []
        self._caption_labels: list[tk.Label] = []

        self._build_heading()
        self._build_kpi_cards()
        self._build_lower_panels()

    def _build_heading(self) -> None:
        t = self.app.theme
        self.heading_label = tk.Label(
            self,
            text="Overview",
            font=(FONT_FAMILY_BODY, FONT_SIZE_HEADING, "bold"),
            bg=t["bg"],
            fg=t["heading"],
        )
        self.heading_label.pack(anchor="w", pady=(0, PADDING_SMALL))

    def _build_kpi_cards(self) -> None:
        """Create the row of four equal-width rounded KPI cards."""
        t = self.app.theme
        self.cards_frame = tk.Frame(self, bg=t["bg"])
        self.cards_frame.pack(fill="x", pady=(0, PADDING_MEDIUM))

        card_specs = [
            ("Products", "products_number_label"),
            ("Items in Stock", "stock_number_label"),
            ("Today's Sales", "sales_number_label"),
            ("Low / Out of Stock", "low_stock_number_label"),
        ]

        for col, (label_text, attr_name) in enumerate(card_specs):
            self.cards_frame.columnconfigure(col, weight=1, uniform="kpi_card")
            number_label = self._create_kpi_card(self.cards_frame, label_text, col)
            setattr(self, attr_name, number_label)

    def _create_kpi_card(
        self, parent: tk.Widget, label_text: str, column: int
    ) -> tk.Label:
        t = self.app.theme
        card = RoundedCard(
            parent,
            bg_color=t["card"],
            parent_bg=t["bg"],
            border_color=t["card_border"],
            border_width=1,
            radius=RADIUS_CARD,
            content_pad=10,
        )
        padx = (0, PADDING_SMALL) if column == 0 else (
            (PADDING_SMALL, 0) if column == 3 else PADDING_SMALL
        )
        card.grid(row=0, column=column, sticky="nsew", padx=padx, pady=4)
        self._cards.append(card)

        number_label = tk.Label(
            card.content,
            text="0",
            font=(FONT_FAMILY_BODY, FONT_SIZE_CARD_NUMBER, "bold"),
            bg=t["card"],
            fg=t["card_number"],
        )
        number_label.pack(pady=(PADDING_MEDIUM, 4))
        self._number_labels.append(number_label)

        caption_label = tk.Label(
            card.content,
            text=label_text,
            font=(FONT_FAMILY_BODY, FONT_SIZE_CARD_LABEL),
            bg=t["card"],
            fg=t["text_light"],
        )
        caption_label.pack(pady=(0, PADDING_MEDIUM))
        self._caption_labels.append(caption_label)

        return number_label

    def _build_lower_panels(self) -> None:
        """Build the Stock Alerts (left) and Recent Sales (right) overview cards."""
        t = self.app.theme
        self.lower_frame = tk.Frame(self, bg=t["bg"])
        self.lower_frame.pack(fill="both", expand=True)
        self.lower_frame.columnconfigure(0, weight=1, uniform="lower_panel")
        self.lower_frame.columnconfigure(1, weight=1, uniform="lower_panel")
        self.lower_frame.rowconfigure(0, weight=1)

        # --- Left Card: Stock Alerts ---
        self.alerts_card = RoundedCard(
            self.lower_frame,
            bg_color=t["card"],
            parent_bg=t["bg"],
            border_color=t["card_border"],
            border_width=1,
            radius=RADIUS_CARD,
            content_pad=14,
        )
        self.alerts_card.grid(row=0, column=0, sticky="nsew", padx=(0, PADDING_SMALL))
        self._cards.append(self.alerts_card)

        self.alerts_header = tk.Frame(self.alerts_card.content, bg=t["card"])
        self.alerts_header.pack(fill="x", pady=(0, 8))

        self.alerts_title = tk.Label(
            self.alerts_header,
            text="⚠  Stock Alerts",
            font=(FONT_FAMILY_BODY, FONT_SIZE_BODY + 2, "bold"),
            bg=t["card"],
            fg=t["heading"],
        )
        self.alerts_title.pack(side="left")

        self.restock_jump_btn = RoundedButton(
            self.alerts_header,
            text="Restock →",
            font=(FONT_FAMILY_BODY, 10, "bold"),
            bg_color=t["secondary_bg"],
            hover_color=t["secondary_hover"],
            fg_color=t["secondary_fg"],
            parent_bg=t["card"],
            padx=12,
            height=28,
            radius=14,
            command=lambda: self.app.show_page(PAGE_PRODUCTS),
        )
        self.restock_jump_btn.pack(side="right")

        self.alerts_divider = tk.Frame(self.alerts_card.content, bg=t["divider"], height=1)
        self.alerts_divider.pack(fill="x", pady=(0, 8))

        self.alerts_list_frame = tk.Frame(self.alerts_card.content, bg=t["card"])
        self.alerts_list_frame.pack(fill="both", expand=True)

        # --- Right Card: Recent Sales & Total Stock Value ---
        self.recent_card = RoundedCard(
            self.lower_frame,
            bg_color=t["card"],
            parent_bg=t["bg"],
            border_color=t["card_border"],
            border_width=1,
            radius=RADIUS_CARD,
            content_pad=14,
        )
        self.recent_card.grid(row=0, column=1, sticky="nsew", padx=(PADDING_SMALL, 0))
        self._cards.append(self.recent_card)

        self.recent_header = tk.Frame(self.recent_card.content, bg=t["card"])
        self.recent_header.pack(fill="x", pady=(0, 8))

        self.recent_title = tk.Label(
            self.recent_header,
            text="🧾  Recent Sales",
            font=(FONT_FAMILY_BODY, FONT_SIZE_BODY + 2, "bold"),
            bg=t["card"],
            fg=t["heading"],
        )
        self.recent_title.pack(side="left")

        self.stock_value_label = tk.Label(
            self.recent_header,
            text="Stock Value: NGN 0.00",
            font=(FONT_FAMILY_BODY, 10, "bold"),
            bg=t["card"],
            fg=t["text_light"],
        )
        self.stock_value_label.pack(side="right")

        self.recent_divider = tk.Frame(self.recent_card.content, bg=t["divider"], height=1)
        self.recent_divider.pack(fill="x", pady=(0, 8))

        self.recent_list_frame = tk.Frame(self.recent_card.content, bg=t["card"])
        self.recent_list_frame.pack(fill="both", expand=True)

    def _render_alerts_list(self) -> None:
        t = self.app.theme
        for child in self.alerts_list_frame.winfo_children():
            child.destroy()

        alerts = self.app.inventory_store.get_alert_products(LOW_STOCK_THRESHOLD)
        if not alerts:
            ok_label = tk.Label(
                self.alerts_list_frame,
                text="✓  All products are comfortably stocked.",
                font=(FONT_FAMILY_BODY, FONT_SIZE_BODY),
                bg=t["card"],
                fg=t["success"],
            )
            ok_label.pack(anchor="w", pady=12)
            return

        for product in alerts[:5]:
            row = tk.Frame(self.alerts_list_frame, bg=t["card"])
            row.pack(fill="x", pady=4)

            is_out = product.is_out_of_stock()
            badge_color = t["danger"] if is_out else t["warning"]
            status_text = "Out of Stock (0)" if is_out else f"Low Stock ({product.quantity} left)"

            name_lbl = tk.Label(
                row,
                text=product.name,
                font=(FONT_FAMILY_BODY, FONT_SIZE_BODY),
                bg=t["card"],
                fg=t["text"],
                anchor="w",
            )
            name_lbl.pack(side="left", fill="x", expand=True)

            status_lbl = tk.Label(
                row,
                text=f"⬤ {status_text}",
                font=(FONT_FAMILY_BODY, FONT_SIZE_BODY - 1, "bold"),
                bg=t["card"],
                fg=badge_color,
                anchor="e",
            )
            status_lbl.pack(side="right")

        if len(alerts) > 5:
            more_lbl = tk.Label(
                self.alerts_list_frame,
                text=f"+ {len(alerts) - 5} more items need restocking...",
                font=(FONT_FAMILY_BODY, FONT_SIZE_BODY - 1),
                bg=t["card"],
                fg=t["text_light"],
            )
            more_lbl.pack(anchor="w", pady=(6, 0))

    def _render_recent_sales_list(self) -> None:
        t = self.app.theme
        for child in self.recent_list_frame.winfo_children():
            child.destroy()

        recent_sales = self.app.sales_store.get_all_sales()[:5]
        if not recent_sales:
            empty_lbl = tk.Label(
                self.recent_list_frame,
                text="No sales recorded yet.",
                font=(FONT_FAMILY_BODY, FONT_SIZE_BODY),
                bg=t["card"],
                fg=t["text_light"],
            )
            empty_lbl.pack(anchor="w", pady=12)
            return

        max_amt = max(sale.amount for sale in recent_sales)

        for sale in recent_sales:
            row = tk.Frame(self.recent_list_frame, bg=t["card"])
            row.pack(fill="x", pady=4)

            desc_lbl = tk.Label(
                row,
                text=f"{sale.product_name}  ×{sale.quantity}",
                font=(FONT_FAMILY_BODY, FONT_SIZE_BODY),
                bg=t["card"],
                fg=t["text"],
                anchor="w",
            )
            desc_lbl.pack(side="left", fill="x", expand=True)

            amt_lbl = tk.Label(
                row,
                text=format_currency_aligned(sale.amount, max_amt),
                font=(FONT_FAMILY_BODY, FONT_SIZE_BODY, "bold"),
                bg=t["card"],
                fg=t["card_number"],
                anchor="e",
            )
            amt_lbl.pack(side="right")

    def apply_theme(self, theme: dict[str, str]) -> None:
        """Update all widgets on this page to match the active theme."""
        self.configure(bg=theme["bg"])
        self.heading_label.configure(bg=theme["bg"], fg=theme["heading"])
        self.cards_frame.configure(bg=theme["bg"])
        self.lower_frame.configure(bg=theme["bg"])

        for card in self._cards:
            card.apply_colors(
                bg_color=theme["card"],
                parent_bg=theme["bg"],
                border_color=theme["card_border"],
            )
        for label in self._number_labels:
            label.configure(bg=theme["card"], fg=theme["card_number"])
        for label in self._caption_labels:
            label.configure(bg=theme["card"], fg=theme["text_light"])

        self.alerts_header.configure(bg=theme["card"])
        self.alerts_title.configure(bg=theme["card"], fg=theme["heading"])
        self.alerts_divider.configure(bg=theme["divider"])
        self.alerts_list_frame.configure(bg=theme["card"])
        self.restock_jump_btn.apply_colors(
            bg_color=theme["secondary_bg"],
            hover_color=theme["secondary_hover"],
            fg_color=theme["secondary_fg"],
            parent_bg=theme["card"],
        )

        self.recent_header.configure(bg=theme["card"])
        self.recent_title.configure(bg=theme["card"], fg=theme["heading"])
        self.stock_value_label.configure(bg=theme["card"], fg=theme["text_light"])
        self.recent_divider.configure(bg=theme["divider"])
        self.recent_list_frame.configure(bg=theme["card"])

        self._render_alerts_list()
        self._render_recent_sales_list()

    def refresh(self) -> None:
        """
        Recalculate and redisplay all four KPI cards, Stock Alerts,
        Total Inventory Value, and Recent Sales.
        """
        inventory_store = self.app.inventory_store
        sales_store = self.app.sales_store

        product_count = len(inventory_store.get_all_products())
        total_units = inventory_store.total_units_in_stock()
        today_total = sales_store.get_today_total()
        alert_count = len(inventory_store.get_alert_products(LOW_STOCK_THRESHOLD))
        total_value = inventory_store.total_inventory_value()

        sales_text = format_currency(today_total)
        sales_font_size = FONT_SIZE_CARD_NUMBER
        if len(sales_text) > 15:
            sales_font_size = 15
        elif len(sales_text) > 12:
            sales_font_size = 18

        self.products_number_label.configure(text=str(product_count))
        self.stock_number_label.configure(text=str(total_units))
        self.sales_number_label.configure(
            text=sales_text,
            font=(FONT_FAMILY_BODY, sales_font_size, "bold"),
        )
        self.low_stock_number_label.configure(text=str(alert_count))
        self.stock_value_label.configure(
            text=f"Stock Value: {format_currency(total_value)}"
        )

        self._render_alerts_list()
        self._render_recent_sales_list()
