"""
Automated Test Suite for Car Rental Management System
Validates database schema, authentication, validators, business rules, transactions, and CSV exports.
"""

import os
import sys
import unittest
from datetime import datetime, date, timedelta
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import DEFAULT_SECURITY_DEPOSIT
from database import DatabaseManager
from utils.security import hash_password, verify_password
from utils.validators import (
    validate_name, validate_cnic, validate_phone,
    validate_email, validate_username, validate_password,
    validate_car_number, validate_year, validate_daily_rate,
    validate_rental_dates
)
from utils.helpers import format_currency, format_date_display, generate_receipt_text, export_to_csv
from models.admin import Admin
from models.customer import Customer
from models.car import Car
from models.rental import Rental
from models.payment import Payment

class TestCarRentalSystem(unittest.TestCase):
    """Unit and Integration tests for core business logic and data layer."""

    @classmethod
    def setUpClass(cls):
        """Initializes database schema and test data."""
        cls.db = DatabaseManager()

    def test_01_password_hashing(self):
        """Test secure password hashing and verification."""
        password = "SecurePassword123!"
        hashed = hash_password(password)
        
        self.assertIn("$", hashed)
        self.assertTrue(verify_password(hashed, password))
        self.assertFalse(verify_password(hashed, "WrongPassword"))
        self.assertFalse(verify_password("", password))

    def test_02_validators(self):
        """Test CNIC, phone, email, and name validators."""
        # CNIC
        self.assertTrue(validate_cnic("35201-1234567-1")[0])
        self.assertFalse(validate_cnic("12345")[0])
        self.assertFalse(validate_cnic("3520112345671")[0])

        # Phone
        self.assertTrue(validate_phone("0300-1234567")[0])
        self.assertTrue(validate_phone("03211234567")[0])
        self.assertFalse(validate_phone("12345")[0])

        # Email
        self.assertTrue(validate_email("test.user@domain.com")[0])
        self.assertFalse(validate_email("invalid-email")[0])

        # Name
        self.assertTrue(validate_name("Muhammad Ali")[0])
        self.assertFalse(validate_name("A123")[0])

        # Dates
        today_str = date.today().strftime("%Y-%m-%d")
        next_week_str = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")
        past_str = (date.today() - timedelta(days=5)).strftime("%Y-%m-%d")

        valid, _, days = validate_rental_dates(today_str, next_week_str)
        self.assertTrue(valid)
        self.assertEqual(days, 7)

        self.assertFalse(validate_rental_dates(past_str, today_str, allow_past=False)[0])
        self.assertFalse(validate_rental_dates(next_week_str, today_str)[0])

    def test_03_admin_authentication(self):
        """Test admin login with valid and invalid credentials."""
        admin = Admin.authenticate("admin", "admin123")
        self.assertIsNotNone(admin)
        self.assertEqual(admin.username, "admin")

        wrong_admin = Admin.authenticate("admin", "wrong_password")
        self.assertIsNone(wrong_admin)

    def test_04_customer_registration_and_auth(self):
        """Test customer registration, duplicate rejection, and authentication."""
        timestamp = datetime.now().strftime("%H%M%S")
        test_user = f"test_cust_{timestamp}"
        test_cnic = f"35201-{timestamp[:7]}-1"

        # Register
        success, msg, cust_id = Customer.register(
            full_name="Test Customer",
            cnic=test_cnic,
            phone="0300-9999999",
            email=f"{test_user}@test.com",
            address="Lahore, Pakistan",
            username=test_user,
            password_plain="testpass123"
        )
        self.assertTrue(success, msg)
        self.assertIsNotNone(cust_id)

        # Duplicate username rejection
        dup_success, dup_msg, _ = Customer.register(
            full_name="Duplicate User",
            cnic="35202-0000000-1",
            phone="0300-8888888",
            email="other@test.com",
            address="Islamabad",
            username=test_user,
            password_plain="testpass123"
        )
        self.assertFalse(dup_success)

        # Authenticate
        auth_cust = Customer.authenticate(test_user, "testpass123")
        self.assertIsNotNone(auth_cust)
        self.assertEqual(auth_cust.id, cust_id)

    def test_05_car_inventory_operations(self):
        """Test adding cars, duplicate registration rejection, updates, and searches."""
        test_plate = f"TEST-{datetime.now().strftime('%M%S')}"
        
        # Add car
        success, msg, car_id = Car.add_car(
            car_number=test_plate,
            brand="Audi",
            model="A6 Quattro",
            year=2023,
            color="Ibis White",
            category="Luxury",
            daily_rate=35000.0,
            status="Available"
        )
        self.assertTrue(success, msg)
        self.assertIsNotNone(car_id)

        # Duplicate plate rejection
        dup_success, _, _ = Car.add_car(
            car_number=test_plate,
            brand="Audi",
            model="A6 Quattro",
            year=2023,
            color="Black",
            category="Luxury",
            daily_rate=35000.0
        )
        self.assertFalse(dup_success)

        # Update
        up_success, _ = Car.update_car(
            car_id=car_id,
            car_number=test_plate,
            brand="Audi",
            model="A6 Matrix",
            year=2024,
            color="Glacier White",
            category="Luxury",
            daily_rate=38000.0,
            status="Available"
        )
        self.assertTrue(up_success)

        # Verify updated info
        fetched = Car.get_car_by_id(car_id)
        self.assertEqual(fetched.model, "A6 Matrix")
        self.assertEqual(fetched.daily_rate, 38000.0)

    def test_06_rental_transaction_and_state_changes(self):
        """Test transactional rental creation and vehicle status change."""
        # Add a car for this test
        plate = f"RENT-{datetime.now().strftime('%M%S')}"
        _, _, car_id = Car.add_car(
            car_number=plate,
            brand="BMW",
            model="3 Series",
            year=2023,
            color="Blue",
            category="Sedan",
            daily_rate=15000.0,
            status="Available"
        )

        customer = Customer.get_all_customers()[0]
        start_date = date.today().strftime("%Y-%m-%d")
        return_date = (date.today() + timedelta(days=5)).strftime("%Y-%m-%d")
        daily_rate = 15000.0
        rental_days = 5
        rental_cost = daily_rate * rental_days
        security_deposit = 5000.0

        # Book rental
        success, msg, rental_id = Rental.create_rental(
            customer_id=customer.id,
            car_id=car_id,
            rental_date=start_date,
            return_date=return_date,
            rental_days=rental_days,
            daily_rate=daily_rate,
            total_amount=rental_cost,
            security_deposit=security_deposit,
            payment_method="Card"
        )
        self.assertTrue(success, msg)
        self.assertIsNotNone(rental_id)

        # Check car status changed to 'Rented'
        car = Car.get_car_by_id(car_id)
        self.assertEqual(car.status, "Rented")

        # Attempt to rent an already rented car (must fail)
        fail_success, fail_msg, _ = Rental.create_rental(
            customer_id=customer.id,
            car_id=car_id,
            rental_date=start_date,
            return_date=return_date,
            rental_days=rental_days,
            daily_rate=daily_rate,
            total_amount=rental_cost,
            security_deposit=security_deposit
        )
        self.assertFalse(fail_success)
        self.assertIn("not available", fail_msg.lower())

        # Check payment record created
        payments = Payment.get_all_payments()
        matching_payment = [p for p in payments if p["rental_id"] == rental_id]
        self.assertEqual(len(matching_payment), 1)
        self.assertEqual(matching_payment[0]["amount"], rental_cost + security_deposit)

    def test_07_return_settlement_and_late_penalty(self):
        """Test returning a vehicle with automated late fee calculation."""
        # Create rental with due date 2 days ago
        plate = f"LATE-{datetime.now().strftime('%M%S')}"
        _, _, car_id = Car.add_car(
            car_number=plate,
            brand="Honda",
            model="HR-V",
            year=2023,
            color="Red",
            category="SUV",
            daily_rate=10000.0,
            status="Available"
        )
        customer = Customer.get_all_customers()[0]
        start_date = (date.today() - timedelta(days=6)).strftime("%Y-%m-%d")
        due_date = (date.today() - timedelta(days=2)).strftime("%Y-%m-%d")
        today_str = date.today().strftime("%Y-%m-%d")

        _, _, rental_id = Rental.create_rental(
            customer_id=customer.id,
            car_id=car_id,
            rental_date=start_date,
            return_date=due_date,
            rental_days=4,
            daily_rate=10000.0,
            total_amount=40000.0,
            security_deposit=5000.0
        )

        # Process Return today (2 days late)
        success, msg, res = Rental.process_return(
            rental_id=rental_id,
            actual_return_date=today_str
        )
        self.assertTrue(success, msg)
        self.assertEqual(res["late_days"], 2)
        self.assertEqual(res["late_charges"], 20000.0) # 2 * 10000
        self.assertEqual(res["final_total"], 60000.0) # 40000 + 20000

        # Car must be restored to 'Available'
        car = Car.get_car_by_id(car_id)
        self.assertEqual(car.status, "Available")

        # Rental status must be 'Completed'
        rental_data = Rental.get_rental_by_id(rental_id)
        self.assertEqual(rental_data["status"], "Completed")

    def test_08_receipt_generation_and_csv_export(self):
        """Test invoice formatting and CSV reports export."""
        receipt = generate_receipt_text(
            rental_id=999,
            customer_name="Test Customer",
            customer_cnic="35201-1234567-1",
            customer_phone="0300-1234567",
            car_number="TEST-999",
            car_brand="Toyota",
            car_model="Corolla",
            rental_date="2026-08-27",
            expected_return_date="2026-08-30",
            rental_days=3,
            daily_rate=5000.0,
            rental_amount=15000.0,
            security_deposit=5000.0,
            total_amount=20000.0
        )
        self.assertIn("OFFICIAL RENTAL INVOICE & RECEIPT", receipt)
        self.assertIn("Test Customer", receipt)
        self.assertIn("TEST-999", receipt)

        # CSV Export
        headers = ["ID", "Name", "Total"]
        rows = [[1, "Sample", 1000]]
        csv_path = export_to_csv("test_export", headers, rows)
        self.assertTrue(os.path.exists(csv_path))

if __name__ == "__main__":
    unittest.main(verbosity=2)
