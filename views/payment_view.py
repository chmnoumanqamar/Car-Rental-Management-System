"""
Payment Management View (Admin)
Audit ledger of transactions, financial filtering, and revenue records.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from config import THEME, FONTS, PAYMENT_METHODS, PAYMENT_STATUSES
from models.payment import Payment
from utils.helpers import format_currency, format_date_display, export_to_csv
from views.styles import create_button, create_scrollable_treeview

class PaymentView(tk.Frame):
    """Payment ledger and transaction history for Administrators."""

    def __init__(self, parent):
        super().__init__(parent, bg=THEME["main_bg"])
        self._build_ui()
        self.load_payments()

    def _build_ui(self):
        # Header Banner
        header = tk.Frame(self, bg=THEME["card_bg"], padx=24, pady=16, highlightbackground=THEME["card_border"], highlightthickness=1)
        header.pack(fill="x", padx=16, pady=(16, 10))

        tk.Label(
            header,
            text="💳 Financial Ledger & Payment Transactions",
            font=FONTS["title_medium"],
            fg=THEME["text_primary"],
            bg=THEME["card_bg"]
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Comprehensive transaction records, receipts audit, and revenue tracking across all payment channels.",
            font=FONTS["small"],
            fg=THEME["text_secondary"],
            bg=THEME["card_bg"]
        ).pack(anchor="w", pady=(2, 0))

        # Main Table Card
        card = tk.Frame(
            self,
            bg=THEME["card_bg"],
            highlightbackground=THEME["card_border"],
            highlightthickness=1,
            padx=16,
            pady=16
        )
        card.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # Filters Bar
        filter_bar = tk.Frame(card, bg=THEME["card_bg"])
        filter_bar.pack(fill="x", pady=(0, 12))

        tk.Label(filter_bar, text="Search:", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["card_bg"]).pack(side="left", padx=(0, 6))
        self.ent_search = ttk.Entry(filter_bar, font=FONTS["body"], width=20)
        self.ent_search.pack(side="left", padx=(0, 8))
        self.ent_search.bind("<Return>", lambda e: self.load_payments())

        tk.Label(filter_bar, text="Method:", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["card_bg"]).pack(side="left", padx=(6, 4))
        self.combo_method = ttk.Combobox(filter_bar, values=["All"] + PAYMENT_METHODS, state="readonly", width=12, font=FONTS["small"])
        self.combo_method.set("All")
        self.combo_method.pack(side="left", padx=(0, 8))
        self.combo_method.bind("<<ComboboxSelected>>", lambda e: self.load_payments())

        tk.Label(filter_bar, text="Status:", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["card_bg"]).pack(side="left", padx=(6, 4))
        self.combo_status = ttk.Combobox(filter_bar, values=["All"] + PAYMENT_STATUSES, state="readonly", width=10, font=FONTS["small"])
        self.combo_status.set("All")
        self.combo_status.pack(side="left", padx=(0, 8))
        self.combo_status.bind("<<ComboboxSelected>>", lambda e: self.load_payments())

        create_button(
            filter_bar,
            text="Filter",
            command=self.load_payments,
            bg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            font=FONTS["small_bold"],
            padx=10,
            pady=4
        ).pack(side="left", padx=2)

        create_button(
            filter_bar,
            text="Reset",
            command=self._reset_filters,
            bg_color=THEME["sidebar_hover"],
            hover_color=THEME["sidebar_bg"],
            font=FONTS["small_bold"],
            padx=10,
            pady=4
        ).pack(side="left", padx=2)

        create_button(
            filter_bar,
            text="📥 Export to CSV",
            command=self._export_csv,
            bg_color=THEME["success"],
            hover_color=THEME["success_hover"],
            font=FONTS["small_bold"],
            padx=12,
            pady=4
        ).pack(side="right")

        # Table
        columns = [
            ("id", "Payment ID", 70),
            ("rental_id", "Rental #", 60),
            ("customer", "Customer Name", 130),
            ("cnic", "CNIC", 115),
            ("car", "Car Plate", 85),
            ("amount", "Amount Paid", 100),
            ("method", "Payment Method", 110),
            ("date", "Transaction Date", 95),
            ("status", "Status", 75)
        ]
        self.tree, tree_container = create_scrollable_treeview(card, columns)
        tree_container.pack(fill="both", expand=True)

    def _reset_filters(self):
        self.ent_search.delete(0, tk.END)
        self.combo_method.set("All")
        self.combo_status.set("All")
        self.load_payments()

    def load_payments(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        search = self.ent_search.get().strip()
        method = self.combo_method.get()
        status = self.combo_status.get()

        payments = Payment.get_all_payments(method_filter=method, status_filter=status, search_term=search)
        if not payments:
            self.tree.insert("", "end", values=("", "No payment records found.", "", "", "", "", "", "", ""))
            return

        for idx, p in enumerate(payments):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert(
                "",
                "end",
                iid=str(p["id"]),
                values=(
                    f"PAY-{p['id']:04d}",
                    f"#{p['rental_id']}",
                    p.get("customer_name", "N/A"),
                    p.get("customer_cnic", "N/A"),
                    p.get("car_number", "N/A"),
                    format_currency(p["amount"]),
                    p["payment_method"],
                    format_date_display(p["payment_date"]),
                    p["payment_status"]
                ),
                tags=(tag,)
            )

    def _export_csv(self):
        payments = Payment.get_all_payments(
            method_filter=self.combo_method.get(),
            status_filter=self.combo_status.get(),
            search_term=self.ent_search.get().strip()
        )
        if not payments:
            messagebox.showwarning("No Data", "No payment records available to export.")
            return

        headers = ["Payment ID", "Rental ID", "Customer Name", "Customer CNIC", "Car Plate", "Amount", "Method", "Date", "Status"]
        rows = [
            [
                f"PAY-{p['id']:04d}",
                p['rental_id'],
                p.get('customer_name', ''),
                p.get('customer_cnic', ''),
                p.get('car_number', ''),
                p['amount'],
                p['payment_method'],
                p['payment_date'],
                p['payment_status']
            ]
            for p in payments
        ]

        try:
            path = export_to_csv("payments_report", headers, rows)
            messagebox.showinfo("Export Successful", f"Payments exported successfully to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Failed to export CSV: {str(e)}")
