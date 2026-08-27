"""
Payment Model
Handles payment records, financial ledgers, revenue aggregations, and statistics.
"""

from typing import Optional, List, Dict, Any, Tuple
from database import db
from utils.helpers import logger, today_iso

class Payment:
    """Represents a payment transaction."""

    def __init__(
        self,
        id: int,
        rental_id: int,
        customer_id: int,
        amount: float,
        payment_method: str,
        payment_date: str,
        payment_status: str = "Paid"
    ):
        self.id = id
        self.rental_id = rental_id
        self.customer_id = customer_id
        self.amount = float(amount)
        self.payment_method = payment_method
        self.payment_date = payment_date
        self.payment_status = payment_status

    @classmethod
    def record_payment(
        cls,
        rental_id: int,
        customer_id: int,
        amount: float,
        payment_method: str,
        payment_status: str = "Paid",
        payment_date: Optional[str] = None
    ) -> int:
        """Records a new payment."""
        date_str = payment_date or today_iso()
        payment_id = db.execute_query("""
            INSERT INTO payments (rental_id, customer_id, amount, payment_method, payment_date, payment_status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            rental_id,
            customer_id,
            float(amount),
            payment_method,
            date_str,
            payment_status
        ))
        logger.info(f"Payment recorded ID #{payment_id}: {amount} via {payment_method} for Rental #{rental_id}")
        return payment_id

    @classmethod
    def get_all_payments(
        cls,
        method_filter: str = "All",
        status_filter: str = "All",
        search_term: str = ""
    ) -> List[Dict[str, Any]]:
        """Fetches all payment records with filters and search."""
        query = """
            SELECT p.*, 
                   cust.full_name as customer_name, cust.cnic as customer_cnic,
                   c.car_number, c.brand, c.model
            FROM payments p
            JOIN customers cust ON p.customer_id = cust.id
            JOIN rentals r ON p.rental_id = r.id
            JOIN cars c ON r.car_id = c.id
            WHERE 1=1
        """
        params: List[Any] = []

        if method_filter and method_filter != "All":
            query += " AND p.payment_method = ?"
            params.append(method_filter)

        if status_filter and status_filter != "All":
            query += " AND p.payment_status = ?"
            params.append(status_filter)

        if search_term and search_term.strip():
            term = f"%{search_term.strip()}%"
            query += """ AND (
                p.id LIKE ? OR 
                p.rental_id LIKE ? OR 
                cust.full_name LIKE ? OR 
                cust.cnic LIKE ? OR 
                c.car_number LIKE ?
            )"""
            params.extend([term, term, term, term, term])

        query += " ORDER BY p.id DESC"
        rows = db.fetch_all(query, tuple(params))
        return [dict(r) for r in rows]

    @classmethod
    def get_customer_payments(cls, customer_id: int) -> List[Dict[str, Any]]:
        """Fetches payment records for a specific customer."""
        rows = db.fetch_all("""
            SELECT p.*, c.car_number, c.brand, c.model
            FROM payments p
            JOIN rentals r ON p.rental_id = r.id
            JOIN cars c ON r.car_id = c.id
            WHERE p.customer_id = ?
            ORDER BY p.id DESC
        """, (customer_id,))
        return [dict(r) for r in rows]

    @classmethod
    def get_revenue_statistics(cls) -> Dict[str, Any]:
        """Calculates total, today's, monthly, and category-wise revenue."""
        today = today_iso()
        current_month = today[:7] # YYYY-MM

        total_row = db.fetch_one("""
            SELECT COALESCE(SUM(amount), 0.0) as total 
            FROM payments 
            WHERE payment_status = 'Paid'
        """)

        today_row = db.fetch_one("""
            SELECT COALESCE(SUM(amount), 0.0) as total 
            FROM payments 
            WHERE payment_status = 'Paid' AND payment_date = ?
        """, (today,))

        month_row = db.fetch_one("""
            SELECT COALESCE(SUM(amount), 0.0) as total 
            FROM payments 
            WHERE payment_status = 'Paid' AND payment_date LIKE ?
        """, (f"{current_month}%",))

        by_category = db.fetch_all("""
            SELECT c.category, COALESCE(SUM(p.amount), 0.0) as revenue, COUNT(DISTINCT r.id) as rental_count
            FROM payments p
            JOIN rentals r ON p.rental_id = r.id
            JOIN cars c ON r.car_id = c.id
            WHERE p.payment_status = 'Paid'
            GROUP BY c.category
            ORDER BY revenue DESC
        """)

        by_car = db.fetch_all("""
            SELECT c.car_number, c.brand, c.model, COALESCE(SUM(p.amount), 0.0) as revenue, COUNT(DISTINCT r.id) as rental_count
            FROM payments p
            JOIN rentals r ON p.rental_id = r.id
            JOIN cars c ON r.car_id = c.id
            WHERE p.payment_status = 'Paid'
            GROUP BY c.id
            ORDER BY revenue DESC
            LIMIT 10
        """)

        return {
            "total_revenue": float(total_row["total"]) if total_row else 0.0,
            "today_revenue": float(today_row["total"]) if today_row else 0.0,
            "month_revenue": float(month_row["total"]) if month_row else 0.0,
            "by_category": [dict(r) for r in by_category],
            "by_car": [dict(r) for r in by_car]
        }
