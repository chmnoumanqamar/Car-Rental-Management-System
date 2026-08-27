"""
Reports & Analytics Module (Admin)
Generates comprehensive visual reports, category revenue breakdowns, and 1-click CSV exports.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Any

from config import THEME, FONTS
from models.car import Car
from models.customer import Customer
from models.rental import Rental
from models.payment import Payment
from utils.helpers import format_currency, format_date_display, export_to_csv
from views.styles import create_button, StatCard, create_scrollable_treeview

class ReportsView(tk.Frame):
    """Reports, financial analytics, and CSV export center."""

    def __init__(self, parent):
        super().__init__(parent, bg=THEME["main_bg"])
        self._build_ui()
        self.load_analytics()

    def _build_ui(self):
        # Header Banner
        header = tk.Frame(self, bg=THEME["card_bg"], padx=24, pady=16, highlightbackground=THEME["card_border"], highlightthickness=1)
        header.pack(fill="x", padx=16, pady=(16, 10))

        tk.Label(
            header,
            text="📊 Analytics & Executive Management Reports",
            font=FONTS["title_medium"],
            fg=THEME["text_primary"],
            bg=THEME["card_bg"]
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Fleet utilization statistics, revenue performance, category analytics, and downloadable CSV audits.",
            font=FONTS["small"],
            fg=THEME["text_secondary"],
            bg=THEME["card_bg"]
        ).pack(anchor="w", pady=(2, 0))

        # Main Scrollable Container
        main_content = tk.Frame(self, bg=THEME["main_bg"])
        main_content.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # Export Buttons Bar
        export_bar = tk.Frame(main_content, bg=THEME["card_bg"], padx=16, pady=12, highlightbackground=THEME["card_border"], highlightthickness=1)
        export_bar.pack(fill="x", pady=(0, 12))

        tk.Label(export_bar, text="Quick CSV Exports:", font=FONTS["body_bold"], fg=THEME["text_primary"], bg=THEME["card_bg"]).pack(side="left", padx=(0, 10))

        create_button(export_bar, text="🚗 Cars CSV", command=self._export_cars_csv, bg_color=THEME["primary"], hover_color=THEME["primary_hover"], font=FONTS["small_bold"], padx=10, pady=4).pack(side="left", padx=4)
        create_button(export_bar, text="👥 Customers CSV", command=self._export_customers_csv, bg_color=THEME["purple"], hover_color=THEME["sidebar_hover"], font=FONTS["small_bold"], padx=10, pady=4).pack(side="left", padx=4)
        create_button(export_bar, text="📋 Rentals CSV", command=self._export_rentals_csv, bg_color=THEME["warning"], hover_color=THEME["warning_hover"], font=FONTS["small_bold"], padx=10, pady=4).pack(side="left", padx=4)
        create_button(export_bar, text="💳 Payments CSV", command=self._export_payments_csv, bg_color=THEME["success"], hover_color=THEME["success_hover"], font=FONTS["small_bold"], padx=10, pady=4).pack(side="left", padx=4)
        create_button(export_bar, text="💰 Revenue Breakdown CSV", command=self._export_revenue_csv, bg_color=THEME["sidebar_bg"], hover_color=THEME["sidebar_hover"], font=FONTS["small_bold"], padx=10, pady=4).pack(side="left", padx=4)

        # Revenue Metrics Cards
        metrics_row = tk.Frame(main_content, bg=THEME["main_bg"])
        metrics_row.pack(fill="x", pady=(0, 12))

        self.card_total_rev = StatCard(metrics_row, title="Total Revenue", value="PKR 0.00", accent_color=THEME["success"], icon_text="💰")
        self.card_total_rev.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.card_today_rev = StatCard(metrics_row, title="Today's Revenue", value="PKR 0.00", accent_color=THEME["primary"], icon_text="📈")
        self.card_today_rev.pack(side="left", fill="x", expand=True, padx=3)

        self.card_month_rev = StatCard(metrics_row, title="This Month", value="PKR 0.00", accent_color=THEME["purple"], icon_text="📅")
        self.card_month_rev.pack(side="left", fill="x", expand=True, padx=(6, 0))

        # Bottom Tables: Left = Category Breakdown, Right = Top Earning Vehicles
        tables_row = tk.Frame(main_content, bg=THEME["main_bg"])
        tables_row.pack(fill="both", expand=True)

        # Left Table: Revenue by Category
        cat_card = tk.Frame(tables_row, bg=THEME["card_bg"], highlightbackground=THEME["card_border"], highlightthickness=1, padx=14, pady=12)
        cat_card.pack(side="left", fill="both", expand=True, padx=(0, 6))

        tk.Label(cat_card, text="Revenue by Vehicle Category", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["card_bg"]).pack(anchor="w", pady=(0, 8))
        
        cat_cols = [("cat", "Category", 110), ("rentals", "Bookings", 60), ("rev", "Total Revenue", 110)]
        self.tree_cat, tree_cat_container = create_scrollable_treeview(cat_card, cat_cols)
        tree_cat_container.pack(fill="both", expand=True)

        # Right Table: Top Earning Cars
        car_card = tk.Frame(tables_row, bg=THEME["card_bg"], highlightbackground=THEME["card_border"], highlightthickness=1, padx=14, pady=12)
        car_card.pack(side="right", fill="both", expand=True, padx=(6, 0))

        tk.Label(car_card, text="Top Revenue Generating Cars", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["card_bg"]).pack(anchor="w", pady=(0, 8))

        car_cols = [("plate", "Plate No", 90), ("model", "Make & Model", 130), ("bookings", "Rentals", 55), ("rev", "Total Earned", 110)]
        self.tree_car, tree_car_container = create_scrollable_treeview(car_card, car_cols)
        tree_car_container.pack(fill="both", expand=True)

    def load_analytics(self):
        """Loads live revenue aggregations and population tables."""
        rev_stats = Payment.get_revenue_statistics()
        
        self.card_total_rev.update_value(format_currency(rev_stats["total_revenue"]))
        self.card_today_rev.update_value(format_currency(rev_stats["today_revenue"]))
        self.card_month_rev.update_value(format_currency(rev_stats["month_revenue"]))

        # Populate Category Tree
        for item in self.tree_cat.get_children():
            self.tree_cat.delete(item)

        for idx, row in enumerate(rev_stats["by_category"]):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree_cat.insert(
                "",
                "end",
                values=(row["category"], row["rental_count"], format_currency(row["revenue"])),
                tags=(tag,)
            )

        # Populate Car Tree
        for item in self.tree_car.get_children():
            self.tree_car.delete(item)

        for idx, row in enumerate(rev_stats["by_car"]):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree_car.insert(
                "",
                "end",
                values=(row["car_number"], f"{row['brand']} {row['model']}", row["rental_count"], format_currency(row["revenue"])),
                tags=(tag,)
            )

    # ---------------- CSV Exports ----------------
    def _export_cars_csv(self):
        cars = Car.get_all_cars()
        headers = ["ID", "Car Number", "Brand", "Model", "Year", "Color", "Category", "Daily Rate", "Status"]
        rows = [[c.id, c.car_number, c.brand, c.model, c.year, c.color, c.category, c.daily_rate, c.status] for c in cars]
        path = export_to_csv("cars_report", headers, rows)
        messagebox.showinfo("Export Successful", f"Cars report exported to:\n{path}")

    def _export_customers_csv(self):
        customers = Customer.get_all_customers()
        headers = ["ID", "Full Name", "CNIC", "Phone", "Email", "Address", "Username", "Registered At"]
        rows = [[c.id, c.full_name, c.cnic, c.phone, c.email, c.address, c.username, c.created_at] for c in customers]
        path = export_to_csv("customers_report", headers, rows)
        messagebox.showinfo("Export Successful", f"Customers report exported to:\n{path}")

    def _export_rentals_csv(self):
        rentals = Rental.get_all_rentals()
        headers = ["Rental ID", "Customer Name", "Customer CNIC", "Car Plate", "Make & Model", "Start Date", "Due Date", "Actual Return Date", "Days", "Daily Rate", "Total Rental Amount", "Security Deposit", "Status"]
        rows = [
            [
                r["id"],
                r.get("customer_name", ""),
                r.get("customer_cnic", ""),
                r.get("car_number", ""),
                f"{r.get('brand', '')} {r.get('model', '')}",
                r["rental_date"],
                r["return_date"],
                r.get("actual_return_date") or "",
                r["rental_days"],
                r["daily_rate"],
                r["total_amount"],
                r["security_deposit"],
                r["status"]
            ]
            for r in rentals
        ]
        path = export_to_csv("rentals_report", headers, rows)
        messagebox.showinfo("Export Successful", f"Rentals report exported to:\n{path}")

    def _export_payments_csv(self):
        payments = Payment.get_all_payments()
        headers = ["Payment ID", "Rental ID", "Customer Name", "Customer CNIC", "Car Plate", "Amount", "Method", "Date", "Status"]
        rows = [
            [
                f"PAY-{p['id']:04d}",
                p["rental_id"],
                p.get("customer_name", ""),
                p.get("customer_cnic", ""),
                p.get("car_number", ""),
                p["amount"],
                p["payment_method"],
                p["payment_date"],
                p["payment_status"]
            ]
            for p in payments
        ]
        path = export_to_csv("payments_report", headers, rows)
        messagebox.showinfo("Export Successful", f"Payments report exported to:\n{path}")

    def _export_revenue_csv(self):
        stats = Payment.get_revenue_statistics()
        headers = ["Vehicle Category", "Total Bookings", "Total Revenue (PKR)"]
        rows = [[r["category"], r["rental_count"], r["revenue"]] for r in stats["by_category"]]
        path = export_to_csv("revenue_report", headers, rows)
        messagebox.showinfo("Export Successful", f"Revenue report exported to:\n{path}")
