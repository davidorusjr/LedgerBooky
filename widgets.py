"""
widgets.py

This file defines reusable, modern rounded UI widgets for LedgerBooky:

    - RoundedCard     -> Rounded container card (for KPIs, summaries, tables)
    - RoundedButton   -> Pill-shaped button with hover & active states
    - RoundedEntry    -> Text input box with rounded corners & focus ring
    - RoundedCombobox -> Dropdown box styled to match RoundedEntry
    - ThemeToggle     -> Pill switch for toggling between Light & Dark mode

When Pillow (PIL) is installed, rounded shapes are supersampled (4x) for
crisp, anti-aliased edges. If Pillow is not available, every widget falls
back cleanly to pure Tkinter Canvas shapes so the app still runs with
zero third-party dependencies.
"""

import tkinter as tk
from tkinter import font as tkfont, ttk
from typing import Callable

from constants import (
    FONT_FAMILY_BODY,
    FONT_SIZE_BODY,
    RADIUS_BUTTON,
    RADIUS_CARD,
    RADIUS_INPUT,
    RADIUS_TOGGLE,
)

try:
    from PIL import Image, ImageDraw, ImageTk

    HAS_PIL = True
except ImportError:
    HAS_PIL = False


# Cache for rendered rounded-rectangle PhotoImages so hover/theme updates are instant.
_IMAGE_CACHE: dict[tuple, object] = {}
_MAX_CACHE_SIZE = 512


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert a '#RRGGBB' hex colour string to an (R, G, B) tuple."""
    color = hex_color.lstrip("#")
    if len(color) == 3:
        color = "".join(ch * 2 for ch in color)
    return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


def _rounded_rect_points(x1: float, y1: float, x2: float, y2: float, radius: float) -> list[float]:
    """Return smooth polygon control points for pure-Tkinter fallback drawing."""
    r = max(0.0, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
    return [
        x1 + r, y1,
        x1 + r, y1,
        x2 - r, y1,
        x2 - r, y1,
        x2, y1,
        x2, y1 + r,
        x2, y1 + r,
        x2, y2 - r,
        x2, y2 - r,
        x2, y2,
        x2 - r, y2,
        x2 - r, y2,
        x1 + r, y2,
        x1 + r, y2,
        x1, y2,
        x1, y2 - r,
        x1, y2 - r,
        x1, y1 + r,
        x1, y1 + r,
        x1, y1,
    ]


def _get_rounded_rect_image(
    canvas: tk.Canvas,
    width: int,
    height: int,
    radius: int,
    fill_color: str,
    parent_bg: str,
    border_color: str | None = None,
    border_width: int = 0,
):
    """
    Create (or retrieve from cache) a 4x supersampled anti-aliased
    rounded-rectangle PhotoImage blended smoothly onto parent_bg.
    """
    root_id = id(canvas.winfo_toplevel())
    cache_key = (
        root_id,
        width,
        height,
        radius,
        fill_color,
        parent_bg,
        border_color,
        border_width,
    )
    if cache_key in _IMAGE_CACHE:
        return _IMAGE_CACHE[cache_key]

    scale = 4
    sw, sh = width * scale, height * scale
    sr = min(radius * scale, sw // 2, sh // 2)

    img = Image.new("RGB", (sw, sh), _hex_to_rgb(parent_bg))
    draw = ImageDraw.Draw(img)

    outline_rgb = _hex_to_rgb(border_color) if (border_color and border_width > 0) else None
    bw = border_width * scale if outline_rgb else 0

    draw.rounded_rectangle(
        [0, 0, sw - 1, sh - 1],
        radius=sr,
        fill=_hex_to_rgb(fill_color),
        outline=outline_rgb,
        width=bw,
    )

    img = img.resize((width, height), Image.Resampling.LANCZOS)
    photo = ImageTk.PhotoImage(img, master=canvas.winfo_toplevel())

    if len(_IMAGE_CACHE) >= _MAX_CACHE_SIZE:
        _IMAGE_CACHE.clear()
    _IMAGE_CACHE[cache_key] = photo
    return photo


def _draw_rounded_surface(
    canvas: tk.Canvas,
    width: int,
    height: int,
    radius: int,
    fill_color: str,
    parent_bg: str,
    border_color: str | None = None,
    border_width: int = 0,
) -> None:
    """Render a rounded rectangle onto a Canvas, using PIL when available."""
    canvas.delete("bg_shape")
    if width < 2 or height < 2:
        return

    if HAS_PIL:
        photo = _get_rounded_rect_image(
            canvas=canvas,
            width=width,
            height=height,
            radius=radius,
            fill_color=fill_color,
            parent_bg=parent_bg,
            border_color=border_color,
            border_width=border_width,
        )
        canvas._bg_photo = photo  # Keep a reference so Tkinter doesn't GC it
        canvas.create_image(0, 0, image=photo, anchor="nw", tags=("bg_shape",))
    else:
        inset = max(1, border_width)
        points = _rounded_rect_points(inset, inset, width - inset, height - inset, radius)
        canvas.create_polygon(
            points,
            smooth=True,
            splinesteps=36,
            fill=fill_color,
            outline=border_color if (border_color and border_width > 0) else fill_color,
            width=border_width if (border_color and border_width > 0) else 0,
            tags=("bg_shape",),
        )
    canvas.tag_lower("bg_shape")


class RoundedCard(tk.Frame):
    """
    A rounded rectangular container card.

    Pack or grid child widgets inside `card.content` rather than directly
    into `card`. Because `self.content` is managed with pack(), the card
    automatically wraps its children's natural size AND expands smoothly
    when packed with fill='both', expand=True.
    """

    def __init__(
        self,
        parent: tk.Widget,
        bg_color: str,
        parent_bg: str,
        border_color: str | None = None,
        border_width: int = 1,
        radius: int = RADIUS_CARD,
        content_pad: int | None = None,
    ):
        super().__init__(parent, bg=parent_bg, bd=0, highlightthickness=0)
        self._bg_color = bg_color
        self._parent_bg = parent_bg
        self._border_color = border_color
        self._border_width = border_width
        self._radius = radius

        # Keep inner frame safely inside the curved corners.
        inset = content_pad if content_pad is not None else max(6, radius // 2)

        self._canvas = tk.Canvas(self, bg=parent_bg, bd=0, highlightthickness=0)
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self._canvas.bind("<Configure>", self._on_resize)

        self.content = tk.Frame(self, bg=bg_color, bd=0, highlightthickness=0)
        self.content.pack(fill="both", expand=True, padx=inset, pady=inset)
        self.content.lift()

    def _on_resize(self, event=None) -> None:
        self._redraw()

    def _redraw(self) -> None:
        w = self._canvas.winfo_width()
        h = self._canvas.winfo_height()
        _draw_rounded_surface(
            canvas=self._canvas,
            width=w,
            height=h,
            radius=self._radius,
            fill_color=self._bg_color,
            parent_bg=self._parent_bg,
            border_color=self._border_color,
            border_width=self._border_width,
        )

    def apply_colors(
        self,
        bg_color: str,
        parent_bg: str,
        border_color: str | None = None,
    ) -> None:
        """Update the card's colours cleanly (used when toggling Light/Dark mode)."""
        self._bg_color = bg_color
        self._parent_bg = parent_bg
        self._border_color = border_color
        self.configure(bg=parent_bg)
        self._canvas.configure(bg=parent_bg)
        self.content.configure(bg=bg_color)
        self._redraw()


class RoundedButton(tk.Canvas):
    """
    A pill-shaped / rounded button with smooth hover and click feedback.
    """

    def __init__(
        self,
        parent: tk.Widget,
        text: str,
        command: Callable[[], None],
        bg_color: str,
        hover_color: str,
        fg_color: str,
        parent_bg: str,
        font: tuple = (FONT_FAMILY_BODY, FONT_SIZE_BODY, "bold"),
        padx: int = 18,
        pady: int = 9,
        radius: int = RADIUS_BUTTON,
        height: int | None = None,
        min_width: int = 0,
    ):
        self._text = text
        self._command = command
        self._bg_color = bg_color
        self._hover_color = hover_color
        self._fg_color = fg_color
        self._parent_bg = parent_bg
        self._font_spec = font
        self._padx = padx
        self._min_width = min_width
        self._radius = radius
        self._is_hovered = False

        measure_font = tkfont.Font(font=font)
        text_width = measure_font.measure(text)
        text_height = measure_font.metrics("linespace")

        self._width = max(min_width, text_width + padx * 2)
        self._height = height if height is not None else (text_height + pady * 2)

        super().__init__(
            parent,
            width=self._width,
            height=self._height,
            bg=parent_bg,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
        )

        self._text_item = self.create_text(
            self._width // 2,
            self._height // 2,
            text=self._text,
            font=self._font_spec,
            fill=self._fg_color,
        )

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonRelease-1>", self._on_release)

        self._redraw()

    def _redraw(self) -> None:
        fill = self._hover_color if self._is_hovered else self._bg_color
        _draw_rounded_surface(
            canvas=self,
            width=self._width,
            height=self._height,
            radius=self._radius,
            fill_color=fill,
            parent_bg=self._parent_bg,
        )
        self.itemconfigure(self._text_item, fill=self._fg_color)
        self.tag_raise(self._text_item)

    def _on_enter(self, _event=None) -> None:
        self._is_hovered = True
        self._redraw()

    def _on_leave(self, _event=None) -> None:
        self._is_hovered = False
        self._redraw()

    def _on_release(self, event) -> None:
        if 0 <= event.x <= self._width and 0 <= event.y <= self._height:
            if self._command:
                self._command()

    def set_text(self, text: str) -> None:
        """Update the button's label text and resize smoothly if needed."""
        self._text = text
        measure_font = tkfont.Font(font=self._font_spec)
        new_width = max(self._min_width, measure_font.measure(text) + self._padx * 2)
        if new_width != self._width:
            self._width = new_width
            self.configure(width=self._width)
            self.coords(self._text_item, self._width // 2, self._height // 2)
        self.itemconfigure(self._text_item, text=self._text)
        self._redraw()

    def apply_colors(
        self,
        bg_color: str,
        hover_color: str,
        fg_color: str,
        parent_bg: str,
    ) -> None:
        """Update button colours dynamically for theme switches or active nav state."""
        self._bg_color = bg_color
        self._hover_color = hover_color
        self._fg_color = fg_color
        self._parent_bg = parent_bg
        self.configure(bg=parent_bg)
        self._redraw()


class RoundedEntry(tk.Frame):
    """
    A rounded text input field that wraps a standard Tkinter Entry widget
    and highlights its border smoothly when focused.
    """

    def __init__(
        self,
        parent: tk.Widget,
        bg_color: str,
        fg_color: str,
        border_color: str,
        focus_color: str,
        parent_bg: str,
        width: int = 20,
        font: tuple = (FONT_FAMILY_BODY, FONT_SIZE_BODY),
        radius: int = RADIUS_INPUT,
        placeholder: str = "",
        placeholder_color: str = "#9AA0A8",
    ):
        super().__init__(parent, bg=parent_bg, bd=0, highlightthickness=0)
        self._bg_color = bg_color
        self._fg_color = fg_color
        self._border_color = border_color
        self._focus_color = focus_color
        self._parent_bg = parent_bg
        self._radius = radius
        self._placeholder = placeholder
        self._placeholder_color = placeholder_color
        self._showing_placeholder = False
        self._is_focused = False

        self._canvas = tk.Canvas(self, bg=parent_bg, bd=0, highlightthickness=0)
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self._canvas.bind("<Configure>", self._on_resize)

        self.entry = tk.Entry(
            self,
            font=font,
            width=width,
            bg=bg_color,
            fg=fg_color,
            insertbackground=fg_color,
            relief="flat",
            bd=0,
            highlightthickness=0,
        )
        self.entry.pack(fill="both", expand=True, padx=10, pady=8)
        self.entry.lift()

        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self._canvas.bind("<Button-1>", lambda _e: self.entry.focus_set())

        if self._placeholder:
            self._show_placeholder()

    def _show_placeholder(self) -> None:
        if not self._placeholder:
            return
        self.entry.delete(0, tk.END)
        self.entry.insert(0, self._placeholder)
        self.entry.configure(fg=self._placeholder_color)
        self._showing_placeholder = True

    def _hide_placeholder(self) -> None:
        if self._showing_placeholder:
            self.entry.delete(0, tk.END)
            self.entry.configure(fg=self._fg_color)
            self._showing_placeholder = False

    def _on_resize(self, _event=None) -> None:
        self._redraw()

    def _on_focus_in(self, _event=None) -> None:
        self._is_focused = True
        self._hide_placeholder()
        self._redraw()

    def _on_focus_out(self, _event=None) -> None:
        self._is_focused = False
        if self._placeholder and self.entry.get() == "":
            self._show_placeholder()
        self._redraw()

    def _redraw(self) -> None:
        w = self._canvas.winfo_width()
        h = self._canvas.winfo_height()
        border = self._focus_color if self._is_focused else self._border_color
        bw = 2 if self._is_focused else 1
        _draw_rounded_surface(
            canvas=self._canvas,
            width=w,
            height=h,
            radius=self._radius,
            fill_color=self._bg_color,
            parent_bg=self._parent_bg,
            border_color=border,
            border_width=bw,
        )

    def apply_colors(
        self,
        bg_color: str,
        fg_color: str,
        border_color: str,
        focus_color: str,
        parent_bg: str,
        placeholder_color: str | None = None,
    ) -> None:
        """Update input colours for theme switches."""
        self._bg_color = bg_color
        self._fg_color = fg_color
        self._border_color = border_color
        self._focus_color = focus_color
        self._parent_bg = parent_bg
        if placeholder_color is not None:
            self._placeholder_color = placeholder_color
        self.configure(bg=parent_bg)
        self._canvas.configure(bg=parent_bg)
        text_color = self._placeholder_color if self._showing_placeholder else fg_color
        self.entry.configure(bg=bg_color, fg=text_color, insertbackground=fg_color)
        self._redraw()

    # Forward common tk.Entry methods so callers can use RoundedEntry directly.
    def get(self) -> str:
        if self._showing_placeholder:
            return ""
        return self.entry.get()

    def delete(self, first, last=None) -> None:
        self._hide_placeholder()
        self.entry.delete(first, last)
        if not self._is_focused and self._placeholder and self.entry.get() == "":
            self._show_placeholder()

    def insert(self, index, string: str) -> None:
        self._hide_placeholder()
        self.entry.insert(index, string)

    def focus_set(self) -> None:
        self.entry.focus_set()

    def bind_entry(self, sequence: str, callback) -> None:
        self.entry.bind(sequence, callback, add="+")


class RoundedCombobox(tk.Frame):
    """
    A rounded container wrapping a borderless ttk.Combobox so dropdowns
    visually match RoundedEntry fields.
    """

    def __init__(
        self,
        parent: tk.Widget,
        bg_color: str,
        border_color: str,
        focus_color: str,
        parent_bg: str,
        width: int = 24,
        font: tuple = (FONT_FAMILY_BODY, FONT_SIZE_BODY),
        state: str = "readonly",
        radius: int = RADIUS_INPUT,
    ):
        super().__init__(parent, bg=parent_bg, bd=0, highlightthickness=0)
        self._bg_color = bg_color
        self._border_color = border_color
        self._focus_color = focus_color
        self._parent_bg = parent_bg
        self._radius = radius
        self._is_focused = False

        self._canvas = tk.Canvas(self, bg=parent_bg, bd=0, highlightthickness=0)
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self._canvas.bind("<Configure>", self._on_resize)

        self.combobox = ttk.Combobox(
            self,
            font=font,
            width=width,
            state=state,
            style="Rounded.TCombobox",
        )
        self.combobox.pack(fill="both", expand=True, padx=8, pady=5)
        self.combobox.lift()

        self.combobox.bind("<FocusIn>", self._on_focus_in)
        self.combobox.bind("<FocusOut>", self._on_focus_out)

    def _on_resize(self, _event=None) -> None:
        self._redraw()

    def _on_focus_in(self, _event=None) -> None:
        self._is_focused = True
        self._redraw()

    def _on_focus_out(self, _event=None) -> None:
        self._is_focused = False
        self._redraw()

    def _redraw(self) -> None:
        w = self._canvas.winfo_width()
        h = self._canvas.winfo_height()
        border = self._focus_color if self._is_focused else self._border_color
        bw = 2 if self._is_focused else 1
        _draw_rounded_surface(
            canvas=self._canvas,
            width=w,
            height=h,
            radius=self._radius,
            fill_color=self._bg_color,
            parent_bg=self._parent_bg,
            border_color=border,
            border_width=bw,
        )

    def apply_colors(
        self,
        bg_color: str,
        border_color: str,
        focus_color: str,
        parent_bg: str,
    ) -> None:
        """Update combobox container colours for theme switches."""
        self._bg_color = bg_color
        self._border_color = border_color
        self._focus_color = focus_color
        self._parent_bg = parent_bg
        self.configure(bg=parent_bg)
        self._canvas.configure(bg=parent_bg)
        self._redraw()

    # Forward common ttk.Combobox methods.
    def get(self) -> str:
        return self.combobox.get()

    def set(self, value: str) -> None:
        self.combobox.set(value)

    def set_values(self, values: list[str]) -> None:
        self.combobox.configure(values=values)

    def bind_select(self, callback) -> None:
        self.combobox.bind("<<ComboboxSelected>>", callback, add="+")


class ThemeToggle(tk.Canvas):
    """
    A sleek pill-shaped Dark Mode toggle switch with a sliding circular
    knob and clear 'Dark Mode' label.
    """

    def __init__(
        self,
        parent: tk.Widget,
        command: Callable[[], None],
        theme: dict[str, str],
        is_dark: bool = False,
    ):
        self._command = command
        self._theme = theme
        self._is_dark = is_dark
        self._is_hovered = False

        self._width = 136
        self._height = 36
        self._radius = RADIUS_TOGGLE

        super().__init__(
            parent,
            width=self._width,
            height=self._height,
            bg=theme["bg"],
            bd=0,
            highlightthickness=0,
            cursor="hand2",
        )

        self._label_item = self.create_text(
            88,
            self._height // 2,
            text="Dark Mode",
            font=(FONT_FAMILY_BODY, 10, "bold"),
            fill=theme["toggle_text"],
        )

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonRelease-1>", self._on_click)

        self._redraw()

    def _on_enter(self, _event=None) -> None:
        self._is_hovered = True
        self._redraw()

    def _on_leave(self, _event=None) -> None:
        self._is_hovered = False
        self._redraw()

    def _on_click(self, event) -> None:
        if 0 <= event.x <= self._width and 0 <= event.y <= self._height:
            if self._command:
                self._command()

    def _redraw(self) -> None:
        self.delete("toggle_art")
        w, h = self._width, self._height
        bg_fill = self._theme["toggle_hover"] if self._is_hovered else self._theme["toggle_bg"]
        border_col = self._theme["toggle_border"]
        parent_bg = self._theme["bg"]
        track_col = self._theme["toggle_track"]
        knob_col = self._theme["toggle_knob"]

        if HAS_PIL:
            scale = 4
            sw, sh = w * scale, h * scale
            img = Image.new("RGB", (sw, sh), _hex_to_rgb(parent_bg))
            draw = ImageDraw.Draw(img)

            # Outer pill container
            draw.rounded_rectangle(
                [0, 0, sw - 1, sh - 1],
                radius=self._radius * scale,
                fill=_hex_to_rgb(bg_fill),
                outline=_hex_to_rgb(border_col),
                width=1 * scale,
            )

            # Inner switch track (36 x 20 px, positioned on the left)
            tx1, ty1 = 10 * scale, 8 * scale
            tx2, ty2 = 46 * scale, 28 * scale
            draw.rounded_rectangle(
                [tx1, ty1, tx2, ty2],
                radius=10 * scale,
                fill=_hex_to_rgb(track_col),
            )

            # Sliding circular knob (14 x 14 px)
            knob_size = 14 * scale
            pad = 3 * scale
            kx1 = (tx2 - pad - knob_size) if self._is_dark else (tx1 + pad)
            ky1 = ty1 + pad
            draw.ellipse(
                [kx1, ky1, kx1 + knob_size, ky1 + knob_size],
                fill=_hex_to_rgb(knob_col),
            )

            img = img.resize((w, h), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img, master=self.winfo_toplevel())
            self._toggle_photo = photo
            self.create_image(0, 0, image=photo, anchor="nw", tags=("toggle_art",))
        else:
            # Pure Tkinter fallback
            points = _rounded_rect_points(1, 1, w - 1, h - 1, self._radius)
            self.create_polygon(
                points,
                smooth=True,
                splinesteps=36,
                fill=bg_fill,
                outline=border_col,
                width=1,
                tags=("toggle_art",),
            )
            track_pts = _rounded_rect_points(10, 8, 46, 28, 10)
            self.create_polygon(
                track_pts,
                smooth=True,
                splinesteps=24,
                fill=track_col,
                outline=track_col,
                tags=("toggle_art",),
            )
            kx1 = 29 if self._is_dark else 13
            self.create_oval(
                kx1, 11, kx1 + 14, 25, fill=knob_col, outline=knob_col, tags=("toggle_art",)
            )

        self.itemconfigure(self._label_item, fill=self._theme["toggle_text"])
        self.tag_lower("toggle_art")
        self.tag_raise(self._label_item)

    def apply_theme(self, theme: dict[str, str], is_dark: bool) -> None:
        """Refresh the switch position and colours when the app theme changes."""
        self._theme = theme
        self._is_dark = is_dark
        self.configure(bg=theme["bg"])
        self._redraw()
