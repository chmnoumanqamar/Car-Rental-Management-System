"""
Customer Management View (Admin)
Directory of registered customers, search, profile editing, and safe deletion.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from config import THEME, FONTS
from models.customer import Customer
from utils.validators import validate_name, validate_phone, validate_email
from utils.helpers import format_date_display, format_currency
from views.styles import create_button, create_scrollable_treeview, center_window

class CustomerEditModal(tk.Toplevel):
    """Modal dialog to update customer details."""

    def __init__(self, parent, customer: Customer, on_success):
        super().__init__(parent)
        self.customer = customer
        self.on_success = on_success
        self.title(f"Edit Customer - {customer.full_name}")
        self.configure(bg=THEME["main_bg"])
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        center_window(self, 480, 520)

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=THEME["sidebar_bg"], padx=20, pady=12)
        hdr.pack(fill="x")

        tk.Label(hdr, text="Edit Customer Profile", font=FONTS["title_small"], fg=THEME["sidebar_text"], bg=THEME["sidebar_bg"]).pack(anchor="w")
        tk.Label(hdr, text=f"Customer ID: #{self.customer.id} | Username: {self.customer.username} | CNIC: {self.customer.cnic}", font=FONTS["small"], fg=THEME["sidebar_muted"], bg=THEME["sidebar_bg"]).pack(anchor="w")

        # Form Area
        form = tk.Frame(self, bg=THEME["main_bg"], padx=25, pady=15)
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

        tk.Label(form, text="Address", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["main_bg"]).pack(anchor="w")
        self.ent_address = ttk.Entry(form, font=FONTS["body"])
        self.ent_address.pack(fill="x", pady=(2, 10))
        self.ent_address.insert(0, self.customer.address)

        tk.Label(form, text="New Password (Leave blank to keep unchanged)", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["main_bg"]).pack(anchor="w")
        self.ent_password = ttk.Entry(form, font=FONTS["body"], show="●")
        self.ent_password.pack(fill="x", pady=(2, 16))

        # Buttons
        btn_box = tk.Frame(self, bg=THEME["main_bg"], padx=25, pady=12)
        btn_box.pack(fill="x", side="bottom")

        create_button(
            btn_box,
            text="Save Changes",
            command=self._handle_save,
            bg_color=THEME["success"],
            hover_color=THEME["success_hover"]
        ).pack(side="left")

        create_button(
            btn_box,
            text="Cancel",
            command=self.destroy,
            bg_color=THEME["sidebar_hover"],
            hover_color=THEME["sidebar_bg"]
        ).pack(side="right")

    def _handle_save(self):
        name = self.ent_name.get().strip()
        phone = self.ent_phone.get().strip()
        email = self.ent_email.get().strip()
        address = self.ent_address.get().strip()
        pwd = self.ent_password.get().strip()

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
            messagebox.showerror("Validation Error", "New password must be at least 6 characters.")
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
            messagebox.showinfo("Success", "Customer profile updated successfully.")
            self.on_success()
            self.destroy()
        else:
            messagebox.showerror("Error", err)

class CustomersView(tk.Frame):
    """Customer management screen for Administrators."""

    def __init__(self, parent):
        super().__init__(parent, bg=THEME["main_bg"])
        self.selected_customer_id: Optional[int] = None
        self._build_ui()
        self.load_customers()

    def _build_ui(self):
        # Header Banner
        header = tk.Frame(self, bg=THEME["card_bg"], padx=24, pady=16, highlightbackground=THEME["card_border"], highlightthickness=1)
        header.pack(fill="x", padx=16, pady=(16, 10))

        tk.Label(
            header,
            text="👥 Customer Accounts Directory",
            font=FONTS["title_medium"],
            fg=THEME["text_primary"],
            bg=THEME["card_bg"]
        ).pack(anchor="w")

        tk.Label(
            header,
            text="View customer profiles, search by identity details, view rental history, or update records.",
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

        # Action Bar (Search + Edit + Delete)
        action_bar = tk.Frame(card, bg=THEME["card_bg"])
        action_bar.pack(fill="x", pady=(0, 12))

        tk.Label(action_bar, text="Search Customer:", font=FONTS["small_bold"], fg=THEME["text_primary"], bg=THEME["card_bg"]).pack(side="left", padx=(0, 6))
        self.ent_search = ttk.Entry(action_bar, font=FONTS["body"], width=24)
        self.ent_search.pack(side="left", padx=(0, 8))
        self.ent_search.bind("<Return>", lambda e: self.load_customers())

        create_button(
            action_bar,
            text="Search",
            command=self.load_customers,
            bg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            font=FONTS["small_bold"],
            padx=10,
            pady=4
        ).pack(side="left", padx=2)

        create_button(
            action_bar,
            text="Reset",
            command=self._reset_search,
            bg_color=THEME["sidebar_hover"],
            hover_color=THEME["sidebar_bg"],
            font=FONTS["small_bold"],
            padx=10,
            pady=4
        ).pack(side="left", padx=2)

        # Right Action Buttons
        create_button(
            action_bar,
            text=" Delete Account",
            command=self._handle_delete_customer,
            bg_color=THEME["danger"],
            hover_color=THEME["danger_hover"],
            font=FONTS["small_bold"],
            padx=12,
            pady=4
        ).pack(side="right", padx=4)

        create_button(
            action_bar,
            text="✏️ Edit Selected",
            command=self._open_edit_modal,
            bg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            font=FONTS["small_bold"],
            padx=12,
            pady=4
        ).pack(side="right", padx=4)

        # Table
        columns = [
            ("id", "ID", 45),
            ("full_name", "Full Name", 130),
            ("cnic", "CNIC", 120),
            ("phone", "Phone", 100),
            ("email", "Email Address", 140),
            ("address", "Address", 140),
            ("username", "Username", 90),
            ("created_at", "Registration Date", 100)
        ]
        self.tree, tree_container = create_scrollable_treeview(card, columns)
        tree_container.pack(fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _reset_search(self):
        self.ent_search.delete(0, tk.END)
        self.load_customers()

    def _on_select(self, event):
        selected = self.tree.selection()
        if selected:
            try:
                self.selected_customer_id = int(selected[0])
            except ValueError:
                self.selected_customer_id = None

    def load_customers(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        search_term = self.ent_search.get().strip()
        customers = Customer.get_all_customers(search_term=search_term)

        if not customers:
            self.tree.insert("", "end", values=("", "No customers found.", "", "", "", "", "", ""))
            return

        for idx, c in enumerate(customers):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert(
                "",
                "end",
                iid=str(c.id),
                values=(
                    c.id,
                    c.full_name,
                    c.cnic,
                    c.phone,
                    c.email,
                    c.address or "N/A",
                    c.username,
                    format_date_display(c.created_at)
                ),
                tags=(tag,)
            )

    def _open_edit_modal(self):
        if not self.selected_customer_id:
            messagebox.showwarning("Selection Required", "Please select a customer from the table to edit.")
            return

        customer = Customer.get_by_id(self.selected_customer_id)
        if not customer:
            return

        CustomerEditModal(self, customer, on_success=self.load_customers)

    def _handle_delete_customer(self):
        if not self.selected_customer_id:
            messagebox.showwarning("Selection Required", "Please select a customer from the table to delete.")
            return

        customer = Customer.get_by_id(self.selected_customer_id)
        if not customer:
            return

        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete customer '{customer.full_name}' (CNIC: {customer.cnic})?\n"
            "This will remove the customer account."
        )
        if not confirm:
            return

        success, msg = Customer.delete_customer(self.selected_customer_id)
        if success:
            messagebox.showinfo("Success", msg)
            self.selected_customer_id = None
            self.load_customers()
        else:
            messagebox.showerror("Cannot Delete", msg)
