"""
Customer Model
Handles Customer registration, authentication, directory queries, profile updates, and statistics.
"""

from typing import Optional, List, Dict, Any, Tuple
from database import db
from utils.security import hash_password, verify_password
from utils.helpers import logger

class Customer:
    """Represents a registered Customer account."""

    def __init__(
        self,
        id: int,
        full_name: str,
        cnic: str,
        phone: str,
        email: str,
        address: str,
        username: str,
        created_at: str = ""
    ):
        self.id = id
        self.full_name = full_name
        self.cnic = cnic
        self.phone = phone
        self.email = email
        self.address = address or ""
        self.username = username
        self.created_at = created_at

    def to_dict(self) -> Dict[str, Any]:
        """Converts customer object to dictionary."""
        return {
            "id": self.id,
            "full_name": self.full_name,
            "cnic": self.cnic,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "username": self.username,
            "created_at": self.created_at
        }

    @classmethod
    def from_row(cls, row) -> "Customer":
        """Creates Customer instance from sqlite3.Row."""
        return cls(
            id=row["id"],
            full_name=row["full_name"],
            cnic=row["cnic"],
            phone=row["phone"],
            email=row["email"],
            address=row["address"] if "address" in row.keys() else "",
            username=row["username"],
            created_at=row["created_at"]
        )

    @classmethod
    def register(
        cls,
        full_name: str,
        cnic: str,
        phone: str,
        email: str,
        address: str,
        username: str,
        password_plain: str
    ) -> Tuple[bool, str, Optional[int]]:
        """Registers a new customer with uniqueness checks for username and CNIC."""
        try:
            clean_username = username.strip().lower()
            clean_cnic = cnic.strip()

            # Check duplicate username
            existing_user = db.fetch_one(
                "SELECT id FROM customers WHERE LOWER(username) = ?",
                (clean_username,)
            )
            if existing_user:
                return False, f"Username '{username}' is already taken. Please choose another.", None

            # Check duplicate CNIC
            existing_cnic = db.fetch_one(
                "SELECT id FROM customers WHERE cnic = ?",
                (clean_cnic,)
            )
            if existing_cnic:
                return False, f"A customer with CNIC '{cnic}' is already registered.", None

            pw_hash = hash_password(password_plain)
            customer_id = db.execute_query("""
                INSERT INTO customers (full_name, cnic, phone, email, address, username, password)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                full_name.strip(),
                clean_cnic,
                phone.strip(),
                email.strip().lower(),
                address.strip(),
                clean_username,
                pw_hash
            ))
            logger.info(f"Customer '{username}' (ID: {customer_id}) registered successfully.")
            return True, "Account created successfully! You can now log in.", customer_id
        except Exception as e:
            logger.error(f"Customer registration failed: {e}")
            return False, f"Registration error: {str(e)}", None

    @classmethod
    def authenticate(cls, username: str, password_plain: str) -> Optional["Customer"]:
        """Verifies customer credentials safely."""
        if not username or not password_plain:
            return None
        
        row = db.fetch_one(
            "SELECT * FROM customers WHERE LOWER(username) = ?",
            (username.strip().lower(),)
        )
        if not row:
            logger.warning(f"Customer login failed: username '{username}' not found.")
            return None

        if verify_password(row["password"], password_plain):
            logger.info(f"Customer '{username}' logged in successfully.")
            return cls.from_row(row)
        else:
            logger.warning(f"Customer login failed: incorrect password for '{username}'.")
            return None

    @classmethod
    def get_by_id(cls, customer_id: int) -> Optional["Customer"]:
        """Fetches customer by ID."""
        row = db.fetch_one("SELECT * FROM customers WHERE id = ?", (customer_id,))
        return cls.from_row(row) if row else None

    @classmethod
    def get_by_cnic(cls, cnic: str) -> Optional["Customer"]:
        """Fetches customer by CNIC."""
        row = db.fetch_one("SELECT * FROM customers WHERE cnic = ?", (cnic.strip(),))
        return cls.from_row(row) if row else None

    @classmethod
    def get_all_customers(cls, search_term: str = "") -> List["Customer"]:
        """Fetches all customers with optional search filtering."""
        query = "SELECT * FROM customers WHERE 1=1"
        params: List[Any] = []

        if search_term and search_term.strip():
            term = f"%{search_term.strip()}%"
            query += " AND (full_name LIKE ? OR cnic LIKE ? OR phone LIKE ? OR email LIKE ? OR username LIKE ?)"
            params.extend([term, term, term, term, term])

        query += " ORDER BY id DESC"
        rows = db.fetch_all(query, tuple(params))
        return [cls.from_row(r) for r in rows]

    @classmethod
    def update_customer(
        cls,
        customer_id: int,
        full_name: str,
        phone: str,
        email: str,
        address: str,
        new_password: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Updates customer profile details."""
        try:
            if new_password and new_password.strip():
                pw_hash = hash_password(new_password.strip())
                db.execute_query("""
                    UPDATE customers
                    SET full_name = ?, phone = ?, email = ?, address = ?, password = ?
                    WHERE id = ?
                """, (full_name.strip(), phone.strip(), email.strip().lower(), address.strip(), pw_hash, customer_id))
            else:
                db.execute_query("""
                    UPDATE customers
                    SET full_name = ?, phone = ?, email = ?, address = ?
                    WHERE id = ?
                """, (full_name.strip(), phone.strip(), email.strip().lower(), address.strip(), customer_id))
            
            logger.info(f"Customer ID {customer_id} updated profile.")
            return True, "Profile updated successfully."
        except Exception as e:
            logger.error(f"Error updating customer {customer_id}: {e}")
            return False, f"Database error: {str(e)}"

    @classmethod
    def delete_customer(cls, customer_id: int) -> Tuple[bool, str]:
        """Deletes customer only if no active rentals exist."""
        try:
            # Check active rentals
            active = db.fetch_one(
                "SELECT COUNT(*) as count FROM rentals WHERE customer_id = ? AND status = 'Active'",
                (customer_id,)
            )
            if active and active["count"] > 0:
                return False, "Cannot delete customer with an ongoing Active car rental."

            # Check rental history
            history = db.fetch_one(
                "SELECT COUNT(*) as count FROM rentals WHERE customer_id = ?",
                (customer_id,)
            )
            if history and history["count"] > 0:
                return False, "Cannot delete customer with past rental and payment records. (Audit records must be retained)"

            db.execute_query("DELETE FROM customers WHERE id = ?", (customer_id,))
            logger.info(f"Customer ID {customer_id} deleted.")
            return True, "Customer deleted successfully."
        except Exception as e:
            logger.error(f"Error deleting customer {customer_id}: {e}")
            return False, f"Database error: {str(e)}"

    @classmethod
    def get_customer_stats(cls, customer_id: int) -> Dict[str, Any]:
        """Calculates dashboard metrics for customer."""
        active = db.fetch_one("""
            SELECT COUNT(*) as count FROM rentals 
            WHERE customer_id = ? AND status = 'Active'
        """, (customer_id,))
        
        total_rentals = db.fetch_one("""
            SELECT COUNT(*) as count FROM rentals 
            WHERE customer_id = ?
        """, (customer_id,))

        total_spent = db.fetch_one("""
            SELECT COALESCE(SUM(amount), 0.0) as total FROM payments 
            WHERE customer_id = ? AND payment_status = 'Paid'
        """, (customer_id,))

        return {
            "active_rentals": active["count"] if active else 0,
            "total_rentals": total_rentals["count"] if total_rentals else 0,
            "total_spent": float(total_spent["total"]) if total_spent else 0.0
        }
