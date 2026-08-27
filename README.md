# Car Rental Management System

**Fast • Reliable • Easy Car Rental Management**

A complete, professional, modular, and secure **Car Rental Management System** in Python. Built using **Tkinter** for a modern GUI, **SQLite3** for ACID-compliant relational data management, and **OOP (Object-Oriented Programming)** architecture.

---

## 🌟 Key Features

### 🛡️ 1. Authentication & Role-Based Access Control
* **Administrator Portal**: Secure login with password hashing.
* **Customer Self-Service**: Full registration with Pakistani format validations (CNIC `XXXXX-XXXXXXX-X`, Mobile `03XX-XXXXXXX`, email format, username uniqueness).
* **Cryptographic Security**: Salted PBKDF2-HMAC-SHA256 password hashing. Passwords are never stored or logged in plain text.

### 🚗 2. Vehicle Fleet Management
* Complete inventory CRUD (Add, Edit, Safe Delete, Search).
* Real-time categorization (Economy, Sedan, SUV, Luxury, Sports, Van, Hatchback).
* Status management (`Available`, `Rented`, `Maintenance`).
* Duplicate vehicle registration number prevention.

### 📋 3. Rental Agreement & Dynamic Booking
* Interactive booking wizard with automatic date calculation.
* Rental amount calculated programmatically (`Total = Daily Rate × Days`).
* Clear distinction between rental charges and refundable security deposit.
* Safe database transactions (checks availability, creates agreement, logs payment, marks car as `Rented`).

### 🔄 4. Car Return & Automated Late Penalties
* Quick search by Rental ID, Plate Number, or Customer CNIC.
* Automatic late fee calculation (`Late Charge = Overdue Days × Daily Rate`).
* Automatic vehicle availability restoration upon check-in.

### 🧾 5. Digital Receipts & Invoices
* Structured ASCII official invoice generator.
* Complete breakdown of customer details, car specs, schedule, rental charges, deposits, and late fees.
* 1-click export/save receipt to text files (`.txt`).

### 💳 6. Financial Ledger & Payments
* Full audit trail of payments across Cash, Card, and Bank Transfer channels.
* Payment status tracking (`Paid`, `Pending`, `Refunded`).

### 📊 7. Reports & CSV Analytics
* Dynamic KPI dashboard (Fleet breakdown, Customer metrics, Active/Completed rentals, Total revenue).
* Category and vehicle-specific revenue summaries.
* 1-click CSV exports for:
  - `cars_report.csv`
  - `customers_report.csv`
  - `rentals_report.csv`
  - `payments_report.csv`
  - `revenue_report.csv`

---

## 🚀 Project Architecture

```
Car rental system/
│
├── main.py                     # Application entry point, logging setup, window lifecycle
├── config.py                   # System constants, styling tokens, categories, statuses
├── database.py                 # SQLite DatabaseManager with transactions & seeding
├── car_rental.db               # SQLite database file (auto-generated)
├── car_rental.log              # Application event & error log (auto-generated)
├── requirements.txt            # Dependencies documentation
├── README.md                   # Complete system documentation
│
├── models/                     # OOP Data Access Layer & Business Logic
│   ├── __init__.py
│   ├── admin.py                # Admin entity and auth methods
│   ├── car.py                  # Fleet inventory & status management
│   ├── customer.py             # Customer profile & auth
│   ├── rental.py               # Rental bookings, returns, and late calculations
│   └── payment.py              # Financial records & revenue aggregations
│
├── utils/                      # Reusable Helpers & Utilities
│   ├── __init__.py
│   ├── security.py             # Salted PBKDF2 password hashing & verification
│   ├── validators.py           # CNIC, Mobile, Email, Name, and Date validators
│   └── helpers.py              # Date formatters, currency formatters, CSV exporter, logger
│
├── views/                      # Modern Tkinter Presentation Layer
│   ├── __init__.py
│   ├── styles.py               # Custom ttk styles, color palettes, fonts, stat cards
│   ├── welcome.py              # Modern landing screen (Customer Login, Admin Login, Reg)
│   ├── admin_dashboard.py      # Admin control center with sidebar & 8 KPI stat cards
│   ├── customer_dashboard.py   # Customer portal (Browse fleet, Rent, History, Profile)
│   ├── cars_view.py            # Vehicle inventory management
│   ├── customers_view.py       # Customer directory & profile management
│   ├── rental_view.py          # Rental agreements ledger & interactive booking modal
│   ├── return_view.py          # Return check-in with automatic late penalty math
│   ├── payment_view.py         # Financial ledger view
│   ├── reports_view.py         # Analytics summary & CSV export dashboard
│   └── receipt_view.py         # Official rental invoice modal & file exporter
│
├── reports/                    # Auto-generated CSV reports & receipts folder
└── tests/
    └── test_system.py          # Automated test suite
```

---

## 🔑 Demo Credentials

The database automatically seeds sample data on first run:

| Role | Username | Password | Notes |
|---|---|---|---|
| **Administrator** | `admin` | `admin123` | Full administrative control |
| **Customer 1** | `ali_khan` | `customer123` | Pre-configured active rental |
| **Customer 2** | `sara_ahmed` | `customer123` | Pre-configured completed rental |

> *Note: In a production deployment, default passwords should be updated via the Profile Settings menu.*

---

## 🛠️ Requirements & Installation

### Requirements
* **Python 3.8 or higher**
* Works out-of-the-box on Windows, Linux, and macOS.
* Uses Python's standard libraries (`tkinter`, `sqlite3`, `hashlib`, `secrets`, `csv`, `logging`). No external dependencies are needed.

### Running the Application
1. Open your terminal / PowerShell in the project directory:
   ```bash
   cd "Car rental system"
   ```
2. Start the application:
   ```bash
   python main.py
   ```

---

## 🧪 Running Automated Tests

Run the test suite to verify database schemas, password hashing, input validations, booking transactions, and late penalty calculations:

```bash
python tests/test_system.py
```

---

## 🗄️ Database Schema

The SQLite database `car_rental.db` enforces relational integrity with `PRAGMA foreign_keys = ON`:

* **`admins`**: `id`, `username` (UNIQUE), `password` (HASH), `full_name`, `email`, `created_at`
* **`customers`**: `id`, `full_name`, `cnic` (UNIQUE), `phone`, `email`, `address`, `username` (UNIQUE), `password` (HASH), `created_at`
* **`cars`**: `id`, `car_number` (UNIQUE), `brand`, `model`, `year`, `color`, `category`, `daily_rate`, `status`, `created_at`
* **`rentals`**: `id`, `customer_id` (FK), `car_id` (FK), `rental_date`, `return_date`, `actual_return_date`, `rental_days`, `daily_rate`, `total_amount`, `security_deposit`, `status`
* **`payments`**: `id`, `rental_id` (FK), `customer_id` (FK), `amount`, `payment_method`, `payment_date`, `payment_status`

---

## 🔮 Future Improvements
* SMS / WhatsApp instant rental confirmation alerts.
* Direct integration with online payment gateways (Stripe / JazzCash / EasyPaisa).
* Export receipts directly to PDF.
* Cloud PostgreSQL database synchronization.
