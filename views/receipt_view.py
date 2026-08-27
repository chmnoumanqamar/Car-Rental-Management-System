"""
Receipt Modal Window
Displays, exports, and prints professional car rental invoices & return receipts.
"""

import tkinter as tk
from tkinter import messagebox, filedialog
from pathlib import Path

from config import THEME, FONTS, REPORTS_DIR
from views.styles import center_window, create_button
from utils.helpers import logger

class ReceiptModal(tk.Toplevel):
    """Modal dialog displaying formatted ASCII receipt with save / export capabilities."""

    def __init__(self, parent, receipt_text: str, title: str = "Car Rental Receipt"):
        super().__init__(parent)
        self.title(title)
        self.receipt_text = receipt_text
        self.configure(bg=THEME["main_bg"])
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        center_window(self, 640, 680)

    def _build_ui(self):
        # Header Banner
        header_frame = tk.Frame(self, bg=THEME["sidebar_bg"], padx=20, pady=14)
        header_frame.pack(fill="x")

        tk.Label(
            header_frame,
            text="CAR RENTAL RECEIPT / INVOICE",
            font=FONTS["title_medium"],
            fg=THEME["sidebar_text"],
            bg=THEME["sidebar_bg"]
        ).pack(anchor="w")

        tk.Label(
            header_frame,
            text="Official Computerized Transaction Record",
            font=FONTS["small"],
            fg=THEME["sidebar_muted"],
            bg=THEME["sidebar_bg"]
        ).pack(anchor="w")

        # Body Container
        body_frame = tk.Frame(self, bg=THEME["main_bg"], padx=20, pady=15)
        body_frame.pack(fill="both", expand=True)

        # Receipt Text View
        text_container = tk.Frame(body_frame, bg=THEME["card_bg"], highlightbackground=THEME["card_border"], highlightthickness=1)
        text_container.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(text_container)
        scrollbar.pack(side="right", fill="y")

        self.text_widget = tk.Text(
            text_container,
            wrap="none",
            font=FONTS["receipt_body"],
            bg=THEME["card_bg"],
            fg=THEME["text_primary"],
            yscrollcommand=scrollbar.set,
            padx=15,
            pady=15,
            bd=0
        )
        self.text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.text_widget.yview)

        # Insert receipt text and make read-only
        self.text_widget.insert("1.0", self.receipt_text)
        self.text_widget.config(state="disabled")

        # Action Buttons
        btn_frame = tk.Frame(self, bg=THEME["main_bg"], padx=20, pady=12)
        btn_frame.pack(fill="x", side="bottom")

        create_button(
            btn_frame,
            text=" Save Receipt to File (.txt)",
            command=self._save_receipt,
            bg_color=THEME["success"],
            hover_color=THEME["success_hover"]
        ).pack(side="left")

        create_button(
            btn_frame,
            text="Close",
            command=self.destroy,
            bg_color=THEME["sidebar_hover"],
            hover_color=THEME["sidebar_bg"]
        ).pack(side="right")

    def _save_receipt(self):
        """Saves receipt text to reports directory or selected file path."""
        try:
            default_path = filedialog.asksaveasfilename(
                initialdir=str(REPORTS_DIR),
                initialfile="rental_receipt.txt",
                defaultextension=".txt",
                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
            )
            if default_path:
                with open(default_path, "w", encoding="utf-8") as f:
                    f.write(self.receipt_text)
                messagebox.showinfo("Receipt Saved", f"Receipt saved successfully to:\n{default_path}")
                logger.info(f"Receipt saved to {default_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save receipt: {str(e)}")
            logger.error(f"Failed to save receipt: {e}")
