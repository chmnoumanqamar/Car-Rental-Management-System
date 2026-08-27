"""
Customer Portal Dashboard
Empowers customers to browse available fleets, filter vehicles, book rentals, view receipts, and update profiles.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional, Dict, Any

from config import THEME, FONTS, CAR_CATEGORIES, DEFAULT_SECURITY_DEPOSIT
from models.customer import Customer
from models.car import Car
from models.rental import Rental
from models.payment import Payment
from utils.helpers import format_currency, format_date_display, generate_receipt_text
from utils.validators import validate_name, validate_phone, validate_email
from views.styles import StatCard, create_button, create_scrollable_treeview, center_window
from views.rental_view import BookingModal
from views.receipt_view import ReceiptModal

class CustomerProfileModal(tk.Toplevel):
    """Modal for customers to update their personal details and password."""

    def __init__(self, parent, customer: Customer, on_update_callback: Callable[[], None]):
        super().__init__(parent)
        self.customer = customer
        self.on_update_callback = on_update_callback
        self.title("My Profile Settings")
        self.configure(bg=THEME["main_bg"])
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        center_window(self, 480, 520)

    def _build_ui(self):
        hdr = tk.Frame(self, bg=THEME["sidebar_bg"], padx=20, pady=12)
        hdr.pack(fill="x")

        tk.Label(hdr, text="Manage Profile", font=FONTS["title_small"], fg=THEME["sidebar_text"], bg=THEME["sidebar_bg"]).pack(anchor="w")
        tk.Label(hdr, text=f"Username: {self.customer.username} | CNIC: {self.customer.cnic}", font=FONTS["small"], fg=THEME["sidebar_muted"], bg=THEME["sidebar_bg"]).pack(anchor="w")

        form = tk.Frame(self, bg=THEME["main_bg"], padx=24, pady=16)
        form.pack(fill="both", expand=True)

        tk.Label(form, text="Full Name *", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["main_bg"]).pack(anchor="w")
        self.ent_name = ttk.Entry(form, font=FONTS["body"])
        self.ent_name.pack(fill="x", pady=(2, 10))
        self.ent_name.insert(0, self.customer.full_name)

        tk.Label(form, text="Phone Number *", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["main_bg"]).pack(anchor="w")
        self.ent_phone = ttk.Entry(form, font=FONTS["body"])
        self.ent_phone.pack(fill="x", pady=(2, 10))
        self.ent_phone.insert(0, self.customer.phone)

        tk.Label(form, text="Email Address *", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["main_bg"]).pack(anchor="w")
        self.ent_email = ttk.Entry(form, font=FONTS["body"])
        self.ent_email.pack(fill="x", pady=(2, 10))
        self.ent_email.insert(0, self.customer.email)

        tk.Label(form, text="Home / Delivery Address", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["main_bg"]).pack(anchor="w")
        self.ent_address = ttk.Entry(form, font=FONTS["body"])
        self.ent_address.pack(fill="x", pady=(2, 10))
        self.ent_address.insert(0, self.customer.address)

        tk.Label(form, text="New Password (Leave blank to keep unchanged)", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["main_bg"]).pack(anchor="w")
        self.ent_pwd = ttk.Entry(form, font=FONTS["body"], show="●")
        self.ent_pwd.pack(fill="x", pady=(2, 16))

        btn_box = tk.Frame(self, bg=THEME["main_bg"], padx=24, pady=12)
        btn_box.pack(fill="x", side="bottom")

        create_button(btn_box, text="Save Changes", command=self._save_profile, bg_color=THEME["success"], hover_color=THEME["success_hover"]).pack(side="left")
        create_button(btn_box, text="Cancel", command=self.destroy, bg_color=THEME["sidebar_hover"], hover_color=THEME["sidebar_bg"]).pack(side="right")

    def _save_profile(self):
        name = self.ent_name.get().strip()
        phone = self.ent_phone.get().strip()
        email = self.ent_email.get().strip()
        address = self.ent_address.get().strip()
        pwd = self.ent_pwd.get().strip()

        valid, msg = validate_name(name)
        if not valid:
            messagebox.showerror("Validation Error", msg)
            return

        valid, msg = validate_phone(phone)
        if not valid:
            messagebox.showerror("Validation Error", msg)
            return

        valid, msg = validate_email(email)
        if not valid:
            messagebox.showerror("Validation Error", msg)
            return

        if pwd and len(pwd) < 6:
            messagebox.showerror("Validation Error", "Password must be at least 6 characters.")
            return

        success, err = Customer.update_customer(
            customer_id=self.customer.id,
            full_name=name,
            phone=phone,
            email=email,
            address=address,
            new_password=pwd if pwd else None
        )

        if success:
            self.customer.full_name = name
            self.customer.phone = phone
            self.customer.email = email
            self.customer.address = address
            messagebox.showinfo("Success", "Profile updated successfully.")
            self.on_update_callback()
            self.destroy()
        else:
            messagebox.showerror("Error", err)

class CustomerDashboard(tk.Frame):
    """Main Customer Rental Portal Window."""

    def __init__(self, parent, customer: Customer, on_logout: Callable[[], None]):
        super().__init__(parent, bg=THEME["main_bg"])
        self.parent = parent
        self.customer = customer
        self.on_logout = on_logout
        self.selected_browse_car_id: Optional[int] = None

        self._build_layout()
        self._show_overview()

    def _build_layout(self):
        # ----------------- Left Sidebar -----------------
        self.sidebar = tk.Frame(self, bg=THEME["sidebar_bg"], width=230)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Brand in Sidebar
        brand_frame = tk.Frame(self.sidebar, bg=THEME["sidebar_bg"], padx=18, pady=20)
        brand_frame.pack(fill="x")

        tk.Label(brand_frame, text="🚘 CAR RENTAL", font=FONTS["title_medium"], fg=THEME["sidebar_text"], bg=THEME["sidebar_bg"]).pack(anchor="w")
        tk.Label(brand_frame, text="Customer Self-Service Portal", font=FONTS["small"], fg=THEME["primary_light"], bg=THEME["sidebar_bg"]).pack(anchor="w")

        # Customer Badge
        cust_info = tk.Frame(self.sidebar, bg=THEME["sidebar_hover"], padx=12, pady=10)
        cust_info.pack(fill="x", padx=12, pady=(0, 15))

        self.lbl_cust_name = tk.Label(cust_info, text=f"👤 {self.customer.full_name}", font=FONTS["small_bold"], fg=THEME["sidebar_text"], bg=THEME["sidebar_hover"])
        self.lbl_cust_name.pack(anchor="w")

        tk.Label(cust_info, text=f"CNIC: {self.customer.cnic}", font=FONTS["small"], fg=THEME["sidebar_muted"], bg=THEME["sidebar_hover"]).pack(anchor="w")

        # Navigation Buttons
        self.nav_buttons = {}
        nav_items = [
            ("overview", "📊 Dashboard", self._show_overview),
            ("browse", "🚗 Browse & Rent Cars", self._show_browse_cars),
            ("my_rentals", "📋 My Rental History", self._show_my_rentals),
            ("payments", "💳 Payment Records", self._show_my_payments),
            ("profile", "⚙️ My Profile", self._open_profile_modal)
        ]

        nav_frame = tk.Frame(self.sidebar, bg=THEME["sidebar_bg"])
        nav_frame.pack(fill="x", padx=10)

        for key, text, cmd in nav_items:
            btn = tk.Button(
                nav_frame,
                text=text,
                font=FONTS["body_bold"],
                bg=THEME["sidebar_bg"],
                fg=THEME["sidebar_text"],
                activebackground=THEME["sidebar_hover"],
                activeforeground=THEME["sidebar_text"],
                bd=0,
                padx=14,
                pady=10,
                anchor="w",
                cursor="hand2",
                command=cmd
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons[key] = btn

        # Logout at bottom
        logout_frame = tk.Frame(self.sidebar, bg=THEME["sidebar_bg"], padx=10, pady=15)
        logout_frame.pack(fill="x", side="bottom")

        create_button(
            logout_frame,
            text="🚪 Sign Out",
            command=self._confirm_logout,
            bg_color=THEME["danger"],
            hover_color=THEME["danger_hover"],
            font=FONTS["body_bold"]
        ).pack(fill="x")

        # ----------------- Right Main View Container -----------------
        self.main_container = tk.Frame(self, bg=THEME["main_bg"])
        self.main_container.pack(side="right", fill="both", expand=True)

    def _set_active_button(self, active_key: str):
        for key, btn in self.nav_buttons.items():
            if key == active_key:
                btn.config(bg=THEME["sidebar_active"], fg="#FFFFFF")
            else:
                btn.config(bg=THEME["sidebar_bg"], fg=THEME["sidebar_text"])

    def _clear_main_container(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    def _confirm_logout(self):
        if messagebox.askyesno("Confirm Logout", "Are you sure you want to sign out?"):
            self.on_logout()

    def _open_profile_modal(self):
        self._set_active_button("profile")
        CustomerProfileModal(
            self,
            self.customer,
            on_update_callback=lambda: self.lbl_cust_name.config(text=f"👤 {self.customer.full_name}")
        )

    # ----------------- Sub-Views -----------------
    def _show_overview(self):
        self._set_active_button("overview")
        self._clear_main_container()

        frame = tk.Frame(self.main_container, bg=THEME["main_bg"])
        frame.pack(fill="both", expand=True)

        # Header
        hdr = tk.Frame(frame, bg=THEME["card_bg"], padx=24, pady=18, highlightbackground=THEME["card_border"], highlightthickness=1)
        hdr.pack(fill="x", padx=16, pady=(16, 12))

        tk.Label(
            hdr,
            text=f"Welcome back, {self.customer.full_name}!",
            font=FONTS["title_medium"],
            fg=THEME["text_primary"],
            bg=THEME["card_bg"]
        ).pack(anchor="w")

        tk.Label(
            hdr,
            text="Explore premium cars, view active bookings, download official receipts, or book your next trip.",
            font=FONTS["small"],
            fg=THEME["text_secondary"],
            bg=THEME["card_bg"]
        ).pack(anchor="w", pady=(2, 0))

        # Dynamic Metrics
        stats = Customer.get_customer_stats(self.customer.id)
        avail_cars = Car.get_car_statistics()["Available"]

        cards_row = tk.Frame(frame, bg=THEME["main_bg"])
        cards_row.pack(fill="x", padx=16, pady=(0, 12))

        StatCard(cards_row, title="Available Fleet", value=str(avail_cars), subtext="Ready for instant booking", accent_color=THEME["success"], icon_text="🚗").pack(side="left", fill="x", expand=True, padx=(0, 4))
        StatCard(cards_row, title="My Active Rentals", value=str(stats["active_rentals"]), subtext="Currently on hire", accent_color=THEME["warning"], icon_text="🔑").pack(side="left", fill="x", expand=True, padx=4)
        StatCard(cards_row, title="Total Bookings", value=str(stats["total_rentals"]), subtext="Lifetime rentals", accent_color=THEME["primary"], icon_text="📋").pack(side="left", fill="x", expand=True, padx=4)
        StatCard(cards_row, title="Total Amount Paid", value=format_currency(stats["total_spent"]), subtext="Settled invoices", accent_color=THEME["purple"], icon_text="💳").pack(side="left", fill="x", expand=True, padx=(4, 0))

        # Quick Call to Action Card
        cta_card = tk.Frame(frame, bg=THEME["card_bg"], highlightbackground=THEME["card_border"], highlightthickness=1, padx=20, pady=16)
        cta_card.pack(fill="x", padx=16, pady=(0, 12))

        cta_left = tk.Frame(cta_card, bg=THEME["card_bg"])
        cta_left.pack(side="left")

        tk.Label(cta_left, text="Ready for your next journey?", font=FONTS["title_small"], fg=THEME["text_primary"], bg=THEME["card_bg"]).pack(anchor="w")
        tk.Label(cta_left, text="Browse our clean, fully serviced, and luxury vehicle collection today.", font=FONTS["small"], fg=THEME["text_secondary"], bg=THEME["card_bg"]).pack(anchor="w", pady=(2, 0))

        create_button(
            cta_card,
            text="🚀 Browse Fleet & Rent Now",
            command=self._show_browse_cars,
            bg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            font=FONTS["body_bold"],
            padx=16,
            pady=10
        ).pack(side="right")

        # Active / Recent Rentals table for this customer
        rec_card = tk.Frame(frame, bg=THEME["card_bg"], highlightbackground=THEME["card_border"], highlightthickness=1, padx=16, pady=14)
        rec_card.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        tk.Label(rec_card, text="Your Recent Bookings", font=FONTS["title_small"], fg=THEME["text_primary"], bg=THEME["card_bg"]).pack(anchor="w", pady=(0, 8))

        cols = [("id", "Rental #", 60), ("car", "Car Plate", 90), ("vehicle", "Make & Model", 140), ("start", "Start Date", 85), ("due", "Due Date", 85), ("amount", "Total Paid", 95), ("status", "Status", 80)]
        tree, tree_container = create_scrollable_treeview(rec_card, cols)
        tree_container.pack(fill="both", expand=True)

        my_rentals = Rental.get_customer_rentals(self.customer.id)[:5]
        for idx, r in enumerate(my_rentals):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            tree.insert(
                "",
                "end",
                values=(
                    f"#{r['id']}",
                    r["car_number"],
                    f"{r['brand']} {r['model']}",
                    format_date_display(r["rental_date"]),
                    format_date_display(r["return_date"]),
                    format_currency(r["total_amount"]),
                    r["status"]
                ),
                tags=(tag,)
            )

    # ----------------- Browse Cars View -----------------
    def _show_browse_cars(self):
        self._set_active_button("browse")
        self._clear_main_container()

        frame = tk.Frame(self.main_container, bg=THEME["main_bg"])
        frame.pack(fill="both", expand=True)

        # Header
        hdr = tk.Frame(frame, bg=THEME["card_bg"], padx=24, pady=16, highlightbackground=THEME["card_border"], highlightthickness=1)
        hdr.pack(fill="x", padx=16, pady=(16, 10))

        tk.Label(hdr, text="🚗 Available Vehicles for Hire", font=FONTS["title_medium"], fg=THEME["text_primary"], bg=THEME["card_bg"]).pack(anchor="w")
        tk.Label(hdr, text="Select an available car and click 'Rent Selected Vehicle' to customize dates and reserve immediately.", font=FONTS["small"], fg=THEME["text_secondary"], bg=THEME["card_bg"]).pack(anchor="w", pady=(2, 0))

        card = tk.Frame(frame, bg=THEME["card_bg"], highlightbackground=THEME["card_border"], highlightthickness=1, padx=16, pady=16)
        card.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # Filter Bar
        f_bar = tk.Frame(card, bg=THEME["card_bg"])
        f_bar.pack(fill="x", pady=(0, 12))

        tk.Label(f_bar, text="Search Make/Model:", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["card_bg"]).pack(side="left", padx=(0, 6))
        self.browse_search = ttk.Entry(f_bar, font=FONTS["body"], width=16)
        self.browse_search.pack(side="left", padx=(0, 8))
        self.browse_search.bind("<Return>", lambda e: self._load_browse_cars())

        tk.Label(f_bar, text="Category:", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["card_bg"]).pack(side="left", padx=(6, 4))
        self.browse_category = ttk.Combobox(f_bar, values=["All"] + CAR_CATEGORIES, state="readonly", width=12, font=FONTS["small"])
        self.browse_category.set("All")
        self.browse_category.pack(side="left", padx=(0, 8))
        self.browse_category.bind("<<ComboboxSelected>>", lambda e: self._load_browse_cars())

        tk.Label(f_bar, text="Max Daily Price (PKR):", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["card_bg"]).pack(side="left", padx=(6, 4))
        self.browse_max_price = ttk.Entry(f_bar, font=FONTS["body"], width=10)
        self.browse_max_price.pack(side="left", padx=(0, 8))
        self.browse_max_price.bind("<Return>", lambda e: self._load_browse_cars())

        create_button(f_bar, text="Apply Filter", command=self._load_browse_cars, bg_color=THEME["primary"], hover_color=THEME["primary_hover"], font=FONTS["small_bold"], padx=10, pady=4).pack(side="left", padx=2)
        create_button(f_bar, text="Reset", command=self._reset_browse_filters, bg_color=THEME["sidebar_hover"], hover_color=THEME["sidebar_bg"], font=FONTS["small_bold"], padx=10, pady=4).pack(side="left", padx=2)

        create_button(
            f_bar,
            text="🔑 Rent Selected Vehicle",
            command=self._open_booking_wizard,
            bg_color=THEME["success"],
            hover_color=THEME["success_hover"],
            font=FONTS["body_bold"],
            padx=14,
            pady=6
        ).pack(side="right")

        # Table
        cols = [
            ("id", "Car ID", 50),
            ("number", "Car Plate", 100),
            ("brand", "Make / Brand", 100),
            ("model", "Model", 130),
            ("year", "Year", 60),
            ("color", "Color", 90),
            ("category", "Category", 95),
            ("rate", "Daily Rate (PKR)", 110),
            ("status", "Availability", 90)
        ]
        self.browse_tree, tree_container = create_scrollable_treeview(card, cols)
        tree_container.pack(fill="both", expand=True)

        self.browse_tree.bind("<<TreeviewSelect>>", self._on_browse_select)
        self._load_browse_cars()

    def _reset_browse_filters(self):
        self.browse_search.delete(0, tk.END)
        self.browse_category.set("All")
        self.browse_max_price.delete(0, tk.END)
        self._load_browse_cars()

    def _load_browse_cars(self):
        for item in self.browse_tree.get_children():
            self.browse_tree.delete(item)

        search = self.browse_search.get().strip()
        cat = self.browse_category.get()
        price_str = self.browse_max_price.get().strip()
        max_p = None
        if price_str:
            try:
                max_p = float(price_str)
            except ValueError:
                pass

        available_cars = Car.get_available_cars(
            category=cat,
            max_price=max_p,
            search_term=search
        )

        if not available_cars:
            self.browse_tree.insert("", "end", values=("", "", "No available cars matching criteria.", "", "", "", "", "", ""))
            return

        for idx, c in enumerate(available_cars):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.browse_tree.insert(
                "",
                "end",
                iid=str(c.id),
                values=(
                    c.id,
                    c.car_number,
                    c.brand,
                    c.model,
                    c.year,
                    c.color,
                    c.category,
                    format_currency(c.daily_rate),
                    c.status
                ),
                tags=(tag,)
            )

    def _on_browse_select(self, event):
        selected = self.browse_tree.selection()
        if selected:
            try:
                self.selected_browse_car_id = int(selected[0])
            except ValueError:
                self.selected_browse_car_id = None

    def _open_booking_wizard(self):
        if not self.selected_browse_car_id:
            messagebox.showwarning("Selection Required", "Please select an available vehicle from the table to rent.")
            return

        car = Car.get_car_by_id(self.selected_browse_car_id)
        if not car or car.status != "Available":
            messagebox.showerror("Unavailable", "This vehicle is currently not available.")
            self._load_browse_cars()
            return

        BookingModal(
            parent=self,
            car=car,
            customer=self.customer,
            on_booking_complete=self._load_browse_cars
        )

    # ----------------- My Rentals View -----------------
    def _show_my_rentals(self):
        self._set_active_button("my_rentals")
        self._clear_main_container()

        frame = tk.Frame(self.main_container, bg=THEME["main_bg"])
        frame.pack(fill="both", expand=True)

        hdr = tk.Frame(frame, bg=THEME["card_bg"], padx=24, pady=16, highlightbackground=THEME["card_border"], highlightthickness=1)
        hdr.pack(fill="x", padx=16, pady=(16, 10))

        tk.Label(hdr, text="📋 My Rental History & Invoices", font=FONTS["title_medium"], fg=THEME["text_primary"], bg=THEME["card_bg"]).pack(anchor="w")
        tk.Label(hdr, text="Review your ongoing car hires, completed agreements, and generate receipts.", font=FONTS["small"], fg=THEME["text_secondary"], bg=THEME["card_bg"]).pack(anchor="w", pady=(2, 0))

        card = tk.Frame(frame, bg=THEME["card_bg"], highlightbackground=THEME["card_border"], highlightthickness=1, padx=16, pady=16)
        card.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        bar = tk.Frame(card, bg=THEME["card_bg"])
        bar.pack(fill="x", pady=(0, 12))

        create_button(bar, text="🔄 Refresh History", command=lambda: self._populate_my_rentals(tree), bg_color=THEME["primary"], hover_color=THEME["primary_hover"], font=FONTS["small_bold"], padx=10, pady=4).pack(side="left")
        
        create_button(
            bar,
            text="📄 View / Save Receipt",
            command=lambda: self._view_my_receipt(tree),
            bg_color=THEME["purple"],
            hover_color=THEME["sidebar_hover"],
            font=FONTS["small_bold"],
            padx=12,
            pady=4
        ).pack(side="right")

        cols = [
            ("id", "Rental #", 60),
            ("car", "Plate No", 90),
            ("model", "Vehicle Details", 140),
            ("category", "Category", 80),
            ("start", "Start Date", 85),
            ("due", "Due Date", 85),
            ("return_act", "Actual Return", 85),
            ("days", "Days", 45),
            ("total", "Rental Fee", 90),
            ("status", "Status", 80)
        ]
        tree, tree_container = create_scrollable_treeview(card, cols)
        tree_container.pack(fill="both", expand=True)

        self._populate_my_rentals(tree)

    def _populate_my_rentals(self, tree: ttk.Treeview):
        for item in tree.get_children():
            tree.delete(item)

        rentals = Rental.get_customer_rentals(self.customer.id)
        if not rentals:
            tree.insert("", "end", values=("", "No rental history found.", "", "", "", "", "", "", "", ""))
            return

        for idx, r in enumerate(rentals):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            tree.insert(
                "",
                "end",
                iid=str(r["id"]),
                values=(
                    f"#{r['id']}",
                    r["car_number"],
                    f"{r['brand']} {r['model']}",
                    r.get("category", "N/A"),
                    format_date_display(r["rental_date"]),
                    format_date_display(r["return_date"]),
                    format_date_display(r["actual_return_date"]) if r["actual_return_date"] else "Active",
                    r["rental_days"],
                    format_currency(r["total_amount"]),
                    r["status"]
                ),
                tags=(tag,)
            )

    def _view_my_receipt(self, tree: ttk.Treeview):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a rental record to view receipt.")
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
            customer_name=self.customer.full_name,
            customer_cnic=self.customer.cnic,
            customer_phone=self.customer.phone,
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

    # ----------------- My Payments View -----------------
    def _show_my_payments(self):
        self._set_active_button("payments")
        self._clear_main_container()

        frame = tk.Frame(self.main_container, bg=THEME["main_bg"])
        frame.pack(fill="both", expand=True)

        hdr = tk.Frame(frame, bg=THEME["card_bg"], padx=24, pady=16, highlightbackground=THEME["card_border"], highlightthickness=1)
        hdr.pack(fill="x", padx=16, pady=(16, 10))

        tk.Label(hdr, text="💳 My Payment Statements", font=FONTS["title_medium"], fg=THEME["text_primary"], bg=THEME["card_bg"]).pack(anchor="w")
        tk.Label(hdr, text="List of all payment receipts recorded against your car rental contracts.", font=FONTS["small"], fg=THEME["text_secondary"], bg=THEME["card_bg"]).pack(anchor="w", pady=(2, 0))

        card = tk.Frame(frame, bg=THEME["card_bg"], highlightbackground=THEME["card_border"], highlightthickness=1, padx=16, pady=16)
        card.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        cols = [
            ("id", "Payment ID", 70),
            ("rental_id", "Rental #", 60),
            ("vehicle", "Vehicle", 140),
            ("amount", "Amount Paid", 100),
            ("method", "Payment Method", 110),
            ("date", "Transaction Date", 95),
            ("status", "Status", 75)
        ]
        tree, tree_container = create_scrollable_treeview(card, cols)
        tree_container.pack(fill="both", expand=True)

        payments = Payment.get_customer_payments(self.customer.id)
        if not payments:
            tree.insert("", "end", values=("", "No payment records found.", "", "", "", "", ""))
        else:
            for idx, p in enumerate(payments):
                tag = "evenrow" if idx % 2 == 0 else "oddrow"
                tree.insert(
                    "",
                    "end",
                    values=(
                        f"PAY-{p['id']:04d}",
                        f"#{p['rental_id']}",
                        f"{p.get('brand', '')} {p.get('model', '')} ({p.get('car_number', '')})",
                        format_currency(p["amount"]),
                        p["payment_method"],
                        format_date_display(p["payment_date"]),
                        p["payment_status"]
                    ),
                    tags=(tag,)
                )
