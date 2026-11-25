"""
ui.py

This file defines the main application window (App). It is responsible for:

    - Setting up the window size, title, and theme (Light / Dark mode).
    - Building the header (title, subtitle, and Dark Mode toggle).
    - Building the rounded navigation bar (buttons to switch pages).
    - Styling shared ttk widgets (tables, dropdowns, scrollbars).
    - Holding all five page frames and switching between them.

This file does NOT contain the detailed content of each page — that
content lives in dashboard.py, products.py, sales.py, inventory.py,
and history.py. ui.py is the "shell" around those pages.
"""

import ctypes
import sys
import tkinter as tk
from tkinter import font as tkfont, ttk

from constants import (
    WINDOW_TITLE,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    LIGHT_THEME,
    DARK_THEME,
    FONT_FAMILY_TITLE,
    FONT_FAMILY_TITLE_FALLBACK,
    FONT_FAMILY_BODY,
    FONT_SIZE_TITLE,
    FONT_SIZE_SUBTITLE,
    FONT_SIZE_NAV_BUTTON,
    FONT_SIZE_BODY,
    PADDING_SMALL,
    PADDING_MEDIUM,
    PADDING_LARGE,
    PAGE_DASHBOARD,
    PAGE_PRODUCTS,
    PAGE_SALES,
    PAGE_INVENTORY,
    PAGE_HISTORY,
)
from storage import (
    InventoryStore,
    SalesStore,
    load_theme_preference,
    save_theme_preference,
)
from widgets import RoundedButton, ThemeToggle
from dashboard import DashboardPage
from products import ProductsPage
from sales import SalesPage
from inventory import InventoryPage
from history import HistoryPage


class App(tk.Tk):
    """
    The main application window.

    Holds one InventoryStore and one SalesStore (the single source of
    truth for all data), manages Light/Dark theme switching, and switches
    between page frames using a single content area instead of opening
    multiple windows.
    """

    def __init__(self):
        super().__init__()

        # Data: loaded once, shared by every page
        self.inventory_store = InventoryStore()
        self.sales_store = SalesStore()

        # Theme state (remembered locally between offline sessions)
        self.is_dark_mode: bool = load_theme_preference()
        self.theme: dict[str, str] = DARK_THEME if self.is_dark_mode else LIGHT_THEME
        self.active_page_name: str = PAGE_DASHBOARD

        # Window setup
        self.title(WINDOW_TITLE)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.resizable(False, False)
        self.configure(bg=self.theme["bg"])

        # Configure ttk widget styling (Treeview, Combobox, Scrollbar)
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self._apply_ttk_theme()

        self._title_font = self._build_title_font()

        self._build_header()
        self._build_navigation()
        self._build_content_area()

        self.pages: dict[str, tk.Frame] = {}
        self._create_pages()

        self.show_page(PAGE_DASHBOARD)
        self.after(10, self._apply_windows_titlebar_theme)

    # -----------------
    # SETUP HELPERS
    # -----------------

    def _build_title_font(self) -> tkfont.Font:
        """
        Try to use the set font for the title. If it is not
        installed on this computer, fall back to a clean standard font
        instead of crashing.
        """
        available_fonts = tkfont.families()
        family = (
            FONT_FAMILY_TITLE
            if FONT_FAMILY_TITLE in available_fonts
            else FONT_FAMILY_TITLE_FALLBACK
        )
        return tkfont.Font(family=family, size=FONT_SIZE_TITLE, weight="bold")

    def _build_header(self) -> None:
        """Build the title, subtitle, and top-right Dark Mode toggle."""
        self.header_frame = tk.Frame(self, bg=self.theme["bg"])
        self.header_frame.pack(fill="x", pady=(PADDING_MEDIUM, PADDING_SMALL))

        self.title_label = tk.Label(
            self.header_frame,
            text=WINDOW_TITLE,
            font=self._title_font,
            bg=self.theme["bg"],
            fg=self.theme["title"],
        )
        self.title_label.pack()

        self.subtitle_label = tk.Label(
            self.header_frame,
            text="Simple Shop Record Book",
            font=(FONT_FAMILY_BODY, FONT_SIZE_SUBTITLE),
            bg=self.theme["bg"],
            fg=self.theme["text_light"],
        )
        self.subtitle_label.pack(pady=(0, PADDING_SMALL))

        # Place the Dark Mode pill switch in the top-right corner so the title stays centered.
        self.theme_toggle = ThemeToggle(
            self.header_frame,
            command=self.toggle_theme,
            theme=self.theme,
            is_dark=self.is_dark_mode,
        )
        self.theme_toggle.place(relx=1.0, x=-PADDING_LARGE, y=8, anchor="ne")

    def _build_navigation(self) -> None:
        """Build the row of rounded pill navigation buttons."""
        self.nav_frame = tk.Frame(self, bg=self.theme["bg"])
        self.nav_frame.pack(fill="x", pady=(4, PADDING_MEDIUM))

        nav_buttons = [
            ("🏠  Dashboard", PAGE_DASHBOARD),
            ("📦  Products", PAGE_PRODUCTS),
            ("🛒  Sales", PAGE_SALES),
            ("📊  Inventory", PAGE_INVENTORY),
            ("📜  History", PAGE_HISTORY),
        ]

        # An inner frame centers the buttons as a group.
        self.nav_inner_frame = tk.Frame(self.nav_frame, bg=self.theme["bg"])
        self.nav_inner_frame.pack()

        self.nav_button_widgets: dict[str, RoundedButton] = {}

        for label_text, page_name in nav_buttons:
            button = RoundedButton(
                self.nav_inner_frame,
                text=label_text,
                font=(FONT_FAMILY_BODY, FONT_SIZE_NAV_BUTTON, "bold"),
                bg_color=self.theme["primary"],
                hover_color=self.theme["primary_hover"],
                fg_color=self.theme["button_text"],
                parent_bg=self.theme["bg"],
                padx=20,
                pady=10,
                radius=20,
                command=lambda name=page_name: self.show_page(name),
            )
            button.pack(side="left", padx=PADDING_SMALL)
            self.nav_button_widgets[page_name] = button

    def _build_content_area(self) -> None:
        """Build the container that holds every page frame, stacked on top of each other."""
        self.content_area = tk.Frame(self, bg=self.theme["bg"])
        self.content_area.pack(
            fill="both", expand=True, padx=PADDING_LARGE, pady=(0, PADDING_LARGE)
        )

    def _create_pages(self) -> None:
        """Create one frame for each page and place them all in the content area."""
        page_classes = {
            PAGE_DASHBOARD: DashboardPage,
            PAGE_PRODUCTS: ProductsPage,
            PAGE_SALES: SalesPage,
            PAGE_INVENTORY: InventoryPage,
            PAGE_HISTORY: HistoryPage,
        }

        for page_name, PageClass in page_classes.items():
            page = PageClass(
                parent=self.content_area,
                app=self,
            )
            page.place(x=0, y=0, relwidth=1, relheight=1)
            self.pages[page_name] = page

    # -----------------
    # THEME MANAGEMENT
    # -----------------

    def toggle_theme(self) -> None:
        """Switch between Light Mode and Dark Mode and save the preference."""
        self.is_dark_mode = not self.is_dark_mode
        self.theme = DARK_THEME if self.is_dark_mode else LIGHT_THEME
        save_theme_preference(self.is_dark_mode)
        self.apply_theme()

    def apply_theme(self) -> None:
        """Apply the active colour theme to the window shell, ttk widgets, and all pages."""
        t = self.theme

        self.configure(bg=t["bg"])
        self.header_frame.configure(bg=t["bg"])
        self.title_label.configure(bg=t["bg"], fg=t["title"])
        self.subtitle_label.configure(bg=t["bg"], fg=t["text_light"])
        self.theme_toggle.apply_theme(t, self.is_dark_mode)

        self.nav_frame.configure(bg=t["bg"])
        self.nav_inner_frame.configure(bg=t["bg"])
        self._highlight_active_nav_button(self.active_page_name)

        self.content_area.configure(bg=t["bg"])

        self._apply_ttk_theme()
        self._apply_windows_titlebar_theme()

        for page in self.pages.values():
            page.apply_theme(t)

    def _apply_ttk_theme(self) -> None:
        """Style ttk Treeview, Combobox (including dropdown list), and Scrollbar."""
        t = self.theme

        # Treeview body
        self.style.configure(
            "Treeview",
            background=t["table_row_bg"],
            fieldbackground=t["table_row_bg"],
            foreground=t["text"],
            rowheight=30,
            borderwidth=0,
            relief="flat",
            font=(FONT_FAMILY_BODY, FONT_SIZE_BODY),
        )
        self.style.map(
            "Treeview",
            background=[("selected", t["table_select_bg"])],
            foreground=[("selected", t["table_select_fg"])],
        )

        # Treeview column headings
        self.style.configure(
            "Treeview.Heading",
            background=t["table_header_bg"],
            foreground=t["table_header_fg"],
            relief="flat",
            borderwidth=0,
            padding=(10, 8),
            font=(FONT_FAMILY_BODY, FONT_SIZE_BODY, "bold"),
        )
        self.style.map(
            "Treeview.Heading",
            background=[("active", t["table_header_bg"])],
            foreground=[("active", t["table_header_fg"])],
        )

        # Remove default outer border around Treeview
        self.style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

        # Combobox styled cleanly inside RoundedCombobox (no inner square border)
        self.style.configure(
            "Rounded.TCombobox",
            fieldbackground=t["input_bg"],
            background=t["input_bg"],
            foreground=t["text"],
            arrowcolor=t["text_light"],
            bordercolor=t["input_bg"],
            lightcolor=t["input_bg"],
            darkcolor=t["input_bg"],
            focusfill=t["input_bg"],
            borderwidth=0,
            relief="flat",
            padding=(4, 3),
        )
        self.style.map(
            "Rounded.TCombobox",
            fieldbackground=[("readonly", t["input_bg"]), ("focus", t["input_bg"])],
            background=[("active", t["input_bg"]), ("readonly", t["input_bg"])],
            foreground=[("readonly", t["text"]), ("focus", t["text"])],
            bordercolor=[
                ("focus", t["input_bg"]),
                ("active", t["input_bg"]),
                ("readonly", t["input_bg"]),
            ],
            lightcolor=[
                ("focus", t["input_bg"]),
                ("active", t["input_bg"]),
                ("readonly", t["input_bg"]),
            ],
            darkcolor=[
                ("focus", t["input_bg"]),
                ("active", t["input_bg"]),
                ("readonly", t["input_bg"]),
            ],
            selectbackground=[("readonly", t["input_bg"])],
            selectforeground=[("readonly", t["text"])],
            arrowcolor=[("active", t["accent"])],
        )

        # Dropdown popup Listbox colours for future & existing Comboboxes
        self.option_add("*TCombobox*Listbox.background", t["card"])
        self.option_add("*TCombobox*Listbox.foreground", t["text"])
        self.option_add("*TCombobox*Listbox.selectBackground", t["accent"])
        self.option_add("*TCombobox*Listbox.selectForeground", t["button_text"])
        self._update_existing_combobox_popdowns()

        # Vertical Scrollbar
        self.style.configure(
            "Vertical.TScrollbar",
            background=t["scrollbar_thumb"],
            troughcolor=t["scrollbar_trough"],
            bordercolor=t["scrollbar_trough"],
            darkcolor=t["scrollbar_thumb"],
            lightcolor=t["scrollbar_thumb"],
            arrowcolor=t["text_light"],
            relief="flat",
            borderwidth=0,
            width=11,
        )
        self.style.map(
            "Vertical.TScrollbar",
            background=[("active", t["scrollbar_hover"])],
        )

    def _update_existing_combobox_popdowns(self) -> None:
        """Update dropdown popup listbox colours for any Combobox already created."""
        t = self.theme

        def walk(widget: tk.Widget) -> None:
            if isinstance(widget, ttk.Combobox):
                try:
                    popdown = widget.tk.eval(f"ttk::combobox::PopdownWindow {widget}")
                    widget.tk.call(
                        f"{popdown}.f.l",
                        "configure",
                        "-background", t["card"],
                        "-foreground", t["text"],
                        "-selectbackground", t["accent"],
                        "-selectforeground", t["button_text"],
                    )
                except tk.TclError:
                    pass
            for child in widget.winfo_children():
                walk(child)

        walk(self)

    def _apply_windows_titlebar_theme(self) -> None:
        """On Windows 10/11, tint the native window titlebar to match Light/Dark mode."""
        if sys.platform != "win32":
            return
        try:
            self.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            value = ctypes.c_int(1 if self.is_dark_mode else 0)
            # Attribute 20 works on Windows 11 & Windows 10 20H1+; 19 is the older fallback.
            for attr in (20, 19):
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, attr, ctypes.byref(value), ctypes.sizeof(value)
                )
        except Exception:
            pass

    # --------------
    # NAVIGATION
    # ---------------

    def show_page(self, page_name: str) -> None:
        """
        Show the requested page and hide the others.

        Also refreshes the page's content, so that switching to a page
        always shows the latest data (e.g. newly added products).
        """
        self.active_page_name = page_name
        page = self.pages[page_name]
        page.refresh()
        page.tkraise()
        self._highlight_active_nav_button(page_name)

    def _highlight_active_nav_button(self, active_page_name: str) -> None:
        """Change the colour of the active nav pill so the user can see where they are."""
        t = self.theme
        for page_name, button in self.nav_button_widgets.items():
            if page_name == active_page_name:
                button.apply_colors(
                    bg_color=t["accent"],
                    hover_color=t["accent_hover"],
                    fg_color=t["button_text"],
                    parent_bg=t["bg"],
                )
            else:
                button.apply_colors(
                    bg_color=t["primary"],
                    hover_color=t["primary_hover"],
                    fg_color=t["button_text"],
                    parent_bg=t["bg"],
                )

    def refresh_all_pages(self) -> None:
        """
        Refresh every page's data.

        Called after any action that changes shared data (adding a
        product, recording a sale) so that, for example, the Dashboard
        card numbers update even though the user is on the Sales page.
        """
        for page in self.pages.values():
            page.refresh()
