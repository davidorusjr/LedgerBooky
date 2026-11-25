"""
constants.py

This file holds every fixed value used across the LedgerBooky application:
colours (for both Light Mode and Dark Mode), corner radii, fonts, sizes,
file paths, and the business rules (like the low stock threshold).

Purpose of this file:
Instead of typing a hex colour code or font name in many different files,
I type it once here and reuse it everywhere. If I ever want to change
the look of the app, I only need to change it in this one place.
"""

# -----------------------------
# WINDOW SETTINGS
# -----------------------------

WINDOW_TITLE = "Ledger Booky"
WINDOW_WIDTH = 1040
WINDOW_HEIGHT = 690

# -----------------------------
# THEME COLOUR PALETTES
# -----------------------------

LIGHT_THEME: dict[str, str] = {
    "bg": "#F7F7F5",                # Main window background (warm off-white)
    "card": "#FFFFFF",              # Cards, panels, table surfaces
    "card_border": "#E3E5E0",       # Subtle card outline
    "input_bg": "#FFFFFF",          # Text input & dropdown fill
    "input_border": "#D2D6D0",      # Unfocused input border
    "input_focus": "#0E91E3",       # Focused input highlight border
    "placeholder": "#9AA0A8",       # Subtle input placeholder text
    "title": "#083C6A",             # Brand title text
    "heading": "#083C6A",           # Section / page headings
    "card_number": "#083C6A",       # Dashboard KPI numbers
    "primary": "#083C6A",           # Primary buttons & inactive nav pills
    "primary_hover": "#0C528F",     # Primary button hover state
    "accent": "#0E91E3",            # Active nav pill & highlights
    "accent_hover": "#0B7CC4",      # Active nav pill hover state
    "secondary_bg": "#E8EEF4",      # Secondary pill buttons (Edit, Cancel, Filter)
    "secondary_hover": "#D5E1EC",   # Secondary pill hover state
    "secondary_fg": "#083C6A",      # Secondary pill text
    "danger_bg": "#C53030",         # Destructive pill buttons (Delete, Void)
    "danger_hover": "#A52424",      # Destructive pill hover state
    "text": "#2B2F36",              # Primary body text
    "text_light": "#6E747E",        # Subtitles & helper captions
    "button_text": "#FFFFFF",       # Text on top of primary/accent/danger buttons
    "table_header_bg": "#EEF3F8",   # Table column header background
    "table_header_fg": "#083C6A",   # Table column header text
    "table_row_bg": "#FFFFFF",      # Even table row background
    "table_row_alt_bg": "#F7F9FB",  # Odd table row background (zebra stripe)
    "table_select_bg": "#DCEEFF",   # Selected table row background
    "table_select_fg": "#083C6A",   # Selected table row text
    "scrollbar_trough": "#F1F3F5",  # Scrollbar track
    "scrollbar_thumb": "#C5CCD6",   # Scrollbar thumb
    "scrollbar_hover": "#9FA9B8",   # Scrollbar thumb on hover
    "toggle_bg": "#FFFFFF",         # Theme toggle pill background
    "toggle_hover": "#EEF3F8",      # Theme toggle pill hover background
    "toggle_border": "#D8DDE3",     # Theme toggle pill border
    "toggle_track": "#CBD5E1",      # Toggle switch track (OFF)
    "toggle_knob": "#FFFFFF",       # Toggle switch knob
    "toggle_text": "#083C6A",       # Theme toggle label text
    "divider": "#E8EAE6",           # Thin horizontal separator inside cards
    "success": "#2F855A",           # Green  - "In Stock"
    "warning": "#D97706",           # Orange - "Low Stock"
    "danger": "#C53030",            # Red    - "Out of Stock" / Errors
}

DARK_THEME: dict[str, str] = {
    "bg": "#0F172A",                # Deep slate-navy window background
    "card": "#1E293B",              # Elevated dark slate card surface
    "card_border": "#334155",       # Crisp subtle slate border
    "input_bg": "#1E293B",          # Text input & dropdown fill
    "input_border": "#475569",      # Unfocused input border
    "input_focus": "#38BDF8",       # Focused input highlight border
    "placeholder": "#64748B",       # Subtle input placeholder text
    "title": "#7DD3FC",             # Luminous sky-blue brand title
    "heading": "#F1F5F9",           # High-contrast light headings
    "card_number": "#38BDF8",       # Vibrant sky-blue Dashboard KPI numbers
    "primary": "#1E3A5F",           # Deep navy buttons & inactive nav pills
    "primary_hover": "#284E7D",     # Primary button hover state
    "accent": "#0E91E3",            # Active nav pill & highlights
    "accent_hover": "#29A3F0",      # Active nav pill hover state
    "secondary_bg": "#273549",      # Secondary pill buttons (Edit, Cancel, Filter)
    "secondary_hover": "#33455E",   # Secondary pill hover state
    "secondary_fg": "#E2E8F0",      # Secondary pill text
    "danger_bg": "#DC2626",         # Destructive pill buttons (Delete, Void)
    "danger_hover": "#EF4444",      # Destructive pill hover state
    "text": "#E2E8F0",              # Crisp light slate body text
    "text_light": "#94A3B8",        # Muted slate subtitles & captions
    "button_text": "#FFFFFF",       # White text on buttons
    "table_header_bg": "#263449",   # Table column header background
    "table_header_fg": "#93C5FD",   # Table column header text
    "table_row_bg": "#1E293B",      # Even table row background
    "table_row_alt_bg": "#243247",  # Odd table row background (zebra stripe)
    "table_select_bg": "#0C4A6E",   # Selected table row background
    "table_select_fg": "#F8FAFC",   # Selected table row text
    "scrollbar_trough": "#1E293B",  # Scrollbar track
    "scrollbar_thumb": "#475569",   # Scrollbar thumb
    "scrollbar_hover": "#64748B",   # Scrollbar thumb on hover
    "toggle_bg": "#1E293B",         # Theme toggle pill background
    "toggle_hover": "#27364C",      # Theme toggle pill hover background
    "toggle_border": "#334155",     # Theme toggle pill border
    "toggle_track": "#0E91E3",      # Toggle switch track (ON)
    "toggle_knob": "#F8FAFC",       # Toggle switch knob
    "toggle_text": "#E2E8F0",       # Theme toggle label text
    "divider": "#2D3B50",           # Thin horizontal separator inside cards
    "success": "#4ADE80",           # Bright emerald - "In Stock"
    "warning": "#FBBF24",           # Bright amber   - "Low Stock"
    "danger": "#F87171",            # Bright coral   - "Out of Stock" / Errors
}

# Default (Light Mode) colour aliases kept for convenience and readability
COLOR_BACKGROUND = LIGHT_THEME["bg"]
COLOR_PRIMARY = LIGHT_THEME["primary"]
COLOR_ACCENT = LIGHT_THEME["accent"]
COLOR_CARD = LIGHT_THEME["card"]
COLOR_TEXT = LIGHT_THEME["text"]
COLOR_TEXT_LIGHT = LIGHT_THEME["text_light"]
COLOR_SUCCESS = LIGHT_THEME["success"]
COLOR_WARNING = LIGHT_THEME["warning"]
COLOR_DANGER = LIGHT_THEME["danger"]
COLOR_BUTTON_TEXT = LIGHT_THEME["button_text"]

# -----------------------------
# CORNER RADII (ROUNDED UI)
# -----------------------------

RADIUS_CARD = 16
RADIUS_BUTTON = 18
RADIUS_INPUT = 10
RADIUS_TOGGLE = 17

# -------------
# FONTS
# -------------

FONT_FAMILY_TITLE = "Pacifico"                    # Cursive font for the title
FONT_FAMILY_TITLE_FALLBACK = "Lucida Handwriting"  # Backup font if the main font isn't available
FONT_FAMILY_BODY = "Segoe UI"                     # Used for normal text and buttons

FONT_SIZE_TITLE = 36
FONT_SIZE_SUBTITLE = 13
FONT_SIZE_NAV_BUTTON = 12
FONT_SIZE_HEADING = 18
FONT_SIZE_BODY = 11
FONT_SIZE_CARD_NUMBER = 21
FONT_SIZE_CARD_LABEL = 12

# --------------
# SPACING
# --------------

PADDING_SMALL = 8
PADDING_MEDIUM = 16
PADDING_LARGE = 28
PADDING_XLARGE = 40

# -------------
# FILE PATHS
# -------------

INVENTORY_FILE_PATH = "inventory.csv"
SALES_FILE_PATH = "sales.csv"
SETTINGS_FILE_PATH = "settings.json"

# --------------------
# CSV COLUMN HEADERS
# --------------------
# Keeping these as constants means storage.py and models.py always agree
# on the exact column names and order.

INVENTORY_CSV_HEADERS = ["name", "price", "quantity"]
SALES_CSV_HEADERS = ["date", "time", "product", "quantity", "amount"]

# ------------------
# BUSINESS RULES
# ------------------

LOW_STOCK_THRESHOLD = 5  # A product is "low stock" when quantity is below this

# -------------------------
# STOCK STATUS LABELS
# --------------------------
# Used by inventory.py to decide which colour and word to display.

STATUS_IN_STOCK = "In Stock"
STATUS_LOW_STOCK = "Low Stock"
STATUS_OUT_OF_STOCK = "Out of Stock"

# ------------------------
# NAVIGATION PAGE NAMES
# ------------------------
# Used by ui.py to know which page is which when switching frames.

PAGE_DASHBOARD = "dashboard"
PAGE_PRODUCTS = "products"
PAGE_SALES = "sales"
PAGE_INVENTORY = "inventory"
PAGE_HISTORY = "history"
