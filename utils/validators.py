"""
Validation Utilities
Provides robust input validations for user registration, cars, dates, and amounts.
"""

import re
from datetime import datetime, date
from typing import Tuple

# Regex Patterns
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
CNIC_REGEX = re.compile(r"^\d{5}-\d{7}-\d{1}$")
PHONE_REGEX = re.compile(r"^(?:\+92|92|0)?3\d{2}[-\s]?\d{7}$")
USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_]{3,30}$")

def validate_name(name: str) -> Tuple[bool, str]:
    """Validate full name (letters, spaces, dots, hyphens; min 2 chars)."""
    if not name or not name.strip():
        return False, "Full Name is required."
    clean = name.strip()
    if len(clean) < 2:
        return False, "Full Name must be at least 2 characters."
    if not re.match(r"^[a-zA-Z\s.'-]+$", clean):
        return False, "Full Name can only contain letters, spaces, dots, and hyphens."
    return True, ""

def validate_cnic(cnic: str) -> Tuple[bool, str]:
    """Validate Pakistan CNIC format (XXXXX-XXXXXXX-X)."""
    if not cnic or not cnic.strip():
        return False, "CNIC is required."
    clean = cnic.strip()
    if not CNIC_REGEX.match(clean):
        return False, "CNIC must follow the format XXXXX-XXXXXXX-X (e.g. 35201-1234567-1)."
    return True, ""

def validate_phone(phone: str) -> Tuple[bool, str]:
    """Validate Pakistani phone number."""
    if not phone or not phone.strip():
        return False, "Phone number is required."
    clean = phone.strip()
    if not PHONE_REGEX.match(clean):
        return False, "Phone number must be a valid Pakistani mobile number (e.g., 0300-1234567 or 03211234567)."
    return True, ""

def validate_email(email: str) -> Tuple[bool, str]:
    """Validate standard email address."""
    if not email or not email.strip():
        return False, "Email is required."
    clean = email.strip()
    if not EMAIL_REGEX.match(clean):
        return False, "Please enter a valid email address (e.g., user@example.com)."
    return True, ""

def validate_username(username: str) -> Tuple[bool, str]:
    """Validate username."""
    if not username or not username.strip():
        return False, "Username is required."
    clean = username.strip()
    if len(clean) < 3:
        return False, "Username must be at least 3 characters."
    if not USERNAME_REGEX.match(clean):
        return False, "Username can only contain alphanumeric characters and underscores."
    return True, ""

def validate_password(password: str, confirm_password: str = None) -> Tuple[bool, str]:
    """Validate password and optional confirmation."""
    if not password:
        return False, "Password cannot be empty."
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    if confirm_password is not None and password != confirm_password:
        return False, "Password and Confirmation Password do not match."
    return True, ""

def validate_car_number(car_number: str) -> Tuple[bool, str]:
    """Validate registration car plate number."""
    if not car_number or not car_number.strip():
        return False, "Car Number / License Plate is required."
    clean = car_number.strip().upper()
    if len(clean) < 3 or len(clean) > 15:
        return False, "Car Number must be between 3 and 15 characters."
    return True, ""

def validate_year(year_val) -> Tuple[bool, str]:
    """Validate vehicle manufacturing year."""
    try:
        y = int(year_val)
        current_year = datetime.now().year
        if y < 1990 or y > current_year + 1:
            return False, f"Year must be between 1990 and {current_year + 1}."
        return True, ""
    except (ValueError, TypeError):
        return False, "Year must be a valid 4-digit number."

def validate_daily_rate(rate_val) -> Tuple[bool, str]:
    """Validate daily rental rate."""
    try:
        r = float(rate_val)
        if r <= 0:
            return False, "Daily rental rate must be greater than 0."
        return True, ""
    except (ValueError, TypeError):
        return False, "Daily rental rate must be a valid positive number."

def validate_rental_dates(start_date_str: str, end_date_str: str, allow_past: bool = False) -> Tuple[bool, str, int]:
    """
    Validates start date and end date strings in YYYY-MM-DD format.
    Returns: (is_valid, error_message, rental_days)
    """
    try:
        start_dt = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return False, "Invalid date format. Expected YYYY-MM-DD.", 0

    today = date.today()
    if not allow_past and start_dt < today:
        return False, "Rental start date cannot be in the past.", 0

    if end_dt < start_dt:
        return False, "Return date cannot be earlier than the start date.", 0

    rental_days = (end_dt - start_dt).days
    if rental_days <= 0:
        # Same day rental is minimum 1 day
        rental_days = 1

    return True, "", rental_days
