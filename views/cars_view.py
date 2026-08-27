"""
Car Management View (Admin)
Handles vehicle inventory listing, search, filtering, and CRUD operations.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from config import THEME, FONTS, CAR_CATEGORIES, CAR_STATUSES
from models.car import Car
from utils.validators import validate_car_number, validate_year, validate_daily_rate
from utils.helpers import format_currency
from views.styles import create_button, create_scrollable_treeview

class CarsView(tk.Frame):
    """Car inventory management interface for Administrators."""

    def __init__(self, parent):
        super().__init__(parent, bg=THEME["main_bg"])
        self.selected_car_id: Optional[int] = None
        self._build_ui()
        self.load_cars()

    def _build_ui(self):
        # Header Banner
        header = tk.Frame(self, bg=THEME["card_bg"], padx=24, pady=16, highlightbackground=THEME["card_border"], highlightthickness=1)
        header.pack(fill="x", padx=16, pady=(16, 10))

        tk.Label(
            header,
            text="🚗 Vehicle Fleet Management",
            font=FONTS["title_medium"],
            fg=THEME["text_primary"],
            bg=THEME["card_bg"]
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Add, modify, monitor, or decommission vehicles in your rental inventory.",
            font=FONTS["small"],
            fg=THEME["text_secondary"],
            bg=THEME["card_bg"]
        ).pack(anchor="w", pady=(2, 0))

        # Main Split Content: Left = Form, Right = Table
        content = tk.Frame(self, bg=THEME["main_bg"])
        content.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # ----------------- Left Panel: Form -----------------
        form_card = tk.Frame(
            content,
            bg=THEME["card_bg"],
            highlightbackground=THEME["card_border"],
            highlightthickness=1,
            padx=18,
            pady=16,
            width=320
        )
        form_card.pack(side="left", fill="y", padx=(0, 10))
        form_card.pack_propagate(False)

        tk.Label(
            form_card,
            text="Vehicle Details",
            font=FONTS["title_small"],
            fg=THEME["text_primary"],
            bg=THEME["card_bg"]
        ).pack(anchor="w", pady=(0, 12))

        # Form Fields
        fields_frame = tk.Frame(form_card, bg=THEME["card_bg"])
        fields_frame.pack(fill="x", expand=False)

        # 1. Car Number
        tk.Label(fields_frame, text="Car Plate Number *", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["card_bg"]).pack(anchor="w")
        self.ent_number = ttk.Entry(fields_frame, font=FONTS["body"])
        self.ent_number.pack(fill="x", pady=(2, 8))

        # 2. Brand / Make
        tk.Label(fields_frame, text="Brand / Make *", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["card_bg"]).pack(anchor="w")
        self.ent_brand = ttk.Entry(fields_frame, font=FONTS["body"])
        self.ent_brand.pack(fill="x", pady=(2, 8))

        # 3. Model
        tk.Label(fields_frame, text="Model *", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["card_bg"]).pack(anchor="w")
        self.ent_model = ttk.Entry(fields_frame, font=FONTS["body"])
        self.ent_model.pack(fill="x", pady=(2, 8))

        # 4. Year & Color (2-columns)
        yc_frame = tk.Frame(fields_frame, bg=THEME["card_bg"])
        yc_frame.pack(fill="x", pady=(0, 8))
        
        tk.Label(yc_frame, text="Year *", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["card_bg"]).grid(row=0, column=0, sticky="w")
        self.ent_year = ttk.Entry(yc_frame, font=FONTS["body"], width=10)
        self.ent_year.grid(row=1, column=0, sticky="ew", padx=(0, 4))

        tk.Label(yc_frame, text="Color *", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["card_bg"]).grid(row=0, column=1, sticky="w")
        self.ent_color = ttk.Entry(yc_frame, font=FONTS["body"], width=14)
        self.ent_color.grid(row=1, column=1, sticky="ew", padx=(4, 0))
        yc_frame.grid_columnconfigure(0, weight=1)
        yc_frame.grid_columnconfigure(1, weight=1)

        # 5. Category (Combobox)
        tk.Label(fields_frame, text="Category *", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["card_bg"]).pack(anchor="w")
        self.combo_category = ttk.Combobox(fields_frame, values=CAR_CATEGORIES, state="readonly", font=FONTS["body"])
        self.combo_category.pack(fill="x", pady=(2, 8))
        self.combo_category.set(CAR_CATEGORIES[0])

        # 6. Daily Rate
        tk.Label(fields_frame, text="Daily Rental Rate (PKR) *", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["card_bg"]).pack(anchor="w")
        self.ent_rate = ttk.Entry(fields_frame, font=FONTS["body"])
        self.ent_rate.pack(fill="x", pady=(2, 8))

        # 7. Status (Combobox)
        tk.Label(fields_frame, text="Current Status *", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["card_bg"]).pack(anchor="w")
        self.combo_status = ttk.Combobox(fields_frame, values=CAR_STATUSES, state="readonly", font=FONTS["body"])
        self.combo_status.pack(fill="x", pady=(2, 14))
        self.combo_status.set(CAR_STATUSES[0])

        # Action Buttons
        btn_grid = tk.Frame(form_card, bg=THEME["card_bg"])
        btn_grid.pack(fill="x", side="bottom")

        self.btn_add = create_button(
            btn_grid,
            text=" Add Car",
            command=self._handle_add_car,
            bg_color=THEME["success"],
            hover_color=THEME["success_hover"],
            font=FONTS["small_bold"]
        )
        self.btn_add.grid(row=0, column=0, sticky="ew", padx=2, pady=2)

        self.btn_update = create_button(
            btn_grid,
            text=" Update",
            command=self._handle_update_car,
            bg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            font=FONTS["small_bold"]
        )
        self.btn_update.grid(row=0, column=1, sticky="ew", padx=2, pady=2)

        self.btn_delete = create_button(
            btn_grid,
            text=" Delete",
            command=self._handle_delete_car,
            bg_color=THEME["danger"],
            hover_color=THEME["danger_hover"],
            font=FONTS["small_bold"]
        )
        self.btn_delete.grid(row=1, column=0, sticky="ew", padx=2, pady=2)

        self.btn_clear = create_button(
            btn_grid,
            text=" Clear Form",
            command=self._clear_form,
            bg_color=THEME["card_border"],
            fg_color=THEME["text_primary"],
            hover_color=THEME["main_bg"],
            font=FONTS["small_bold"]
        )
        self.btn_clear.grid(row=1, column=1, sticky="ew", padx=2, pady=2)

        btn_grid.grid_columnconfigure(0, weight=1)
        btn_grid.grid_columnconfigure(1, weight=1)

        # ----------------- Right Panel: Search & Table -----------------
        table_card = tk.Frame(
            content,
            bg=THEME["card_bg"],
            highlightbackground=THEME["card_border"],
            highlightthickness=1,
            padx=16,
            pady=16
        )
        table_card.pack(side="right", fill="both", expand=True)

        # Search / Filter Bar
        filter_bar = tk.Frame(table_card, bg=THEME["card_bg"])
        filter_bar.pack(fill="x", pady=(0, 12))

        tk.Label(filter_bar, text="Search:", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["card_bg"]).pack(side="left", padx=(0, 6))
        self.ent_search = ttk.Entry(filter_bar, font=FONTS["body"], width=20)
        self.ent_search.pack(side="left", padx=(0, 8))
        self.ent_search.bind("<Return>", lambda e: self.load_cars())

        tk.Label(filter_bar, text="Category:", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["card_bg"]).pack(side="left", padx=(6, 4))
        self.filter_cat = ttk.Combobox(filter_bar, values=["All"] + CAR_CATEGORIES, state="readonly", width=12, font=FONTS["small"])
        self.filter_cat.set("All")
        self.filter_cat.pack(side="left", padx=(0, 8))
        self.filter_cat.bind("<<ComboboxSelected>>", lambda e: self.load_cars())

        tk.Label(filter_bar, text="Status:", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["card_bg"]).pack(side="left", padx=(6, 4))
        self.filter_stat = ttk.Combobox(filter_bar, values=["All"] + CAR_STATUSES, state="readonly", width=12, font=FONTS["small"])
        self.filter_stat.set("All")
        self.filter_stat.pack(side="left", padx=(0, 8))
        self.filter_stat.bind("<<ComboboxSelected>>", lambda e: self.load_cars())

        create_button(
            filter_bar,
            text="Search",
            command=self.load_cars,
            bg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            font=FONTS["small_bold"],
            padx=10,
            pady=4
        ).pack(side="left", padx=4)

        create_button(
            filter_bar,
            text="Reset",
            command=self._reset_filters,
            bg_color=THEME["sidebar_hover"],
            hover_color=THEME["sidebar_bg"],
            font=FONTS["small_bold"],
            padx=10,
            pady=4
        ).pack(side="left", padx=4)

        # Treeview Table
        columns = [
            ("id", "ID", 45),
            ("car_number", "Car Number", 100),
            ("brand", "Brand", 90),
            ("model", "Model", 110),
            ("year", "Year", 55),
            ("color", "Color", 80),
            ("category", "Category", 80),
            ("daily_rate", "Daily Rate", 95),
            ("status", "Status", 85)
        ]
        self.tree, tree_container = create_scrollable_treeview(table_card, columns)
        tree_container.pack(fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self._on_car_select)

    def _reset_filters(self):
        self.ent_search.delete(0, tk.END)
        self.filter_cat.set("All")
        self.filter_stat.set("All")
        self.load_cars()

    def load_cars(self):
        """Fetches and renders cars in the Treeview table."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        search_term = self.ent_search.get().strip()
        cat = self.filter_cat.get()
        stat = self.filter_stat.get()

        cars = Car.get_all_cars(search_term=search_term, category=cat, status=stat)

        if not cars:
            # Empty state note
            self.tree.insert("", "end", values=("", "", "No cars found.", "", "", "", "", "", ""))
            return

        for idx, c in enumerate(cars):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert(
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

    def _on_car_select(self, event):
        """Populates form with selected car data."""
        selected = self.tree.selection()
        if not selected:
            return

        item_id = selected[0]
        try:
            car_id = int(item_id)
        except ValueError:
            return

        car = Car.get_car_by_id(car_id)
        if not car:
            return

        self.selected_car_id = car.id
        self.ent_number.delete(0, tk.END)
        self.ent_number.insert(0, car.car_number)

        self.ent_brand.delete(0, tk.END)
        self.ent_brand.insert(0, car.brand)

        self.ent_model.delete(0, tk.END)
        self.ent_model.insert(0, car.model)

        self.ent_year.delete(0, tk.END)
        self.ent_year.insert(0, str(car.year))

        self.ent_color.delete(0, tk.END)
        self.ent_color.insert(0, car.color)

        self.combo_category.set(car.category)

        self.ent_rate.delete(0, tk.END)
        self.ent_rate.insert(0, f"{car.daily_rate:.2f}")

        self.combo_status.set(car.status)

    def _clear_form(self):
        self.selected_car_id = None
        self.ent_number.delete(0, tk.END)
        self.ent_brand.delete(0, tk.END)
        self.ent_model.delete(0, tk.END)
        self.ent_year.delete(0, tk.END)
        self.ent_color.delete(0, tk.END)
        self.ent_rate.delete(0, tk.END)
        self.combo_category.set(CAR_CATEGORIES[0])
        self.combo_status.set(CAR_STATUSES[0])
        self.tree.selection_remove(self.tree.selection())

    def _validate_form(self):
        number = self.ent_number.get().strip()
        brand = self.ent_brand.get().strip()
        model = self.ent_model.get().strip()
        year = self.ent_year.get().strip()
        color = self.ent_color.get().strip()
        category = self.combo_category.get().strip()
        rate = self.ent_rate.get().strip()
        status = self.combo_status.get().strip()

        valid, msg = validate_car_number(number)
        if not valid:
            messagebox.showerror("Validation Error", msg)
            return None

        if not brand or len(brand) < 2:
            messagebox.showerror("Validation Error", "Please enter a valid brand / make.")
            return None

        if not model or len(model) < 1:
            messagebox.showerror("Validation Error", "Please enter a vehicle model.")
            return None

        valid, msg = validate_year(year)
        if not valid:
            messagebox.showerror("Validation Error", msg)
            return None

        if not color or len(color) < 2:
            messagebox.showerror("Validation Error", "Please enter vehicle color.")
            return None

        valid, msg = validate_daily_rate(rate)
        if not valid:
            messagebox.showerror("Validation Error", msg)
            return None

        return {
            "car_number": number.upper(),
            "brand": brand,
            "model": model,
            "year": int(year),
            "color": color,
            "category": category,
            "daily_rate": float(rate),
            "status": status
        }

    def _handle_add_car(self):
        data = self._validate_form()
        if not data:
            return

        success, msg, car_id = Car.add_car(**data)
        if success:
            messagebox.showinfo("Success", msg)
            self._clear_form()
            self.load_cars()
        else:
            messagebox.showerror("Error", msg)

    def _handle_update_car(self):
        if not self.selected_car_id:
            messagebox.showwarning("Selection Required", "Please select a car from the table to update.")
            return

        data = self._validate_form()
        if not data:
            return

        confirm = messagebox.askyesno(
            "Confirm Update",
            f"Are you sure you want to update details for car {data['car_number']}?"
        )
        if not confirm:
            return

        success, msg = Car.update_car(car_id=self.selected_car_id, **data)
        if success:
            messagebox.showinfo("Success", msg)
            self._clear_form()
            self.load_cars()
        else:
            messagebox.showerror("Error", msg)

    def _handle_delete_car(self):
        if not self.selected_car_id:
            messagebox.showwarning("Selection Required", "Please select a car from the table to delete.")
            return

        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete this car record (ID #{self.selected_car_id})?\nThis action cannot be undone."
        )
        if not confirm:
            return

        success, msg = Car.delete_car(self.selected_car_id)
        if success:
            messagebox.showinfo("Deleted", msg)
            self._clear_form()
            self.load_cars()
        else:
            messagebox.showerror("Cannot Delete", msg)
