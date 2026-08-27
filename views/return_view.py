"""
Return Car Module (Admin)
Processes vehicle check-in, automated late penalty fee calculation, deposit reconciliation, and fleet availability restoration.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
from typing import Optional, Dict, Any

from config import THEME, FONTS
from models.rental import Rental
from utils.helpers import format_currency, format_date_display, today_iso, generate_receipt_text
from views.styles import create_button, create_scrollable_treeview
from views.receipt_view import ReceiptModal

class ReturnView(tk.Frame):
    """Car return processing interface for Administrators."""

    def __init__(self, parent):
        super().__init__(parent, bg=THEME["main_bg"])
        self.selected_rental: Optional[Dict[str, Any]] = None
        self._build_ui()
        self.load_active_rentals()

    def _build_ui(self):
        # Header Banner
        header = tk.Frame(self, bg=THEME["card_bg"], padx=24, pady=16, highlightbackground=THEME["card_border"], highlightthickness=1)
        header.pack(fill="x", padx=16, pady=(16, 10))

        tk.Label(
            header,
            text="🔄 Vehicle Return & Settlement Check-in",
            font=FONTS["title_medium"],
            fg=THEME["text_primary"],
            bg=THEME["card_bg"]
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Check-in returned vehicles, calculate late return penalties, settle accounts, and restore car availability.",
            font=FONTS["small"],
            fg=THEME["text_secondary"],
            bg=THEME["card_bg"]
        ).pack(anchor="w", pady=(2, 0))

        # Main Split Content: Left = Active Rentals Table, Right = Settlement Form
        content = tk.Frame(self, bg=THEME["main_bg"])
        content.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # ----------------- Left Panel: Active Rentals List -----------------
        left_card = tk.Frame(
            content,
            bg=THEME["card_bg"],
            highlightbackground=THEME["card_border"],
            highlightthickness=1,
            padx=16,
            pady=16
        )
        left_card.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Search Bar
        search_bar = tk.Frame(left_card, bg=THEME["card_bg"])
        search_bar.pack(fill="x", pady=(0, 10))

        tk.Label(search_bar, text="Search Active Rentals:", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["card_bg"]).pack(side="left", padx=(0, 6))
        self.ent_search = ttk.Entry(search_bar, font=FONTS["body"])
        self.ent_search.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.ent_search.bind("<Return>", lambda e: self.load_active_rentals())

        create_button(
            search_bar,
            text="Search",
            command=self.load_active_rentals,
            bg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            font=FONTS["small_bold"],
            padx=10,
            pady=4
        ).pack(side="left", padx=2)

        create_button(
            search_bar,
            text="Refresh",
            command=self._reset_search,
            bg_color=THEME["sidebar_hover"],
            hover_color=THEME["sidebar_bg"],
            font=FONTS["small_bold"],
            padx=10,
            pady=4
        ).pack(side="left", padx=2)

        # Active Rentals Table
        columns = [
            ("id", "Rental #", 60),
            ("customer", "Customer Name", 120),
            ("cnic", "CNIC", 115),
            ("car", "Car Plate", 85),
            ("vehicle", "Make & Model", 120),
            ("start", "Start Date", 80),
            ("due", "Due Date", 80)
        ]
        self.tree, tree_container = create_scrollable_treeview(left_card, columns)
        tree_container.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_rental_select)

        # ----------------- Right Panel: Return Calculation & Check-in -----------------
        self.form_card = tk.Frame(
            content,
            bg=THEME["card_bg"],
            highlightbackground=THEME["card_border"],
            highlightthickness=1,
            padx=18,
            pady=16,
            width=360
        )
        self.form_card.pack(side="right", fill="y")
        self.form_card.pack_propagate(False)

        tk.Label(
            self.form_card,
            text="Return & Late Fee Settlement",
            font=FONTS["title_small"],
            fg=THEME["text_primary"],
            bg=THEME["card_bg"]
        ).pack(anchor="w", pady=(0, 10))

        # Selected Rental Details Box
        self.details_box = tk.Frame(self.form_card, bg=THEME["main_bg"], padx=12, pady=10, highlightbackground=THEME["card_border"], highlightthickness=1)
        self.details_box.pack(fill="x", pady=(0, 12))

        self.lbl_sel_info = tk.Label(
            self.details_box,
            text="No active rental selected.\nSelect a record from the table to proceed.",
            font=FONTS["small"],
            fg=THEME["text_muted"],
            bg=THEME["main_bg"],
            justify="left"
        )
        self.lbl_sel_info.pack(anchor="w")

        # Actual Return Date Input
        date_box = tk.Frame(self.form_card, bg=THEME["card_bg"])
        date_box.pack(fill="x", pady=(0, 12))

        tk.Label(date_box, text="Actual Return Date (YYYY-MM-DD) *", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["card_bg"]).pack(anchor="w")
        self.ent_actual_date = ttk.Entry(date_box, font=FONTS["body"])
        self.ent_actual_date.pack(fill="x", pady=(2, 4))
        self.ent_actual_date.insert(0, today_iso())
        self.ent_actual_date.bind("<KeyRelease>", lambda e: self._recalculate_settlement())

        # Calculations Summary Box
        self.calc_box = tk.Frame(self.form_card, bg=THEME["primary_light"], padx=12, pady=10, highlightbackground=THEME["primary"], highlightthickness=1)
        self.calc_box.pack(fill="x", pady=(0, 14))

        tk.Label(self.calc_box, text="SETTLEMENT SUMMARY", font=FONTS["small_bold"], fg=THEME["primary_hover"], bg=THEME["primary_light"]).pack(anchor="w", pady=(0, 4))

        self.lbl_orig_amount = tk.Label(self.calc_box, text="Original Rental: PKR 0.00", font=FONTS["small"], bg=THEME["primary_light"], fg=THEME["text_primary"])
        self.lbl_orig_amount.pack(anchor="w")

        self.lbl_late_days = tk.Label(self.calc_box, text="Overdue Days: 0 day(s)", font=FONTS["small"], bg=THEME["primary_light"], fg=THEME["text_primary"])
        self.lbl_late_days.pack(anchor="w")

        self.lbl_late_charges = tk.Label(self.calc_box, text="Late Penalty Fee: PKR 0.00", font=FONTS["small_bold"], bg=THEME["primary_light"], fg=THEME["danger"])
        self.lbl_late_charges.pack(anchor="w")

        self.lbl_final_total = tk.Label(self.calc_box, text="Final Amount: PKR 0.00", font=FONTS["title_small"], bg=THEME["primary_light"], fg=THEME["primary_hover"])
        self.lbl_final_total.pack(anchor="w", pady=(4, 0))

        # Process Return Button
        create_button(
            self.form_card,
            text="✓ Confirm & Process Return",
            command=self._handle_process_return,
            bg_color=THEME["success"],
            hover_color=THEME["success_hover"],
            font=FONTS["body_bold"]
        ).pack(fill="x", side="bottom", pady=(0, 4))

    def _reset_search(self):
        self.ent_search.delete(0, tk.END)
        self.load_active_rentals()

    def load_active_rentals(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        search = self.ent_search.get().strip()
        rentals = Rental.search_active_rentals(search_term=search)

        if not rentals:
            self.tree.insert("", "end", values=("", "No active rentals found.", "", "", "", "", ""))
            return

        for idx, r in enumerate(rentals):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert(
                "",
                "end",
                iid=str(r["id"]),
                values=(
                    f"#{r['id']}",
                    r.get("customer_name", "N/A"),
                    r.get("customer_cnic", "N/A"),
                    r.get("car_number", "N/A"),
                    f"{r.get('brand', '')} {r.get('model', '')}",
                    format_date_display(r["rental_date"]),
                    format_date_display(r["return_date"])
                ),
                tags=(tag,)
            )

    def _on_rental_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        try:
            rental_id = int(selected[0])
        except ValueError:
            return

        rental = Rental.get_rental_by_id(rental_id)
        if not rental:
            return

        self.selected_rental = rental
        self.lbl_sel_info.config(
            text=f"Rental ID   : #{rental['id']}\n"
                 f"Customer    : {rental['customer_name']}\n"
                 f"CNIC        : {rental['customer_cnic']}\n"
                 f"Car         : {rental['brand']} {rental['model']} ({rental['car_number']})\n"
                 f"Start Date  : {format_date_display(rental['rental_date'])}\n"
                 f"Due Date    : {format_date_display(rental['return_date'])}\n"
                 f"Daily Rate  : {format_currency(rental['daily_rate'])} / day",
            fg=THEME["text_primary"]
        )

        self._recalculate_settlement()

    def _recalculate_settlement(self):
        if not self.selected_rental:
            return None

        actual_str = self.ent_actual_date.get().strip()
        try:
            actual_dt = datetime.strptime(actual_str, "%Y-%m-%d").date()
        except ValueError:
            self.lbl_late_days.config(text="Overdue Days: Invalid Date Format")
            return None

        expected_dt = datetime.strptime(self.selected_rental["return_date"], "%Y-%m-%d").date()
        late_days = max(0, (actual_dt - expected_dt).days)
        daily_rate = float(self.selected_rental["daily_rate"])
        late_charges = late_days * daily_rate
        orig_amount = float(self.selected_rental["total_amount"])
        final_total = orig_amount + late_charges

        self.lbl_orig_amount.config(text=f"Original Rental: {format_currency(orig_amount)}")
        self.lbl_late_days.config(text=f"Overdue Days: {late_days} day(s)")
        self.lbl_late_charges.config(
            text=f"Late Penalty Fee: {format_currency(late_charges)}",
            fg=THEME["danger"] if late_charges > 0 else THEME["text_secondary"]
        )
        self.lbl_final_total.config(text=f"Final Amount: {format_currency(final_total)}")

        return {
            "actual_date": actual_str,
            "late_days": late_days,
            "late_charges": late_charges,
            "orig_amount": orig_amount,
            "final_total": final_total
        }

    def _handle_process_return(self):
        if not self.selected_rental:
            messagebox.showwarning("Selection Required", "Please select an active rental to process return.")
            return

        calc = self._recalculate_settlement()
        if not calc:
            messagebox.showerror("Error", "Please provide a valid actual return date in YYYY-MM-DD format.")
            return

        confirm_msg = (
            f"Confirm return check-in for Rental #{self.selected_rental['id']}?\n\n"
            f"• Vehicle: {self.selected_rental['brand']} {self.selected_rental['model']} ({self.selected_rental['car_number']})\n"
            f"• Customer: {self.selected_rental['customer_name']}\n"
            f"• Actual Return Date: {format_date_display(calc['actual_date'])}\n"
            f"• Overdue Days: {calc['late_days']} day(s)\n"
            f"• Late Penalty Fee: {format_currency(calc['late_charges'])}\n"
            f"• Final Adjusted Total: {format_currency(calc['final_total'])}\n\n"
            "This will mark the rental as Completed and return the vehicle to 'Available' status."
        )

        if not messagebox.askyesno("Confirm Vehicle Return", confirm_msg):
            return

        success, msg, result = Rental.process_return(
            rental_id=self.selected_rental["id"],
            actual_return_date=calc["actual_date"]
        )

        if success:
            messagebox.showinfo("Return Processed", "Vehicle returned and status updated to Available!")
            
            # Generate receipt
            receipt_text = generate_receipt_text(
                rental_id=result["rental_id"],
                customer_name=result["customer_name"],
                customer_cnic=result["customer_cnic"],
                customer_phone=result["customer_phone"],
                car_number=result["car_number"],
                car_brand=result["car_brand"],
                car_model=result["car_model"],
                rental_date=result["rental_date"],
                expected_return_date=result["expected_return_date"],
                rental_days=result["rental_days"],
                daily_rate=result["daily_rate"],
                rental_amount=result["original_rental_amount"],
                security_deposit=result["security_deposit"],
                total_amount=result["original_rental_amount"] + result["security_deposit"],
                actual_return_date=result["actual_return_date"],
                late_days=result["late_days"],
                late_charges=result["late_charges"],
                final_amount=result["final_total"]
            )

            self.selected_rental = None
            self.lbl_sel_info.config(text="No active rental selected.\nSelect a record from the table to proceed.", fg=THEME["text_muted"])
            self.load_active_rentals()

            # Show Return Settlement Receipt
            ReceiptModal(self, receipt_text, title="Vehicle Return Settlement Receipt")
        else:
            messagebox.showerror("Return Failed", msg)
