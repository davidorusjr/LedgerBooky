"""
history.py

This file defines the Sales History page. It shows a log of every
sale ever recorded, sorted newest-first by default, along with:

    - Summary banner (Best Selling Product, Total Sales, Total Revenue)
    - Live search by product name or date (e.g. "2026-11-25")
    - Pixel-aligned NGN Amount column + clickable column sorting
    - Void Sale button (deletes a mistaken sale and optionally restores stock)
    - Offline Export CSV button for local backups & spreadsheets
"""

from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from constants import (
    FONT_FAMILY_BODY,
    FONT_SIZE_HEADING,
    FONT_SIZE_BODY,
    PADDING_SMALL,
    PADDING_MEDIUM,
    RADIUS_BUTTON,
    RADIUS_CARD,
    RADIUS_INPUT,
)
from models import Sale
from utils import format_currency, format_currency_aligned
from widgets import RoundedButton, RoundedCard, RoundedEntry


class HistoryPage(tk.Frame):
    """The Sales History page: searchable log, totals banner, void & CSV export."""

    def __init__(self, parent: tk.Widget, app):
        self.app = app
        t = app.theme
        super().__init__(parent, bg=t["bg"])

        self._bg_frames: list[tk.Frame] = []
        self._row_to_sale: dict[str, Sale] = {}
        self._sort_column: str = "date"
        self._sort_reverse: bool = True

        self._build_header_bar()
        self._build_summary_card()
        self._build_table()

    def _build_header_bar(self) -> None:
        t = self.app.theme
        top_row = tk.Frame(self, bg=t["bg"])
        top_row.pack(fill="x", pady=(0, PADDING_SMALL + 2))
        self._bg_frames.append(top_row)

        self.heading_label = tk.Label(
            top_row,
            text="Sales History",
            font=(FONT_FAMILY_BODY, FONT_SIZE_HEADING, "bold"),
            bg=t["bg"],
            fg=t["heading"],
        )
        self.heading_label.pack(side="left")

        # Right-side controls: Void Sale, Export CSV, and Search
        self.void_button = RoundedButton(
            top_row,
            text="↩  Void Sale",
            font=(FONT_FAMILY_BODY, 10, "bold"),
            bg_color=t["danger_bg"],
            hover_color=t["danger_hover"],
            fg_color=t["button_text"],
            parent_bg=t["bg"],
            padx=14,
            height=36,
            radius=RADIUS_BUTTON,
            command=self._handle_void_sale,
        )
        self.void_button.pack(side="right")

        self.export_button = RoundedButton(
            top_row,
            text="💾  Export CSV",
            font=(FONT_FAMILY_BODY, 10, "bold"),
            bg_color=t["secondary_bg"],
            hover_color=t["secondary_hover"],
            fg_color=t["secondary_fg"],
            parent_bg=t["bg"],
            padx=14,
            height=36,
            radius=RADIUS_BUTTON,
            command=self._handle_export_csv,
        )
        self.export_button.pack(side="right", padx=(0, PADDING_SMALL))

        self.search_entry = RoundedEntry(
            top_row,
            bg_color=t["input_bg"],
            fg_color=t["text"],
            border_color=t["input_border"],
            focus_color=t["input_focus"],
            parent_bg=t["bg"],
            width=24,
            font=(FONT_FAMILY_BODY, FONT_SIZE_BODY),
            radius=RADIUS_INPUT,
            placeholder="🔍  Search product or date...",
            placeholder_color=t["placeholder"],
        )
        self.search_entry.pack(side="right", padx=(0, PADDING_SMALL))
        self.search_entry.bind_entry("<KeyRelease>", lambda _e: self.refresh())

    def _build_summary_card(self) -> None:
        t = self.app.theme
        self.summary_card = RoundedCard(
            self,
            bg_color=t["card"],
            parent_bg=t["bg"],
            border_color=t["card_border"],
            border_width=1,
            radius=RADIUS_CARD,
            content_pad=10,
        )
        self.summary_card.pack(fill="x", pady=(0, PADDING_MEDIUM))

        self.best_seller_label = tk.Label(
            self.summary_card.content,
            text="🏆  Best Seller: —",
            font=(FONT_FAMILY_BODY, FONT_SIZE_BODY, "bold"),
            bg=t["card"],
            fg=t["text"],
        )
        self.best_seller_label.pack(side="left", padx=PADDING_SMALL, pady=4)

        self.revenue_label = tk.Label(
            self.summary_card.content,
            text="Total Revenue: NGN 0.00",
            font=(FONT_FAMILY_BODY, FONT_SIZE_BODY, "bold"),
            bg=t["card"],
            fg=t["card_number"],
        )
        self.revenue_label.pack(side="right", padx=PADDING_SMALL, pady=4)

        self.sales_count_label = tk.Label(
            self.summary_card.content,
            text="0 sales",
            font=(FONT_FAMILY_BODY, FONT_SIZE_BODY),
            bg=t["card"],
            fg=t["text_light"],
        )
        self.sales_count_label.pack(side="right", padx=(0, PADDING_MEDIUM), pady=4)

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

        columns = ("date", "time", "product", "quantity", "amount")
        self.history_table = ttk.Treeview(
            self.table_card.content,
            columns=columns,
            show="headings",
            height=9,
            selectmode="browse",
        )

        self._col_labels = {
            "date": "Date",
            "time": "Time",
            "product": "Product",
            "quantity": "Quantity",
            "amount": "Amount",
        }
        self._col_anchors = {
            "date": "center",
            "time": "center",
            "product": "w",
            "quantity": "center",
            "amount": "e",
        }

        for col in columns:
            self.history_table.heading(
                col,
                text=self._col_labels[col],
                anchor=self._col_anchors[col],
                command=lambda c=col: self._sort_by(c),
            )

        self.history_table.column("date", anchor="center", width=115)
        self.history_table.column("time", anchor="center", width=95)
        self.history_table.column("product", anchor="w", width=310)
        self.history_table.column("quantity", anchor="center", width=95)
        self.history_table.column("amount", anchor="e", width=180)

        self._configure_table_tags(t)
        self._update_heading_indicators()

        scrollbar = ttk.Scrollbar(
            self.table_card.content, orient="vertical", command=self.history_table.yview
        )
        self.history_table.configure(yscrollcommand=scrollbar.set)

        self.history_table.pack(
            side="left", fill="both", expand=True, padx=(4, PADDING_SMALL), pady=4
        )
        scrollbar.pack(side="right", fill="y", pady=4)

    # ------------------------------------------------------------------
    # SORTING
    # ------------------------------------------------------------------

    def _sort_by(self, column: str) -> None:
        if self._sort_column == column:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_column = column
            self._sort_reverse = column in ("date", "time", "amount")
        self._update_heading_indicators()
        self.refresh()

    def _update_heading_indicators(self) -> None:
        arrow = " ▼" if self._sort_reverse else " ▲"
        for col, base_label in self._col_labels.items():
            text = f"{base_label}{arrow}" if col == self._sort_column else base_label
            self.history_table.heading(col, text=text)

    # ------------------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------------------

    def _handle_void_sale(self) -> None:
        """Delete a mistaken sale entry and optionally restore its units to stock."""
        selection = self.history_table.selection()
        if not selection:
            messagebox.showinfo(
                "Select a Sale", "Please select a sale row from the table to void."
            )
            return

        sale = self._row_to_sale.get(selection[0])
        if sale is None:
            return

        product_exists = sale.product_name in self.app.inventory_store.products
        stock_note = (
            f"\n\n{sale.quantity} unit(s) will also be returned to inventory stock."
            if product_exists
            else "\n\n(Note: this product is no longer in inventory, so stock will not change.)"
        )

        confirmed = messagebox.askyesno(
            "Confirm Void Sale",
            f"Void this sale record?\n\n"
            f"Product: {sale.product_name}\n"
            f"Quantity: {sale.quantity}\n"
            f"Amount: {format_currency(sale.amount)}\n"
            f"Date: {sale.date} {sale.time}"
            f"{stock_note}",
        )
        if not confirmed:
            return

        self.app.sales_store.delete_sale(sale)
        if product_exists:
            self.app.inventory_store.restock_product(sale.product_name, sale.quantity)

        self.app.refresh_all_pages()
        messagebox.showinfo("Sale Voided", "The sale record has been removed.")

    def _handle_export_csv(self) -> None:
        """Save an offline backup copy of the sales log as a CSV spreadsheet."""
        if not self.app.sales_store.sales:
            messagebox.showinfo("Nothing to Export", "There are no sales recorded yet.")
            return

        default_name = f"ledgerbooky_sales_{datetime.now().strftime('%Y-%m-%d')}.csv"
        export_path = filedialog.asksaveasfilename(
            title="Export Sales Report (CSV)",
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=[("CSV Spreadsheet", "*.csv"), ("All Files", "*.*")],
        )
        if not export_path:
            return

        try:
            self.app.sales_store.export_to_csv(export_path)
        except OSError as error:
            messagebox.showerror("Export Failed", f"Could not save file:\n{error}")
            return

        messagebox.showinfo(
            "Export Complete", f"Sales report exported successfully to:\n{export_path}"
        )

    # ------------------------------------------------------------------
    # THEME
    # ------------------------------------------------------------------

    def _configure_table_tags(self, theme: dict[str, str]) -> None:
        self.history_table.tag_configure("even", background=theme["table_row_bg"])
        self.history_table.tag_configure("odd", background=theme["table_row_alt_bg"])

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
        self.export_button.apply_colors(
            bg_color=theme["secondary_bg"],
            hover_color=theme["secondary_hover"],
            fg_color=theme["secondary_fg"],
            parent_bg=theme["bg"],
        )
        self.void_button.apply_colors(
            bg_color=theme["danger_bg"],
            hover_color=theme["danger_hover"],
            fg_color=theme["button_text"],
            parent_bg=theme["bg"],
        )

        self.summary_card.apply_colors(
            bg_color=theme["card"],
            parent_bg=theme["bg"],
            border_color=theme["card_border"],
        )
        self.best_seller_label.configure(bg=theme["card"], fg=theme["text"])
        self.sales_count_label.configure(bg=theme["card"], fg=theme["text_light"])
        self.revenue_label.configure(bg=theme["card"], fg=theme["card_number"])

        self.table_card.apply_colors(
            bg_color=theme["card"],
            parent_bg=theme["bg"],
            border_color=theme["card_border"],
        )
        self._configure_table_tags(theme)

    # ------------------------------------------------------------------
    # REFRESH
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Reload the history table with aligned NGN amounts and summary stats."""
        self.history_table.delete(*self.history_table.get_children())
        self._row_to_sale.clear()

        sales = self.app.sales_store.get_all_sales()
        query = self.search_entry.get().strip().lower()
        if query:
            sales = [
                sale
                for sale in sales
                if query in sale.product_name.lower() or query in sale.date.lower()
            ]

        if self._sort_column == "time":
            sales.sort(key=lambda s: (s.time, s.date), reverse=self._sort_reverse)
        elif self._sort_column == "product":
            sales.sort(
                key=lambda s: (s.product_name.lower(), s.date, s.time),
                reverse=self._sort_reverse,
            )
        elif self._sort_column == "quantity":
            sales.sort(
                key=lambda s: (s.quantity, s.date, s.time), reverse=self._sort_reverse
            )
        elif self._sort_column == "amount":
            sales.sort(
                key=lambda s: (s.amount, s.date, s.time), reverse=self._sort_reverse
            )
        else:
            sales.sort(key=lambda s: (s.date, s.time), reverse=self._sort_reverse)

        max_amount = max((s.amount for s in sales), default=0.0)

        for index, sale in enumerate(sales):
            stripe_tag = "even" if index % 2 == 0 else "odd"
            row_id = self.history_table.insert(
                "",
                tk.END,
                values=(
                    sale.date,
                    sale.time,
                    sale.product_name,
                    sale.quantity,
                    format_currency_aligned(sale.amount, max_amount),
                ),
                tags=(stripe_tag,),
            )
            self._row_to_sale[row_id] = sale

        best_seller = self.app.sales_store.get_best_selling_product()
        if best_seller is None:
            self.best_seller_label.configure(text="🏆  Best Seller: —")
        else:
            self.best_seller_label.configure(text=f"🏆  Best Seller: {best_seller}")

        visible_revenue = sum(s.amount for s in sales)
        count_word = "sale" if len(sales) == 1 else "sales"
        self.sales_count_label.configure(text=f"{len(sales)} {count_word}")
        self.revenue_label.configure(
            text=f"Total Revenue: {format_currency(visible_revenue)}"
        )
