"""
Admin Master Dashboard
Integrates dark sidebar navigation with dynamic overview stat cards and sub-module switching.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional

from config import THEME, FONTS, APP_TITLE
from models.admin import Admin
from models.car import Car
from models.customer import Customer
from models.rental import Rental
from models.payment import Payment
from utils.helpers import format_currency, format_date_display
from views.styles import StatCard, create_button, create_scrollable_treeview, center_window
from views.cars_view import CarsView
from views.customers_view import CustomersView
from views.rental_view import AdminRentalsView
from views.return_view import ReturnView
from views.payment_view import PaymentView
from views.reports_view import ReportsView

class AdminProfileModal(tk.Toplevel):
    """Modal for updating Administrator Profile and Password."""

    def __init__(self, parent, admin: Admin, on_update_callback: Callable[[], None]):
        super().__init__(parent)
        self.admin = admin
        self.on_update_callback = on_update_callback
        self.title("Admin Profile Settings")
        self.configure(bg=THEME["main_bg"])
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        center_window(self, 440, 420)

    def _build_ui(self):
        hdr = tk.Frame(self, bg=THEME["sidebar_bg"], padx=20, pady=12)
        hdr.pack(fill="x")

        tk.Label(hdr, text="Administrator Account Settings", font=FONTS["title_small"], fg=THEME["sidebar_text"], bg=THEME["sidebar_bg"]).pack(anchor="w")
        tk.Label(hdr, text=f"Username: {self.admin.username}", font=FONTS["small"], fg=THEME["sidebar_muted"], bg=THEME["sidebar_bg"]).pack(anchor="w")

        form = tk.Frame(self, bg=THEME["main_bg"], padx=24, pady=16)
        form.pack(fill="both", expand=True)

        tk.Label(form, text="Full Name *", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["main_bg"]).pack(anchor="w")
        self.ent_name = ttk.Entry(form, font=FONTS["body"])
        self.ent_name.pack(fill="x", pady=(2, 10))
        self.ent_name.insert(0, self.admin.full_name)

        tk.Label(form, text="Email Address *", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["main_bg"]).pack(anchor="w")
        self.ent_email = ttk.Entry(form, font=FONTS["body"])
        self.ent_email.pack(fill="x", pady=(2, 10))
        self.ent_email.insert(0, self.admin.email)

        tk.Label(form, text="New Password (Leave blank to keep current)", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["main_bg"]).pack(anchor="w")
        self.ent_pwd = ttk.Entry(form, font=FONTS["body"], show="●")
        self.ent_pwd.pack(fill="x", pady=(2, 16))

        btn_box = tk.Frame(self, bg=THEME["main_bg"], padx=24, pady=12)
        btn_box.pack(fill="x", side="bottom")

        create_button(btn_box, text="Save Changes", command=self._save_profile, bg_color=THEME["success"], hover_color=THEME["success_hover"]).pack(side="left")
        create_button(btn_box, text="Cancel", command=self.destroy, bg_color=THEME["sidebar_hover"], hover_color=THEME["sidebar_bg"]).pack(side="right")

    def _save_profile(self):
        name = self.ent_name.get().strip()
        email = self.ent_email.get().strip()
        pwd = self.ent_pwd.get().strip()

        if not name or not email:
            messagebox.showwarning("Missing Fields", "Full name and email are required.")
            return

        if pwd and len(pwd) < 6:
            messagebox.showwarning("Validation Error", "Password must be at least 6 characters.")
            return

        success = Admin.update_profile(
            admin_id=self.admin.id,
            full_name=name,
            email=email,
            new_password=pwd if pwd else None
        )

        if success:
            self.admin.full_name = name
            self.admin.email = email
            messagebox.showinfo("Success", "Profile updated successfully.")
            self.on_update_callback()
            self.destroy()
        else:
            messagebox.showerror("Error", "Failed to update profile.")

class AdminDashboard(tk.Frame):
    """Main Administrator Control Center."""

    def __init__(self, parent, admin: Admin, on_logout: Callable[[], None]):
        super().__init__(parent, bg=THEME["main_bg"])
        self.parent = parent
        self.admin = admin
        self.on_logout = on_logout
        self.current_section = "dashboard"

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
        tk.Label(brand_frame, text="Admin Control Center", font=FONTS["small"], fg=THEME["primary_light"], bg=THEME["sidebar_bg"]).pack(anchor="w")

        # Admin Badge
        admin_info = tk.Frame(self.sidebar, bg=THEME["sidebar_hover"], padx=12, pady=10)
        admin_info.pack(fill="x", padx=12, pady=(0, 15))

        self.lbl_admin_name = tk.Label(admin_info, text=f"👤 {self.admin.full_name}", font=FONTS["small_bold"], fg=THEME["sidebar_text"], bg=THEME["sidebar_hover"])
        self.lbl_admin_name.pack(anchor="w")

        tk.Label(admin_info, text=f"@{self.admin.username}", font=FONTS["small"], fg=THEME["sidebar_muted"], bg=THEME["sidebar_hover"]).pack(anchor="w")

        # Navigation Menu Buttons
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "📊 Dashboard", self._show_overview),
            ("cars", "🚗 Cars Fleet", self._show_cars),
            ("customers", "👥 Customers", self._show_customers),
            ("rentals", "📋 All Rentals", self._show_rentals),
            ("returns", "🔄 Return Car", self._show_returns),
            ("payments", "💳 Payments", self._show_payments),
            ("reports", "📈 Reports & CSV", self._show_reports),
            ("profile", "⚙️ Profile Settings", self._open_profile_modal)
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
            text="🚪 Logout",
            command=self._confirm_logout,
            bg_color=THEME["danger"],
            hover_color=THEME["danger_hover"],
            font=FONTS["body_bold"]
        ).pack(fill="x")

        # ----------------- Right Main View Container -----------------
        self.main_container = tk.Frame(self, bg=THEME["main_bg"])
        self.main_container.pack(side="right", fill="both", expand=True)

    def _set_active_button(self, active_key: str):
        self.current_section = active_key
        for key, btn in self.nav_buttons.items():
            if key == active_key:
                btn.config(bg=THEME["sidebar_active"], fg="#FFFFFF")
            else:
                btn.config(bg=THEME["sidebar_bg"], fg=THEME["sidebar_text"])

    def _clear_main_container(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    def _confirm_logout(self):
        if messagebox.askyesno("Confirm Logout", "Are you sure you want to sign out of the Admin panel?"):
            self.on_logout()

    def _open_profile_modal(self):
        self._set_active_button("profile")
        AdminProfileModal(
            self,
            self.admin,
            on_update_callback=lambda: self.lbl_admin_name.config(text=f"👤 {self.admin.full_name}")
        )

    # ----------------- Sub-Views -----------------
    def _show_overview(self):
        self._set_active_button("dashboard")
        self._clear_main_container()

        # Overview View
        overview_frame = tk.Frame(self.main_container, bg=THEME["main_bg"])
        overview_frame.pack(fill="both", expand=True)

        # Header
        hdr = tk.Frame(overview_frame, bg=THEME["card_bg"], padx=24, pady=16, highlightbackground=THEME["card_border"], highlightthickness=1)
        hdr.pack(fill="x", padx=16, pady=(16, 12))

        title_row = tk.Frame(hdr, bg=THEME["card_bg"])
        title_row.pack(fill="x")

        tk.Label(title_row, text="📊 System Dashboard Overview", font=FONTS["title_medium"], fg=THEME["text_primary"], bg=THEME["card_bg"]).pack(side="left")
        create_button(title_row, text="🔄 Refresh Stats", command=self._show_overview, bg_color=THEME["primary"], hover_color=THEME["primary_hover"], font=FONTS["small_bold"], padx=10, pady=4).pack(side="right")

        tk.Label(hdr, text="Real-time operational indicators, fleet status, customer registrations, and revenue.", font=FONTS["small"], fg=THEME["text_secondary"], bg=THEME["card_bg"]).pack(anchor="w", pady=(2, 0))

        # Query dynamic statistics from SQLite
        car_stats = Car.get_car_statistics()
        customers = Customer.get_all_customers()
        rental_stats = Rental.get_rental_statistics()
        rev_stats = Payment.get_revenue_statistics()

        # 8 KPI Stat Cards in 2 Rows (4 cards per row)
        grid_cards = tk.Frame(overview_frame, bg=THEME["main_bg"])
        grid_cards.pack(fill="x", padx=16, pady=(0, 12))

        # Row 1
        r1 = tk.Frame(grid_cards, bg=THEME["main_bg"])
        r1.pack(fill="x", pady=(0, 8))
        StatCard(r1, title="Total Fleet", value=str(car_stats["Total"]), subtext="Registered vehicles", accent_color=THEME["primary"], icon_text="🚗").pack(side="left", fill="x", expand=True, padx=(0, 4))
        StatCard(r1, title="Available Cars", value=str(car_stats["Available"]), subtext="Ready for rent", accent_color=THEME["success"], icon_text="✓").pack(side="left", fill="x", expand=True, padx=4)
        StatCard(r1, title="Rented Out", value=str(car_stats["Rented"]), subtext="Active on road", accent_color=THEME["purple"], icon_text="🔑").pack(side="left", fill="x", expand=True, padx=4)
        StatCard(r1, title="In Maintenance", value=str(car_stats["Maintenance"]), subtext="Under servicing", accent_color=THEME["warning"], icon_text="🔧").pack(side="left", fill="x", expand=True, padx=(4, 0))

        # Row 2
        r2 = tk.Frame(grid_cards, bg=THEME["main_bg"])
        r2.pack(fill="x", pady=(0, 8))
        StatCard(r2, title="Total Customers", value=str(len(customers)), subtext="Verified accounts", accent_color=THEME["primary"], icon_text="👥").pack(side="left", fill="x", expand=True, padx=(0, 4))
        StatCard(r2, title="Active Rentals", value=str(rental_stats["Active"]), subtext="Ongoing bookings", accent_color=THEME["warning"], icon_text="⏳").pack(side="left", fill="x", expand=True, padx=4)
        StatCard(r2, title="Completed Rentals", value=str(rental_stats["Completed"]), subtext="Successfully returned", accent_color=THEME["success"], icon_text="🏁").pack(side="left", fill="x", expand=True, padx=4)
        StatCard(r2, title="Total Revenue", value=format_currency(rev_stats["total_revenue"]), subtext="All-time earnings", accent_color=THEME["success"], icon_text="💰").pack(side="left", fill="x", expand=True, padx=(4, 0))

        # Recent Activity Table (Last 6 Rentals)
        recent_card = tk.Frame(overview_frame, bg=THEME["card_bg"], highlightbackground=THEME["card_border"], highlightthickness=1, padx=16, pady=14)
        recent_card.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        tk.Label(recent_card, text="Recent Rental Agreements", font=FONTS["title_small"], fg=THEME["text_primary"], bg=THEME["card_bg"]).pack(anchor="w", pady=(0, 8))

        recent_cols = [
            ("id", "Rental #", 60),
            ("customer", "Customer Name", 130),
            ("car", "Car Plate", 90),
            ("vehicle", "Make & Model", 130),
            ("start", "Start Date", 85),
            ("due", "Due Date", 85),
            ("amount", "Rental Fee", 95),
            ("status", "Status", 80)
        ]
        recent_tree, tree_container = create_scrollable_treeview(recent_card, recent_cols)
        tree_container.pack(fill="both", expand=True)

        recent_rentals = Rental.get_all_rentals()[:6]
        for idx, r in enumerate(recent_rentals):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            recent_tree.insert(
                "",
                "end",
                values=(
                    f"#{r['id']}",
                    r.get("customer_name", "N/A"),
                    r.get("car_number", "N/A"),
                    f"{r.get('brand', '')} {r.get('model', '')}",
                    format_date_display(r["rental_date"]),
                    format_date_display(r["return_date"]),
                    format_currency(r["total_amount"]),
                    r["status"]
                ),
                tags=(tag,)
            )

    def _show_cars(self):
        self._set_active_button("cars")
        self._clear_main_container()
        view = CarsView(self.main_container)
        view.pack(fill="both", expand=True)

    def _show_customers(self):
        self._set_active_button("customers")
        self._clear_main_container()
        view = CustomersView(self.main_container)
        view.pack(fill="both", expand=True)

    def _show_rentals(self):
        self._set_active_button("rentals")
        self._clear_main_container()
        view = AdminRentalsView(self.main_container)
        view.pack(fill="both", expand=True)

    def _show_returns(self):
        self._set_active_button("returns")
        self._clear_main_container()
        view = ReturnView(self.main_container)
        view.pack(fill="both", expand=True)

    def _show_payments(self):
        self._set_active_button("payments")
        self._clear_main_container()
        view = PaymentView(self.main_container)
        view.pack(fill="both", expand=True)

    def _show_reports(self):
        self._set_active_button("reports")
        self._clear_main_container()
        view = ReportsView(self.main_container)
        view.pack(fill="both", expand=True)
