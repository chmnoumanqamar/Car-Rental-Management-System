"""
Car Rental Management System - Configuration
Centralized configuration settings, styling tokens, and constants.
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = str(BASE_DIR / "car_rental.db")
LOG_FILE_PATH = str(BASE_DIR / "car_rental.log")
REPORTS_DIR = BASE_DIR / "reports"
ASSETS_DIR = BASE_DIR / "assets"

# Ensure runtime directories exist
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Application Info
APP_TITLE = "Car Rental Management System"
APP_SUBTITLE = "Fast • Reliable • Easy Car Rental Management"
APP_VERSION = "1.0.0"

# Financial & Rental Defaults
DEFAULT_SECURITY_DEPOSIT = 5000.0  # in PKR
DEFAULT_CURRENCY = "PKR"

# Business Options & Constants
CAR_CATEGORIES = [
    "Economy",
    "Sedan",
    "SUV",
    "Luxury",
    "Sports",
    "Van",
    "Hatchback"
]

CAR_STATUSES = [
    "Available",
    "Rented",
    "Maintenance"
]

RENTAL_STATUSES = [
    "Active",
    "Completed",
    "Cancelled"
]

PAYMENT_METHODS = [
    "Cash",
    "Card",
    "Bank Transfer"
]

PAYMENT_STATUSES = [
    "Paid",
    "Pending",
    "Refunded"
]

# UI Color Palette (Modern Dark-Slate & Vibrant Indigo / Emerald Accents)
THEME = {
    "bg_dark": "#0F172A",          # Slate 900
    "sidebar_bg": "#1E293B",       # Slate 800
    "sidebar_hover": "#334155",    # Slate 700
    "sidebar_active": "#2563EB",   # Blue 600
    "sidebar_text": "#F8FAFC",     # Slate 50
    "sidebar_muted": "#94A3B8",    # Slate 400
    
    "main_bg": "#F1F5F9",          # Slate 100
    "card_bg": "#FFFFFF",          # Pure White
    "card_border": "#E2E8F0",      # Slate 200
    
    "text_primary": "#0F172A",     # Slate 900
    "text_secondary": "#475569",   # Slate 600
    "text_muted": "#94A3B8",       # Slate 400
    
    "primary": "#2563EB",          # Royal Blue
    "primary_hover": "#1D4ED8",    # Darker Blue
    "primary_light": "#DBEAFE",    # Light Blue
    
    "success": "#10B981",          # Emerald Green
    "success_hover": "#059669",
    "success_light": "#D1FAE5",
    
    "warning": "#F59E0B",          # Amber Warning
    "warning_hover": "#D97706",
    "warning_light": "#FEF3C7",
    
    "danger": "#EF4444",           # Crimson Red
    "danger_hover": "#DC2626",
    "danger_light": "#FEE2E2",
    
    "purple": "#8B5CF6",           # Purple Accent
    "purple_light": "#EDE9FE",
    
    "table_header_bg": "#1E293B",
    "table_header_fg": "#FFFFFF",
    "table_row_alt": "#F8FAFC",
    "table_row_select": "#BFDBFE"
}

# Typography
FONTS = {
    "title_large": ("Segoe UI", 20, "bold"),
    "title_medium": ("Segoe UI", 15, "bold"),
    "title_small": ("Segoe UI", 12, "bold"),
    "body": ("Segoe UI", 10, "normal"),
    "body_bold": ("Segoe UI", 10, "bold"),
    "small": ("Segoe UI", 9, "normal"),
    "small_bold": ("Segoe UI", 9, "bold"),
    "monospace": ("Consolas", 10, "normal"),
    "receipt_header": ("Courier New", 12, "bold"),
    "receipt_body": ("Courier New", 10, "normal")
}
