"""
Database Manager Module
Handles SQLite database connection, table initialization, foreign key enforcement,
query execution with parameterization, transactions, and initial demo data seeding.
"""

import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime, date, timedelta
from typing import List, Tuple, Dict, Any, Optional

from config import DATABASE_PATH, DEFAULT_SECURITY_DEPOSIT
from utils.security import hash_password
from utils.helpers import logger

class DatabaseManager:
    """Manages SQLite database connections, execution, transactions, and migrations."""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.initialize_database()

    @contextmanager
    def get_connection(self):
        """Context manager for SQLite database connection with row_factory and foreign keys."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database transaction error rolled back: {e}")
            raise
        finally:
            conn.close()

    def execute_query(self, query: str, params: Tuple = ()) -> int:
        """Executes INSERT, UPDATE, DELETE queries and returns lastrowid or affected count."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.lastrowid

    def fetch_one(self, query: str, params: Tuple = ()) -> Optional[sqlite3.Row]:
        """Fetches a single row."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()

    def fetch_all(self, query: str, params: Tuple = ()) -> List[sqlite3.Row]:
        """Fetches all matching rows."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    def initialize_database(self):
        """Creates the necessary schema tables and indexes if they do not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Admins Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Customers Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                cnic TEXT UNIQUE NOT NULL,
                phone TEXT NOT NULL,
                email TEXT NOT NULL,
                address TEXT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Cars Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS cars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                car_number TEXT UNIQUE NOT NULL,
                brand TEXT NOT NULL,
                model TEXT NOT NULL,
                year INTEGER NOT NULL,
                color TEXT NOT NULL,
                category TEXT NOT NULL,
                daily_rate REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'Available',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Rentals Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS rentals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                car_id INTEGER NOT NULL,
                rental_date TEXT NOT NULL,
                return_date TEXT NOT NULL,
                actual_return_date TEXT,
                rental_days INTEGER NOT NULL,
                daily_rate REAL NOT NULL,
                total_amount REAL NOT NULL,
                security_deposit REAL NOT NULL DEFAULT 5000.0,
                status TEXT NOT NULL DEFAULT 'Active',
                FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE RESTRICT,
                FOREIGN KEY (car_id) REFERENCES cars(id) ON DELETE RESTRICT
            );
            """)

            # Payments Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rental_id INTEGER NOT NULL,
                customer_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                payment_method TEXT NOT NULL,
                payment_date TEXT NOT NULL,
                payment_status TEXT NOT NULL DEFAULT 'Paid',
                FOREIGN KEY (rental_id) REFERENCES rentals(id) ON DELETE RESTRICT,
                FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE RESTRICT
            );
            """)

            # Useful Indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cars_status ON cars(status);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cars_category ON cars(category);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rentals_status ON rentals(status);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rentals_customer ON rentals(customer_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rentals_car ON rentals(car_id);")

        self.seed_demo_data()

    def seed_demo_data(self):
        """Seeds initial admin and sample data if tables are empty."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check Admin
            cursor.execute("SELECT COUNT(*) as count FROM admins")
            if cursor.fetchone()["count"] == 0:
                admin_pw_hash = hash_password("admin123")
                cursor.execute("""
                    INSERT INTO admins (username, password, full_name, email)
                    VALUES (?, ?, ?, ?)
                """, ("admin", admin_pw_hash, "System Administrator", "admin@carrentalsystem.com"))
                logger.info("Demo Admin created: username='admin', password='admin123'")

            # Check Customers
            cursor.execute("SELECT COUNT(*) as count FROM customers")
            if cursor.fetchone()["count"] == 0:
                c1_hash = hash_password("customer123")
                c2_hash = hash_password("customer123")
                cursor.execute("""
                    INSERT INTO customers (full_name, cnic, phone, email, address, username, password)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, ("Ali Khan", "35201-1234567-1", "0300-1234567", "ali.khan@example.com", "Gulberg III, Lahore", "ali_khan", c1_hash))
                
                cursor.execute("""
                    INSERT INTO customers (full_name, cnic, phone, email, address, username, password)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, ("Sara Ahmed", "35202-9876543-2", "0321-7654321", "sara.ahmed@example.com", "F-7/2, Islamabad", "sara_ahmed", c2_hash))
                logger.info("Demo Customers created: 'ali_khan' & 'sara_ahmed'")

            # Check Cars
            cursor.execute("SELECT COUNT(*) as count FROM cars")
            if cursor.fetchone()["count"] == 0:
                sample_cars = [
                    ("LE-21-4589", "Toyota", "Corolla Altis", 2022, "Super White", "Sedan", 6500.0, "Available"),
                    ("ICT-22-1029", "Honda", "Civic RS Turbo", 2023, "Crystal Black", "Sedan", 9500.0, "Rented"),
                    ("KHI-20-7711", "Toyota", "Fortuner Legender", 2022, "Phantom Brown", "SUV", 22000.0, "Available"),
                    ("LHR-23-3344", "Hyundai", "Tucson AWD", 2023, "Silver Metallic", "SUV", 15000.0, "Available"),
                    ("ISB-24-8800", "Mercedes-Benz", "E-Class E200", 2024, "Obsidian Black", "Luxury", 45000.0, "Available"),
                    ("LHR-19-5566", "Suzuki", "Alto VXL", 2021, "Silky Silver", "Economy", 3200.0, "Available"),
                    ("ISB-22-9090", "Suzuki", "Cultus Auto Gear Shift", 2022, "Graphite Grey", "Economy", 4000.0, "Maintenance"),
                    ("LE-23-9999", "Ford", "Mustang GT 5.0", 2023, "Race Red", "Sports", 60000.0, "Available"),
                    ("KHI-21-3412", "Toyota", "Hiace Grand Cabin", 2021, "White", "Van", 18000.0, "Available"),
                    ("LHR-22-4411", "Kia", "Sportage Alpha", 2022, "Clear White", "SUV", 13500.0, "Available")
                ]
                
                cursor.executemany("""
                    INSERT INTO cars (car_number, brand, model, year, color, category, daily_rate, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, sample_cars)
                logger.info("Seeded 10 sample vehicles into inventory.")

            # Seed a sample active rental and a completed rental for realistic demo stats
            cursor.execute("SELECT COUNT(*) as count FROM rentals")
            if cursor.fetchone()["count"] == 0:
                # Customer 1 (Ali Khan) rented Honda Civic (id 2)
                today_str = date.today().strftime("%Y-%m-%d")
                return_str = (date.today() + timedelta(days=4)).strftime("%Y-%m-%d")
                past_start = (date.today() - timedelta(days=10)).strftime("%Y-%m-%d")
                past_return = (date.today() - timedelta(days=7)).strftime("%Y-%m-%d")
                
                # Active Rental
                cursor.execute("""
                    INSERT INTO rentals (customer_id, car_id, rental_date, return_date, rental_days, daily_rate, total_amount, security_deposit, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (1, 2, today_str, return_str, 4, 9500.0, 38000.0, 5000.0, "Active"))
                active_rental_id = cursor.lastrowid

                # Payment for Active Rental
                cursor.execute("""
                    INSERT INTO payments (rental_id, customer_id, amount, payment_method, payment_date, payment_status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (active_rental_id, 1, 43000.0, "Card", today_str, "Paid"))

                # Completed Rental (Sara Ahmed rented Toyota Corolla id 1 in past)
                cursor.execute("""
                    INSERT INTO rentals (customer_id, car_id, rental_date, return_date, actual_return_date, rental_days, daily_rate, total_amount, security_deposit, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (2, 1, past_start, past_return, past_return, 3, 6500.0, 19500.0, 5000.0, "Completed"))
                completed_rental_id = cursor.lastrowid

                # Payment for Completed Rental
                cursor.execute("""
                    INSERT INTO payments (rental_id, customer_id, amount, payment_method, payment_date, payment_status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (completed_rental_id, 2, 24500.0, "Bank Transfer", past_start, "Paid"))
                
                logger.info("Seeded sample active and completed rentals with payments.")

# Singleton instance
db = DatabaseManager()
