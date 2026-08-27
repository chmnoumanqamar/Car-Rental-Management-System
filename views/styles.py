"""
UI Styling & Component Helpers
Defines ttk styles, color schemes, custom cards, and reusable widget generators.
"""

import tkinter as tk
from tkinter import ttk
from typing import Tuple, List, Dict, Any, Optional

from config import THEME, FONTS

def apply_custom_styles(root: tk.Tk):
    """Configures global ttk style tokens."""
    style = ttk.Style()
    
    # Try using 'clam' theme for consistent cross-platform styling
    available = style.theme_names()
    if "clam" in available:
        style.theme_use("clam")

    # Treeview Styling
    style.configure(
        "Custom.Treeview",
        background=THEME["card_bg"],
        foreground=THEME["text_primary"],
        fieldbackground=THEME["card_bg"],
        font=FONTS["body"],
        rowheight=28,
        borderwidth=0
    )
    style.configure(
        "Custom.Treeview.Heading",
        background=THEME["table_header_bg"],
        foreground=THEME["table_header_fg"],
        font=FONTS["small_bold"],
        relief="flat",
        padding=(8, 6)
    )
    style.map(
        "Custom.Treeview.Heading",
        background=[("active", THEME["sidebar_hover"])]
    )
    style.map(
        "Custom.Treeview",
        background=[("selected", THEME["table_row_select"])],
        foreground=[("selected", THEME["text_primary"])]
    )

    # TCombobox Styling
    style.configure(
        "TCombobox",
        fieldbackground=THEME["card_bg"],
        background=THEME["main_bg"],
        foreground=THEME["text_primary"],
        font=FONTS["body"],
        padding=4
    )

    # TEntry Styling
    style.configure(
        "TEntry",
        fieldbackground=THEME["card_bg"],
        foreground=THEME["text_primary"],
        padding=6
    )

    # Scrollbar
    style.configure(
        "Vertical.TScrollbar",
        background=THEME["main_bg"],
        troughcolor=THEME["card_bg"],
        borderwidth=0,
        arrowsize=14
    )

def center_window(window: tk.Tk or tk.Toplevel, width: int, height: int):
    """Centers a tkinter window on the screen."""
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = max(0, (screen_width - width) // 2)
    y = max(0, (screen_height - height) // 2 - 30)
    window.geometry(f"{width}x{height}+{x}+{y}")

class StatCard(tk.Frame):
    """A modern KPI Dashboard stat card with top accent stripe, icon, title, value, and footer."""

    def __init__(
        self,
        parent,
        title: str,
        value: str,
        subtext: str = "",
        accent_color: str = THEME["primary"],
        icon_text: str = "●",
        **kwargs
    ):
        super().__init__(parent, bg=THEME["card_bg"], highlightbackground=THEME["card_border"], highlightthickness=1, bd=0, **kwargs)
        
        # Top Accent Color Stripe
        stripe = tk.Frame(self, bg=accent_color, height=4)
        stripe.pack(fill="x", side="top")

        content_frame = tk.Frame(self, bg=THEME["card_bg"], padx=16, pady=12)
        content_frame.pack(fill="both", expand=True)

        # Header Row (Title & Icon)
        header_row = tk.Frame(content_frame, bg=THEME["card_bg"])
        header_row.pack(fill="x", anchor="w")

        title_lbl = tk.Label(
            header_row,
            text=title.upper(),
            font=FONTS["small_bold"],
            fg=THEME["text_muted"],
            bg=THEME["card_bg"]
        )
        title_lbl.pack(side="left")

        icon_lbl = tk.Label(
            header_row,
            text=icon_text,
            font=("Segoe UI", 12, "bold"),
            fg=accent_color,
            bg=THEME["card_bg"]
        )
        icon_lbl.pack(side="right")

        # Value Label
        self.val_lbl = tk.Label(
            content_frame,
            text=value,
            font=FONTS["title_large"],
            fg=THEME["text_primary"],
            bg=THEME["card_bg"]
        )
        self.val_lbl.pack(anchor="w", pady=(6, 2))

        # Subtext Label
        if subtext:
            self.sub_lbl = tk.Label(
                content_frame,
                text=subtext,
                font=FONTS["small"],
                fg=THEME["text_secondary"],
                bg=THEME["card_bg"]
            )
            self.sub_lbl.pack(anchor="w")

    def update_value(self, new_value: str, new_subtext: Optional[str] = None):
        """Updates value dynamically."""
        self.val_lbl.config(text=new_value)
        if new_subtext is not None and hasattr(self, "sub_lbl"):
            self.sub_lbl.config(text=new_subtext)

def create_button(
    parent,
    text: str,
    command,
    bg_color: str = THEME["primary"],
    fg_color: str = "#FFFFFF",
    hover_color: Optional[str] = None,
    font = FONTS["body_bold"],
    padx: int = 14,
    pady: int = 8,
    width: Optional[int] = None
) -> tk.Button:
    """Creates a styled modern Tkinter flat button with smooth hover effect."""
    btn = tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg_color,
        fg=fg_color,
        activebackground=hover_color or bg_color,
        activeforeground=fg_color,
        font=font,
        bd=0,
        padx=padx,
        pady=pady,
        relief="flat",
        cursor="hand2"
    )
    if width:
        btn.config(width=width)

    def on_enter(e):
        if hover_color:
            btn.config(bg=hover_color)

    def on_leave(e):
        btn.config(bg=bg_color)

    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    return btn

def create_scrollable_treeview(
    parent,
    columns: List[Tuple[str, str, int]], # (col_id, col_name, width)
    selectmode: str = "browse"
) -> Tuple[ttk.Treeview, tk.Frame]:
    """
    Creates a responsive Treeview table enclosed in a frame with vertical & horizontal scrollbars.
    """
    container = tk.Frame(parent, bg=THEME["card_bg"], highlightbackground=THEME["card_border"], highlightthickness=1)
    
    col_ids = [c[0] for c in columns]
    tree = ttk.Treeview(
        container,
        columns=col_ids,
        show="headings",
        selectmode=selectmode,
        style="Custom.Treeview"
    )

    # Scrollbars
    v_scroll = ttk.Scrollbar(container, orient="vertical", command=tree.yview, style="Vertical.TScrollbar")
    h_scroll = ttk.Scrollbar(container, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

    # Configure columns
    for col_id, col_name, width in columns:
        tree.heading(col_id, text=col_name, anchor="center")
        tree.column(col_id, width=width, anchor="center", minwidth=width // 2)

    # Alternate row colors
    tree.tag_configure("evenrow", background=THEME["table_row_alt"])
    tree.tag_configure("oddrow", background=THEME["card_bg"])

    # Layout
    tree.grid(row=0, column=0, sticky="nsew")
    v_scroll.grid(row=0, column=1, sticky="ns")
    h_scroll.grid(row=1, column=0, sticky="ew")

    container.grid_rowconfigure(0, weight=1)
    container.grid_columnconfigure(0, weight=1)

    return tree, container
