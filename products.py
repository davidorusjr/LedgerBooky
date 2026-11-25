"""
products.py

This file defines the Products page. It lets the user:

    - Add a new product (name, price, quantity).
    - Edit an existing product (select a row and click Edit, or double-click).
    - Delete a mistaken product (select a row and click Delete, with confirmation).
    - Restock any existing product using the bottom restock bar.
    - Sort the table by clicking any column header.

All validation (blank names, duplicates, negative numbers, letters in
number fields) is handled by utils.py, so this file only worries about
the user interface and reacting to validation results.
"""

import tkinter as tk
from tkinter import ttk, messagebox

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
from utils import (
    validate_product_name,
    validate_price,
    validate_quantity,
    ValidationError,
    format_currency_aligned,
)
from widgets import RoundedButton, RoundedCard, RoundedCombobox, RoundedEntry


class ProductsPage(tk.Frame):
    """The Products page: add, edit, delete, and restock products."""

    def __init__(self, parent: tk.Widget, app):
        self.app = app
        t = app.theme
        super().__init__(parent, bg=t["bg"])

        self._bg_frames: list[tk.Frame] = []
        self._field_labels: list[tk.Label] = []
        self._entries: list[RoundedEntry] = []

        # Edit-mode state: None means "Add new product"; a product name means editing it.
        self._editing_product_name: str | None = None

        # Table sorting state
        self._sort_column: str = "name"
        self._sort_reverse: bool = False

        self._build_heading()
        self._build_form()
        self._build_bottom_bar()
        self._build_table()

    # ------------------------------------------------------------------
    # BUILD UI
    # ------------------------------------------------------------------

    def _build_heading(self) -> None:
        t = self.app.theme
        header_row = tk.Frame(self, bg=t["bg"])
        header_row.pack(fill="x", pady=(0, PADDING_SMALL))
        self._bg_frames.append(header_row)

        self.heading_label = tk.Label(
            header_row,
            text="Add a Product",
            font=(FONT_FAMILY_BODY, FONT_SIZE_HEADING, "bold"),
            bg=t["bg"],
            fg=t["heading"],
        )
        self.heading_label.pack(side="left")

        self.hint_label = tk.Label(
            header_row,
            text="Tip: Select a row to Edit or Delete (double-click to edit)",
            font=(FONT_FAMILY_BODY, FONT_SIZE_BODY - 1),
            bg=t["bg"],
            fg=t["text_light"],
        )
        self.hint_label.pack(side="right", pady=(6, 0))
        self._field_labels.append(self.hint_label)

    def _build_form(self) -> None:
        """Build the row of rounded input fields and the Add/Save button."""
        t = self.app.theme
        form_frame = tk.Frame(self, bg=t["bg"])
        form_frame.pack(fill="x", pady=(0, PADDING_MEDIUM))
        self._bg_frames.append(form_frame)

        self.name_entry = self._create_labeled_entry(form_frame, "Product Name", width=26)
        self.price_entry = self._create_labeled_entry(form_frame, "Price (NGN)", width=13)
        self.quantity_entry = self._create_labeled_entry(form_frame, "Quantity", width=10)

        for entry in (self.name_entry, self.price_entry, self.quantity_entry):
            entry.bind_entry("<Return>", lambda _e: self._handle_submit_product())

        self.submit_button = RoundedButton(
            form_frame,
            text="＋  Add Product",
            font=(FONT_FAMILY_BODY, FONT_SIZE_BODY, "bold"),
            bg_color=t["primary"],
            hover_color=t["primary_hover"],
            fg_color=t["button_text"],
            parent_bg=t["bg"],
            padx=20,
            height=38,
            radius=RADIUS_BUTTON,
            command=self._handle_submit_product,
        )
        self.submit_button.pack(side="left", padx=(PADDING_MEDIUM, 0), pady=(21, 0))

        self.cancel_edit_button = RoundedButton(
            form_frame,
            text="Cancel",
            font=(FONT_FAMILY_BODY, FONT_SIZE_BODY, "bold"),
            bg_color=t["secondary_bg"],
            hover_color=t["secondary_hover"],
            fg_color=t["secondary_fg"],
            parent_bg=t["bg"],
            padx=16,
            height=38,
            radius=RADIUS_BUTTON,
            command=self._exit_edit_mode,
        )
        # Shown only when editing an existing product.

    def _create_labeled_entry(
        self, parent: tk.Widget, label_text: str, width: int
    ) -> RoundedEntry:
        """Create a small 'label above rounded entry box' group and return the entry."""
        t = self.app.theme
        column_frame = tk.Frame(parent, bg=t["bg"])
        column_frame.pack(side="left", padx=(0, PADDING_MEDIUM))
        self._bg_frames.append(column_frame)

        label = tk.Label(
            column_frame,
            text=label_text,
            font=(FONT_FAMILY_BODY, FONT_SIZE_BODY - 1),
            bg=t["bg"],
            fg=t["text_light"],
        )
        label.pack(anchor="w")
        self._field_labels.append(label)

        entry = RoundedEntry(
            column_frame,
            bg_color=t["input_bg"],
            fg_color=t["text"],
            border_color=t["input_border"],
            focus_color=t["input_focus"],
            parent_bg=t["bg"],
            width=width,
            font=(FONT_FAMILY_BODY, FONT_SIZE_BODY),
            radius=RADIUS_INPUT,
        )
        entry.pack(pady=(4, 0))
        self._entries.append(entry)

        return entry

    def _build_table(self) -> None:
        """Build the rounded scrollable table card that lists every product."""
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

        columns = ("name", "price", "quantity")
        self.product_table = ttk.Treeview(
            self.table_card.content,
            columns=columns,
            show="headings",
            height=5,
            selectmode="browse",
        )

        self._col_labels = {
            "name": "Product Name",
            "price": "Price",
            "quantity": "Quantity",
        }
        self._col_anchors = {
            "name": "w",
            "price": "e",
            "quantity": "center",
        }

        for col in columns:
            self.product_table.heading(
                col,
                text=self._col_labels[col],
                anchor=self._col_anchors[col],
                command=lambda c=col: self._sort_by(c),
            )

        self.product_table.column("name", anchor="w", width=380)
        self.product_table.column("price", anchor="e", width=180)
        self.product_table.column("quantity", anchor="center", width=130)

        self.product_table.bind("<Double-1>", lambda _e: self._handle_start_edit())
        self.product_table.bind("<Delete>", lambda _e: self._handle_delete_product())

        self._configure_table_tags(t)
        self._update_heading_indicators()

        scrollbar = ttk.Scrollbar(
            self.table_card.content, orient="vertical", command=self.product_table.yview
        )
        self.product_table.configure(yscrollcommand=scrollbar.set)

        self.product_table.pack(
            side="left", fill="both", expand=True, padx=(4, PADDING_SMALL), pady=4
        )
        scrollbar.pack(side="right", fill="y", pady=4)

    def _build_bottom_bar(self) -> None:
        """Build the bottom action bar: Restock on the left, Edit & Delete on the right."""
        t = self.app.theme
        bottom_frame = tk.Frame(self, bg=t["bg"])
        bottom_frame.pack(side="bottom", fill="x", pady=(PADDING_MEDIUM, 0))
        self._bg_frames.append(bottom_frame)

        # --- Left side: Restock controls ---
        restock_label = tk.Label(
            bottom_frame,
            text="Restock:",
            font=(FONT_FAMILY_BODY, FONT_SIZE_BODY, "bold"),
            bg=t["bg"],
            fg=t["text"],
        )
        restock_label.pack(side="left", padx=(0, PADDING_SMALL))
        self.restock_label = restock_label

        self.restock_dropdown = RoundedCombobox(
            bottom_frame,
            bg_color=t["input_bg"],
            border_color=t["input_border"],
            focus_color=t["input_focus"],
            parent_bg=t["bg"],
            width=22,
            font=(FONT_FAMILY_BODY, FONT_SIZE_BODY),
            state="readonly",
            radius=RADIUS_INPUT,
        )
        self.restock_dropdown.pack(side="left", padx=(0, PADDING_SMALL))

        self.restock_quantity_entry = RoundedEntry(
            bottom_frame,
            bg_color=t["input_bg"],
            fg_color=t["text"],
            border_color=t["input_border"],
            focus_color=t["input_focus"],
            parent_bg=t["bg"],
            width=8,
            font=(FONT_FAMILY_BODY, FONT_SIZE_BODY),
            radius=RADIUS_INPUT,
            placeholder="Qty",
            placeholder_color=t["placeholder"],
        )
        self.restock_quantity_entry.pack(side="left", padx=(0, PADDING_SMALL))
        self.restock_quantity_entry.bind_entry("<Return>", lambda _e: self._handle_restock())
        self._entries.append(self.restock_quantity_entry)

        self.restock_button = RoundedButton(
            bottom_frame,
            text="🔁  Restock",
            font=(FONT_FAMILY_BODY, FONT_SIZE_BODY, "bold"),
            bg_color=t["primary"],
            hover_color=t["primary_hover"],
            fg_color=t["button_text"],
            parent_bg=t["bg"],
            padx=16,
            height=38,
            radius=RADIUS_BUTTON,
            command=self._handle_restock,
        )
        self.restock_button.pack(side="left", padx=(4, 0))

        # --- Right side: Delete & Edit selected product ---
        self.delete_button = RoundedButton(
            bottom_frame,
            text="🗑  Delete",
            font=(FONT_FAMILY_BODY, FONT_SIZE_BODY, "bold"),
            bg_color=t["danger_bg"],
            hover_color=t["danger_hover"],
            fg_color=t["button_text"],
            parent_bg=t["bg"],
            padx=16,
            height=38,
            radius=RADIUS_BUTTON,
            command=self._handle_delete_product,
        )
        self.delete_button.pack(side="right")

        self.edit_button = RoundedButton(
            bottom_frame,
            text="✏  Edit",
            font=(FONT_FAMILY_BODY, FONT_SIZE_BODY, "bold"),
            bg_color=t["secondary_bg"],
            hover_color=t["secondary_hover"],
            fg_color=t["secondary_fg"],
            parent_bg=t["bg"],
            padx=16,
            height=38,
            radius=RADIUS_BUTTON,
            command=self._handle_start_edit,
        )
        self.edit_button.pack(side="right", padx=(0, PADDING_SMALL))

    # ------------------------------------------------------------------
    # SORTING
    # ------------------------------------------------------------------

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
            self.product_table.heading(col, text=text)

    # ------------------------------------------------------------------
    # THEME
    # ------------------------------------------------------------------

    def _configure_table_tags(self, theme: dict[str, str]) -> None:
        self.product_table.tag_configure("even", background=theme["table_row_bg"])
        self.product_table.tag_configure("odd", background=theme["table_row_alt_bg"])

    def apply_theme(self, theme: dict[str, str]) -> None:
        """Update all widgets on this page to match the active theme."""
        self.configure(bg=theme["bg"])
        self.heading_label.configure(bg=theme["bg"], fg=theme["heading"])

        for frame in self._bg_frames:
            frame.configure(bg=theme["bg"])
        for label in self._field_labels:
            label.configure(bg=theme["bg"], fg=theme["text_light"])
        self.restock_label.configure(bg=theme["bg"], fg=theme["text"])

        for entry in self._entries:
            entry.apply_colors(
                bg_color=theme["input_bg"],
                fg_color=theme["text"],
                border_color=theme["input_border"],
                focus_color=theme["input_focus"],
                parent_bg=theme["bg"],
                placeholder_color=theme["placeholder"],
            )

        self.restock_dropdown.apply_colors(
            bg_color=theme["input_bg"],
            border_color=theme["input_border"],
            focus_color=theme["input_focus"],
            parent_bg=theme["bg"],
        )

        submit_bg = theme["accent"] if self._editing_product_name else theme["primary"]
        submit_hover = (
            theme["accent_hover"] if self._editing_product_name else theme["primary_hover"]
        )
        self.submit_button.apply_colors(
            bg_color=submit_bg,
            hover_color=submit_hover,
            fg_color=theme["button_text"],
            parent_bg=theme["bg"],
        )
        self.restock_button.apply_colors(
            bg_color=theme["primary"],
            hover_color=theme["primary_hover"],
            fg_color=theme["button_text"],
            parent_bg=theme["bg"],
        )
        for sec_btn in (self.edit_button, self.cancel_edit_button):
            sec_btn.apply_colors(
                bg_color=theme["secondary_bg"],
                hover_color=theme["secondary_hover"],
                fg_color=theme["secondary_fg"],
                parent_bg=theme["bg"],
            )
        self.delete_button.apply_colors(
            bg_color=theme["danger_bg"],
            hover_color=theme["danger_hover"],
            fg_color=theme["button_text"],
            parent_bg=theme["bg"],
        )

        self.table_card.apply_colors(
            bg_color=theme["card"],
            parent_bg=theme["bg"],
            border_color=theme["card_border"],
        )
        self._configure_table_tags(theme)

    # ------------------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------------------

    def _get_selected_product_name(self) -> str | None:
        selection = self.product_table.selection()
        if not selection:
            return None
        values = self.product_table.item(selection[0], "values")
        return values[0] if values else None

    def _handle_start_edit(self) -> None:
        """Load the selected product into the top form for editing."""
        product_name = self._get_selected_product_name()
        if not product_name:
            messagebox.showinfo(
                "Select a Product", "Please select a product from the table to edit."
            )
            return

        product = self.app.inventory_store.products.get(product_name)
        if product is None:
            return

        self._editing_product_name = product.name
        self._clear_form()
        self.name_entry.insert(0, product.name)
        price_str = (
            str(int(product.price))
            if product.price.is_integer()
            else f"{product.price:.2f}"
        )
        self.price_entry.insert(0, price_str)
        self.quantity_entry.insert(0, str(product.quantity))

        t = self.app.theme
        self.heading_label.configure(text=f'Editing "{product.name}"')
        self.submit_button.set_text("💾  Save Changes")
        self.submit_button.apply_colors(
            bg_color=t["accent"],
            hover_color=t["accent_hover"],
            fg_color=t["button_text"],
            parent_bg=t["bg"],
        )
        if not self.cancel_edit_button.winfo_ismapped():
            self.cancel_edit_button.pack(side="left", padx=(PADDING_SMALL, 0), pady=(21, 0))
        self.name_entry.focus_set()

    def _exit_edit_mode(self) -> None:
        """Return the top form back to standard 'Add a Product' mode."""
        self._editing_product_name = None
        self._clear_form()
        t = self.app.theme
        self.heading_label.configure(text="Add a Product")
        self.submit_button.set_text("＋  Add Product")
        self.submit_button.apply_colors(
            bg_color=t["primary"],
            hover_color=t["primary_hover"],
            fg_color=t["button_text"],
            parent_bg=t["bg"],
        )
        self.cancel_edit_button.pack_forget()

    def _handle_submit_product(self) -> None:
        """Validate the form and either add a new product or save edits."""
        is_editing = self._editing_product_name is not None
        error_title = "Could Not Save Changes" if is_editing else "Could Not Add Product"

        try:
            existing_names = self.app.inventory_store.get_product_names()
            name = validate_product_name(
                self.name_entry.get(),
                existing_names,
                ignore_name=self._editing_product_name,
            )
            price = validate_price(self.price_entry.get())
            quantity = validate_quantity(self.quantity_entry.get())
        except ValidationError as error:
            messagebox.showerror(error_title, str(error))
            return

        if is_editing:
            original_name = self._editing_product_name
            self.app.inventory_store.update_product(original_name, name, price, quantity)
            self._exit_edit_mode()
            messagebox.showinfo("Product Updated", f'"{name}" was updated successfully.')
        else:
            self.app.inventory_store.add_product(name, price, quantity)
            self._clear_form()
            messagebox.showinfo("Product Added", f'"{name}" was added successfully.')

        self.app.refresh_all_pages()

    def _handle_delete_product(self) -> None:
        """Delete the selected product from inventory after user confirmation."""
        product_name = self._get_selected_product_name()
        if not product_name:
            messagebox.showinfo(
                "Select a Product", "Please select a product from the table to delete."
            )
            return

        confirmed = messagebox.askyesno(
            "Confirm Delete",
            f'Are you sure you want to delete "{product_name}" from inventory?\n\n'
            "Past sales history records will be kept.",
        )
        if not confirmed:
            return

        self.app.inventory_store.delete_product(product_name)
        if self._editing_product_name == product_name:
            self._exit_edit_mode()

        self.app.refresh_all_pages()
        messagebox.showinfo("Product Deleted", f'"{product_name}" was removed from inventory.')

    def _clear_form(self) -> None:
        """Empty the input fields after a successful add or cancel."""
        self.name_entry.delete(0, tk.END)
        self.price_entry.delete(0, tk.END)
        self.quantity_entry.delete(0, tk.END)

    def _handle_restock(self) -> None:
        """Validate and apply a restock to the chosen product."""
        product_name = self.restock_dropdown.get()

        if not product_name:
            messagebox.showerror("Could Not Restock", "Please choose a product to restock.")
            return

        try:
            extra_quantity = validate_quantity(self.restock_quantity_entry.get())
        except ValidationError as error:
            messagebox.showerror("Could Not Restock", str(error))
            return

        if extra_quantity == 0:
            messagebox.showerror(
                "Could Not Restock", "Please enter a quantity greater than zero."
            )
            return

        updated_product = self.app.inventory_store.restock_product(
            product_name, extra_quantity
        )
        self.restock_quantity_entry.delete(0, tk.END)
        messagebox.showinfo(
            "Restocked",
            f'"{product_name}" now has {updated_product.quantity} units in stock.',
        )
        self.app.refresh_all_pages()

    # ------------------------------------------------------------------
    # REFRESH
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Reload the table with aligned NGN prices and current sort order."""
        self.product_table.delete(*self.product_table.get_children())

        products = self.app.inventory_store.get_all_products()
        if self._sort_column == "price":
            products.sort(key=lambda p: (p.price, p.name.lower()), reverse=self._sort_reverse)
        elif self._sort_column == "quantity":
            products.sort(key=lambda p: (p.quantity, p.name.lower()), reverse=self._sort_reverse)
        else:
            products.sort(key=lambda p: p.name.lower(), reverse=self._sort_reverse)

        max_price = max((p.price for p in products), default=0.0)

        for index, product in enumerate(products):
            stripe_tag = "even" if index % 2 == 0 else "odd"
            self.product_table.insert(
                "",
                tk.END,
                values=(
                    product.name,
                    format_currency_aligned(product.price, max_price),
                    product.quantity,
                ),
                tags=(stripe_tag,),
            )

        product_names = self.app.inventory_store.get_product_names()
        self.restock_dropdown.set_values(product_names)
        if self.restock_dropdown.get() not in product_names:
            self.restock_dropdown.set("")
