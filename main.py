"""
Car Rental Management System - Main Application Entry Point
Initializes the SQLite database, configures logging, applies UI styles, and manages screen lifecycles.
"""

import sys
import tkinter as tk
from tkinter import messagebox

from config import APP_TITLE, APP_VERSION, THEME
from database import db
from models.admin import Admin
from models.customer import Customer
from utils.helpers import setup_logger, logger
from views.styles import apply_custom_styles, center_window
from views.welcome import WelcomeView
from views.admin_dashboard import AdminDashboard
from views.customer_dashboard import CustomerDashboard

class CarRentalApp:
    """Master Application Controller managing views and authentication state."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"{APP_TITLE} (v{APP_VERSION})")
        self.root.configure(bg=THEME["main_bg"])
        self.root.minsize(1050, 680)

        # Apply global ttk themes and styling
        apply_custom_styles(self.root)
        center_window(self.root, 1100, 720)

        # Setup protocol on window close
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

        # Current logged-in user references
        self.current_admin = None
        self.current_customer = None
        self.current_view = None

        # Start on Welcome View
        self.show_welcome()
        logger.info("Application initialized and ready.")

    def _clear_current_view(self):
        """Clears the active view container."""
        if self.current_view:
            self.current_view.destroy()
            self.current_view = None

    def show_welcome(self):
        """Displays the Welcome & Authentication landing screen."""
        self._clear_current_view()
        self.current_admin = None
        self.current_customer = None
        self.root.title(f"{APP_TITLE} (v{APP_VERSION})")

        self.current_view = WelcomeView(
            parent=self.root,
            on_admin_login_success=self.show_admin_dashboard,
            on_customer_login_success=self.show_customer_dashboard,
            on_exit=self.exit_app
        )
        self.current_view.pack(fill="both", expand=True)

    def show_admin_dashboard(self, admin: Admin):
        """Transitions to the Administrator Dashboard."""
        self._clear_current_view()
        self.current_admin = admin
        self.root.title(f"{APP_TITLE} - Admin Control Center ({admin.full_name})")

        self.current_view = AdminDashboard(
            parent=self.root,
            admin=admin,
            on_logout=self.show_welcome
        )
        self.current_view.pack(fill="both", expand=True)

    def show_customer_dashboard(self, customer: Customer):
        """Transitions to the Customer Self-Service Portal."""
        self._clear_current_view()
        self.current_customer = customer
        self.root.title(f"{APP_TITLE} - Customer Portal ({customer.full_name})")

        self.current_view = CustomerDashboard(
            parent=self.root,
            customer=customer,
            on_logout=self.show_welcome
        )
        self.current_view.pack(fill="both", expand=True)

    def exit_app(self):
        """Safely exits the application."""
        if messagebox.askokcancel("Exit", "Are you sure you want to exit the Car Rental Management System?"):
            logger.info("Application closed by user.")
            self.root.destroy()
            sys.exit(0)

def main():
    """Main execution function."""
    # Setup application logging
    setup_logger()
    logger.info(f"Starting {APP_TITLE} v{APP_VERSION}...")

    # Database is initialized via database.py singleton import
    logger.info("Database initialized successfully.")

    # Initialize Tkinter GUI
    root = tk.Tk()
    app = CarRentalApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
