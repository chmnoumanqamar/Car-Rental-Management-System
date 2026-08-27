"""
Rental View & Booking Module
Provides interactive rental booking wizards, receipt generation, and rental history viewers.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, Callable

from config import THEME, FONTS, DEFAULT_SECURITY_DEPOSIT, PAYMENT_METHODS
from models.car import Car
from models.customer import Customer
from models.rental import Rental
from utils.validators import validate_rental_dates
from utils.helpers import format_currency, format_date_display, today_iso, generate_receipt_text
from views.styles import create_button, create_scrollable_treeview, center_window
from views.receipt_view import ReceiptModal

class BookingModal(tk.Toplevel):
    """Interactive Booking Wizard with dynamic automatic price calculation and validation."""

    def __init__(self, parent, car: Car, customer: Customer, on_booking_complete: Callable[[], None]):
        super().__init__(parent)
        self.car = car
        self.customer = customer
        self.on_booking_complete = on_booking_complete
        
        self.title(f"Book Rental - {car.brand} {car.model} ({car.car_number})")
        self.configure(bg=THEME["main_bg"])
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        center_window(self, 580, 680)
        self._calculate_pricing()

    def _build_ui(self):
        # Header Banner
        hdr = tk.Frame(self, bg=THEME["sidebar_bg"], padx=20, pady=14)
        hdr.pack(fill="x")

        tk.Label(
            hdr,
            text=f"🚘 Rental Booking Agreement",
            font=FONTS["title_small"],
            fg=THEME["sidebar_text"],
            bg=THEME["sidebar_bg"]
        ).pack(anchor="w")

        tk.Label(
            hdr,
            text=f"Customer: {self.customer.full_name} | Vehicle: {self.car.brand} {self.car.model} ({self.car.car_number})",
            font=FONTS["small"],
            fg=THEME["sidebar_muted"],
            bg=THEME["sidebar_bg"]
        ).pack(anchor="w")

        # Scrollable / Structured Content
        body = tk.Frame(self, bg=THEME["main_bg"], padx=24, pady=16)
        body.pack(fill="both", expand=True)

        # Vehicle Info Card
        v_card = tk.Frame(body, bg=THEME["card_bg"], highlightbackground=THEME["card_border"], highlightthickness=1, padx=16, pady=10)
        v_card.pack(fill="x", pady=(0, 12))

        tk.Label(v_card, text="VEHICLE SPECIFICATIONS", font=FONTS["small_bold"], fg=THEME["text_muted"], bg=THEME["card_bg"]).pack(anchor="w", pady=(0, 4))
        
        info_grid = tk.Frame(v_card, bg=THEME["card_bg"])
        info_grid.pack(fill="x")

        tk.Label(info_grid, text=f"Make & Model: {self.car.brand} {self.car.model} ({self.car.year})", font=FONTS["body_bold"], fg=THEME["text_primary"], bg=THEME["card_bg"]).grid(row=0, column=0, sticky="w", pady=2)
        tk.Label(info_grid, text=f"Category: {self.car.category} | Color: {self.car.color}", font=FONTS["body"], fg=THEME["text_secondary"], bg=THEME["card_bg"]).grid(row=1, column=0, sticky="w", pady=2)
        tk.Label(info_grid, text=f"Daily Rental Rate: {format_currency(self.car.daily_rate)} / day", font=FONTS["body_bold"], fg=THEME["primary"], bg=THEME["card_bg"]).grid(row=0, column=1, sticky="e", padx=(20, 0))
        info_grid.grid_columnconfigure(0, weight=1)

        # Date & Payment Inputs Card
        in_card = tk.Frame(body, bg=THEME["card_bg"], highlightbackground=THEME["card_border"], highlightthickness=1, padx=16, pady=12)
        in_card.pack(fill="x", pady=(0, 12))

        tk.Label(in_card, text="RENTAL DATES & PAYMENT", font=FONTS["small_bold"], fg=THEME["text_muted"], bg=THEME["card_bg"]).pack(anchor="w", pady=(0, 8))

        date_grid = tk.Frame(in_card, bg=THEME["card_bg"])
        date_grid.pack(fill="x")

        # Start Date
        tk.Label(date_grid, text="Start Date (YYYY-MM-DD) *", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["card_bg"]).grid(row=0, column=0, sticky="w")
        self.ent_start_date = ttk.Entry(date_grid, font=FONTS["body"])
        self.ent_start_date.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(2, 8))
        self.ent_start_date.insert(0, today_iso())
        self.ent_start_date.bind("<KeyRelease>", lambda e: self._calculate_pricing())

        # Expected Return Date
        tk.Label(date_grid, text="Expected Return Date (YYYY-MM-DD) *", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["card_bg"]).grid(row=0, column=1, sticky="w")
        self.ent_return_date = ttk.Entry(date_grid, font=FONTS["body"])
        self.ent_return_date.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(2, 8))
        tomorrow_str = (date.today() + timedelta(days=3)).strftime("%Y-%m-%d")
        self.ent_return_date.insert(0, tomorrow_str)
        self.ent_return_date.bind("<KeyRelease>", lambda e: self._calculate_pricing())

        # Payment Method
        tk.Label(date_grid, text="Payment Method *", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["card_bg"]).grid(row=2, column=0, sticky="w")
        self.combo_payment = ttk.Combobox(date_grid, values=PAYMENT_METHODS, state="readonly", font=FONTS["body"])
        self.combo_payment.grid(row=3, column=0, sticky="ew", padx=(0, 8), pady=(2, 4))
        self.combo_payment.set(PAYMENT_METHODS[0])

        date_grid.grid_columnconfigure(0, weight=1)
        date_grid.grid_columnconfigure(1, weight=1)

        # Financial Breakdown Card
        self.calc_card = tk.Frame(body, bg=THEME["primary_light"], highlightbackground=THEME["primary"], highlightthickness=1, padx=16, pady=12)
        self.calc_card.pack(fill="x", pady=(0, 10))

        tk.Label(self.calc_card, text="ESTIMATED COST BREAKDOWN", font=FONTS["small_bold"], fg=THEME["primary_hover"], bg=THEME["primary_light"]).pack(anchor="w", pady=(0, 6))

        self.lbl_days = tk.Label(self.calc_card, text="Rental Duration: 3 day(s)", font=FONTS["body"], bg=THEME["primary_light"], fg=THEME["text_primary"])
        self.lbl_days.pack(anchor="w")

        self.lbl_rental_charge = tk.Label(self.calc_card, text="Rental Amount: PKR 0.00", font=FONTS["body"], bg=THEME["primary_light"], fg=THEME["text_primary"])
        self.lbl_rental_charge.pack(anchor="w")

        self.lbl_deposit = tk.Label(self.calc_card, text=f"Refundable Security Deposit: {format_currency(DEFAULT_SECURITY_DEPOSIT)}", font=FONTS["body"], bg=THEME["primary_light"], fg=THEME["text_secondary"])
        self.lbl_deposit.pack(anchor="w")

        self.lbl_grand_total = tk.Label(self.calc_card, text="Grand Total Payable: PKR 0.00", font=FONTS["title_small"], bg=THEME["primary_light"], fg=THEME["primary_hover"])
        self.lbl_grand_total.pack(anchor="w", pady=(6, 0))

        # Bottom Buttons
        btn_bar = tk.Frame(self, bg=THEME["main_bg"], padx=24, pady=12)
        btn_bar.pack(fill="x", side="bottom")

        create_button(
            btn_bar,
            text=" Confirm & Book Rental",
            command=self._handle_confirm_booking,
            bg_color=THEME["success"],
            hover_color=THEME["success_hover"],
            font=FONTS["body_bold"]
        ).pack(side="left")

        create_button(
            btn_bar,
            text="Cancel",
            command=self.destroy,
            bg_color=THEME["sidebar_hover"],
            hover_color=THEME["sidebar_bg"]
        ).pack(side="right")

    def _calculate_pricing(self):
        start_str = self.ent_start_date.get().strip()
        return_str = self.ent_return_date.get().strip()

        valid, msg, days = validate_rental_dates(start_str, return_str, allow_past=False)
        if not valid:
            self.lbl_days.config(text=f"Rental Duration: Invalid ({msg})", fg=THEME["danger"])
            self.lbl_rental_charge.config(text="Rental Amount: --")
            self.lbl_grand_total.config(text="Grand Total Payable: --")
            return None

        rental_charge = days * self.car.daily_rate
        deposit = DEFAULT_SECURITY_DEPOSIT
        grand_total = rental_charge + deposit

        self.lbl_days.config(text=f"Rental Duration: {days} day(s)", fg=THEME["text_primary"])
        self.lbl_rental_charge.config(text=f"Rental Amount ({days}d x {format_currency(self.car.daily_rate)}): {format_currency(rental_charge)}")
        self.lbl_grand_total.config(text=f"Grand Total Payable: {format_currency(grand_total)}")

        return {
            "start_date": start_str,
            "return_date": return_str,
            "days": days,
            "daily_rate": self.car.daily_rate,
            "rental_amount": rental_charge,
            "security_deposit": deposit,
            "grand_total": grand_total,
            "payment_method": self.combo_payment.get()
        }

    def _handle_confirm_booking(self):
        pricing = self._calculate_pricing()
        if not pricing:
            messagebox.showerror("Invalid Booking Dates", "Please specify valid rental dates before proceeding.")
            return

        # Double check confirmation
        confirm = messagebox.askyesno(
            "Confirm Booking",
            f"Confirm rental booking for {self.car.brand} {self.car.model}?\n\n"
            f"• Duration: {pricing['days']} day(s) ({format_date_display(pricing['start_date'])} to {format_date_display(pricing['return_date'])})\n"
            f"• Rental Cost: {format_currency(pricing['rental_amount'])}\n"
            f"• Refundable Deposit: {format_currency(pricing['security_deposit'])}\n"
            f"• Grand Total: {format_currency(pricing['grand_total'])}\n"
            f"• Payment Method: {pricing['payment_method']}\n\n"
            "Proceed with booking?"
        )
        if not confirm:
            return

        success, msg, rental_id = Rental.create_rental(
            customer_id=self.customer.id,
            car_id=self.car.id,
            rental_date=pricing["start_date"],
            return_date=pricing["return_date"],
            rental_days=pricing["days"],
            daily_rate=pricing["daily_rate"],
            total_amount=pricing["rental_amount"],
            security_deposit=pricing["security_deposit"],
            payment_method=pricing["payment_method"]
        )

        if success:
            messagebox.showinfo("Rental Confirmed", f"Rental contract #{rental_id} successfully created!")
            
            # Generate and show receipt
            receipt_text = generate_receipt_text(
                rental_id=rental_id,
                customer_name=self.customer.full_name,
                customer_cnic=self.customer.cnic,
                customer_phone=self.customer.phone,
                car_number=self.car.car_number,
                car_brand=self.car.brand,
                car_model=self.car.model,
                rental_date=pricing["start_date"],
                expected_return_date=pricing["return_date"],
                rental_days=pricing["days"],
                daily_rate=pricing["daily_rate"],
                rental_amount=pricing["rental_amount"],
                security_deposit=pricing["security_deposit"],
                total_amount=pricing["grand_total"],
                payment_method=pricing["payment_method"],
                payment_status="Paid"
            )

            self.on_booking_complete()
            self.destroy()

            # Open Receipt Modal
            ReceiptModal(self.master, receipt_text)
        else:
            messagebox.showerror("Booking Failed", msg)

class AdminRentalsView(tk.Frame):
    """Admin view for monitoring all rental agreements and viewing invoices."""

    def __init__(self, parent):
        super().__init__(parent, bg=THEME["main_bg"])
        self._build_ui()
        self.load_rentals()

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=THEME["card_bg"], padx=24, pady=16, highlightbackground=THEME["card_border"], highlightthickness=1)
        hdr.pack(fill="x", padx=16, pady=(16, 10))

        tk.Label(hdr, text="📋 Rental Agreements Ledger", font=FONTS["title_medium"], fg=THEME["text_primary"], bg=THEME["card_bg"]).pack(anchor="w")
        tk.Label(hdr, text="Track active and historic rental contracts, vehicle assignments, and invoices.", font=FONTS["small"], fg=THEME["text_secondary"], bg=THEME["card_bg"]).pack(anchor="w", pady=(2, 0))

        card = tk.Frame(self, bg=THEME["card_bg"], highlightbackground=THEME["card_border"], highlightthickness=1, padx=16, pady=16)
        card.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # Filter Bar
        bar = tk.Frame(card, bg=THEME["card_bg"])
        bar.pack(fill="x", pady=(0, 12))

        tk.Label(bar, text="Search:", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["card_bg"]).pack(side="left", padx=(0, 6))
        self.ent_search = ttk.Entry(bar, font=FONTS["body"], width=22)
        self.ent_search.pack(side="left", padx=(0, 8))
        self.ent_search.bind("<Return>", lambda e: self.load_rentals())

        tk.Label(bar, text="Status:", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["card_bg"]).pack(side="left", padx=(6, 4))
        self.filter_status = ttk.Combobox(bar, values=["All", "Active", "Completed", "Cancelled"], state="readonly", width=12, font=FONTS["small"])
        self.filter_status.set("All")
        self.filter_status.pack(side="left", padx=(0, 8))
        self.filter_status.bind("<<ComboboxSelected>>", lambda e: self.load_rentals())

        create_button(bar, text="Filter", command=self.load_rentals, bg_color=THEME["primary"], hover_color=THEME["primary_hover"], font=FONTS["small_bold"], padx=10, pady=4).pack(side="left", padx=2)
        create_button(bar, text="Reset", command=self._reset, bg_color=THEME["sidebar_hover"], hover_color=THEME["sidebar_bg"], font=FONTS["small_bold"], padx=10, pady=4).pack(side="left", padx=2)

        create_button(
            bar,
            text=" View Receipt / Invoice",
            command=self._view_selected_receipt,
            bg_color=THEME["purple"],
            hover_color=THEME["sidebar_hover"],
            font=FONTS["small_bold"],
            padx=12,
            pady=4
        ).pack(side="right")

        # Table
        columns = [
            ("id", "Rental #", 60),
            ("customer", "Customer Name", 120),
            ("cnic", "CNIC", 115),
            ("car", "Car Plate", 90),
            ("vehicle", "Vehicle Make & Model", 130),
            ("rental_date", "Start Date", 85),
            ("return_date", "Due Date", 85),
            ("days", "Days", 45),
            ("total", "Rental Fee", 90),
            ("deposit", "Deposit", 75),
            ("status", "Status", 75)
        ]
        self.tree, tree_container = create_scrollable_treeview(card, columns)
        tree_container.pack(fill="both", expand=True)

    def _reset(self):
        self.ent_search.delete(0, tk.END)
        self.filter_status.set("All")
        self.load_rentals()

    def load_rentals(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        search = self.ent_search.get().strip()
        status = self.filter_status.get()

        rentals = Rental.get_all_rentals(status=status, search_term=search)
        if not rentals:
            self.tree.insert("", "end", values=("", "No rental records found.", "", "", "", "", "", "", "", "", ""))
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
                    format_date_display(r["return_date"]),
                    r["rental_days"],
                    format_currency(r["total_amount"]),
                    format_currency(r["security_deposit"]),
                    r["status"]
                ),
                tags=(tag,)
            )

    def _view_selected_receipt(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a rental record from the table.")
            return

        try:
            rental_id = int(selected[0])
        except ValueError:
            return

        r = Rental.get_rental_by_id(rental_id)
        if not r:
            return

        receipt_text = generate_receipt_text(
            rental_id=r["id"],
            customer_name=r["customer_name"],
            customer_cnic=r["customer_cnic"],
            customer_phone=r["customer_phone"],
            car_number=r["car_number"],
            car_brand=r["brand"],
            car_model=r["model"],
            rental_date=r["rental_date"],
            expected_return_date=r["return_date"],
            rental_days=r["rental_days"],
            daily_rate=r["daily_rate"],
            rental_amount=r["total_amount"],
            security_deposit=r["security_deposit"],
            total_amount=r["total_amount"] + r["security_deposit"],
            actual_return_date=r.get("actual_return_date")
        )
        ReceiptModal(self, receipt_text)
