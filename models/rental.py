"""
Rental Model
Manages rental transactions, return settlement, late fee calculation, and history.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple
from database import db
from utils.helpers import logger, today_iso

class Rental:
    """Represents a car rental contract / transaction."""

    def __init__(
        self,
        id: int,
        customer_id: int,
        car_id: int,
        rental_date: str,
        return_date: str,
        actual_return_date: Optional[str],
        rental_days: int,
        daily_rate: float,
        total_amount: float,
        security_deposit: float,
        status: str = "Active"
    ):
        self.id = id
        self.customer_id = customer_id
        self.car_id = car_id
        self.rental_date = rental_date
        self.return_date = return_date
        self.actual_return_date = actual_return_date
        self.rental_days = rental_days
        self.daily_rate = float(daily_rate)
        self.total_amount = float(total_amount)
        self.security_deposit = float(security_deposit)
        self.status = status

    @classmethod
    def create_rental(
        cls,
        customer_id: int,
        car_id: int,
        rental_date: str,
        return_date: str,
        rental_days: int,
        daily_rate: float,
        total_amount: float,
        security_deposit: float,
        payment_method: str = "Cash"
    ) -> Tuple[bool, str, Optional[int]]:
        """
        Atomically executes car rental booking in a single safe database transaction:
        1. Verifies car availability
        2. Inserts rental record
        3. Updates car status to 'Rented'
        4. Records initial payment (Rental Amount + Security Deposit)
        """
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()

                # 1. Verify car availability
                cursor.execute("SELECT status, car_number, brand, model FROM cars WHERE id = ?", (car_id,))
                car = cursor.fetchone()
                if not car:
                    return False, "Selected car does not exist.", None
                if car["status"] != "Available":
                    return False, f"Car {car['brand']} {car['model']} ({car['car_number']}) is currently not available for rental (Status: {car['status']}).", None

                # 2. Insert rental
                cursor.execute("""
                    INSERT INTO rentals (
                        customer_id, car_id, rental_date, return_date,
                        rental_days, daily_rate, total_amount, security_deposit, status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Active')
                """, (
                    customer_id,
                    car_id,
                    rental_date,
                    return_date,
                    int(rental_days),
                    float(daily_rate),
                    float(total_amount),
                    float(security_deposit)
                ))
                rental_id = cursor.lastrowid

                # 3. Update Car status
                cursor.execute("UPDATE cars SET status = 'Rented' WHERE id = ?", (car_id,))

                # 4. Insert Payment record
                grand_total = float(total_amount) + float(security_deposit)
                cursor.execute("""
                    INSERT INTO payments (
                        rental_id, customer_id, amount, payment_method, payment_date, payment_status
                    )
                    VALUES (?, ?, ?, ?, ?, 'Paid')
                """, (
                    rental_id,
                    customer_id,
                    grand_total,
                    payment_method,
                    rental_date
                ))

                logger.info(f"Rental created ID #{rental_id} for Customer #{customer_id} on Car #{car_id}. Amount: {grand_total}")
                return True, "Rental booked successfully!", rental_id

        except Exception as e:
            logger.error(f"Rental transaction failed and was rolled back: {e}")
            return False, f"Rental failed: {str(e)}", None

    @classmethod
    def process_return(
        cls,
        rental_id: int,
        actual_return_date: Optional[str] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Processes vehicle return in an atomic transaction:
        1. Checks rental status
        2. Calculates late days & penalty charges
        3. Updates rental status to 'Completed'
        4. Updates car status to 'Available'
        5. Records additional late payment if applicable
        """
        calc_result: Dict[str, Any] = {}
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()

                # Fetch full rental details
                cursor.execute("""
                    SELECT r.*, c.car_number, c.brand, c.model, cust.full_name, cust.cnic, cust.phone
                    FROM rentals r
                    JOIN cars c ON r.car_id = c.id
                    JOIN customers cust ON r.customer_id = cust.id
                    WHERE r.id = ?
                """, (rental_id,))
                rental = cursor.fetchone()

                if not rental:
                    return False, "Rental record not found.", {}

                if rental["status"] != "Active":
                    return False, f"Rental #{rental_id} is already marked as {rental['status']}.", {}

                # Calculate dates and late penalty
                actual_date_str = actual_return_date or today_iso()
                actual_dt = datetime.strptime(actual_date_str, "%Y-%m-%d").date()
                expected_dt = datetime.strptime(rental["return_date"], "%Y-%m-%d").date()

                late_days = max(0, (actual_dt - expected_dt).days)
                daily_rate = float(rental["daily_rate"])
                late_charges = float(late_days * daily_rate)
                original_rental_amount = float(rental["total_amount"])
                security_deposit = float(rental["security_deposit"])
                
                # Final financial calculation
                final_total = original_rental_amount + late_charges

                # Update rental record
                cursor.execute("""
                    UPDATE rentals
                    SET actual_return_date = ?, status = 'Completed'
                    WHERE id = ?
                """, (actual_date_str, rental_id))

                # Update car status to Available
                cursor.execute("UPDATE cars SET status = 'Available' WHERE id = ?", (rental["car_id"],))

                # If late penalty applies, record penalty payment
                if late_charges > 0:
                    cursor.execute("""
                        INSERT INTO payments (rental_id, customer_id, amount, payment_method, payment_date, payment_status)
                        VALUES (?, ?, ?, 'Cash', ?, 'Paid')
                    """, (rental_id, rental["customer_id"], late_charges, actual_date_str))

                calc_result = {
                    "rental_id": rental_id,
                    "customer_name": rental["full_name"],
                    "customer_cnic": rental["cnic"],
                    "customer_phone": rental["phone"],
                    "car_number": rental["car_number"],
                    "car_brand": rental["brand"],
                    "car_model": rental["model"],
                    "rental_date": rental["rental_date"],
                    "expected_return_date": rental["return_date"],
                    "actual_return_date": actual_date_str,
                    "rental_days": rental["rental_days"],
                    "daily_rate": daily_rate,
                    "original_rental_amount": original_rental_amount,
                    "security_deposit": security_deposit,
                    "late_days": late_days,
                    "late_charges": late_charges,
                    "final_total": final_total
                }

                logger.info(f"Rental #{rental_id} returned. Late days: {late_days}, Late fee: {late_charges}")
                return True, "Vehicle returned and processed successfully.", calc_result

        except Exception as e:
            logger.error(f"Return processing transaction failed: {e}")
            return False, f"Failed to process return: {str(e)}", {}

    @classmethod
    def get_rental_by_id(cls, rental_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves full details for a rental ID."""
        row = db.fetch_one("""
            SELECT r.*, 
                   c.car_number, c.brand, c.model, c.category, c.color,
                   cust.full_name as customer_name, cust.cnic as customer_cnic, cust.phone as customer_phone, cust.email as customer_email
            FROM rentals r
            JOIN cars c ON r.car_id = c.id
            JOIN customers cust ON r.customer_id = cust.id
            WHERE r.id = ?
        """, (rental_id,))
        return dict(row) if row else None

    @classmethod
    def get_all_rentals(cls, status: str = "All", search_term: str = "") -> List[Dict[str, Any]]:
        """Retrieves all rentals with search and status filtering."""
        query = """
            SELECT r.*, 
                   c.car_number, c.brand, c.model, c.category,
                   cust.full_name as customer_name, cust.cnic as customer_cnic, cust.phone as customer_phone
            FROM rentals r
            JOIN cars c ON r.car_id = c.id
            JOIN customers cust ON r.customer_id = cust.id
            WHERE 1=1
        """
        params: List[Any] = []

        if status and status != "All":
            query += " AND r.status = ?"
            params.append(status)

        if search_term and search_term.strip():
            term = f"%{search_term.strip()}%"
            query += """ AND (
                r.id LIKE ? OR 
                c.car_number LIKE ? OR 
                c.brand LIKE ? OR 
                c.model LIKE ? OR 
                cust.full_name LIKE ? OR 
                cust.cnic LIKE ?
            )"""
            params.extend([term, term, term, term, term, term])

        query += " ORDER BY r.id DESC"
        rows = db.fetch_all(query, tuple(params))
        return [dict(r) for r in rows]

    @classmethod
    def get_customer_rentals(cls, customer_id: int) -> List[Dict[str, Any]]:
        """Retrieves rental history for a specific customer."""
        rows = db.fetch_all("""
            SELECT r.*, 
                   c.car_number, c.brand, c.model, c.category, c.color
            FROM rentals r
            JOIN cars c ON r.car_id = c.id
            WHERE r.customer_id = ?
            ORDER BY r.id DESC
        """, (customer_id,))
        return [dict(r) for r in rows]

    @classmethod
    def search_active_rentals(cls, search_term: str = "") -> List[Dict[str, Any]]:
        """Search specifically for active rentals to process returns."""
        query = """
            SELECT r.*, 
                   c.car_number, c.brand, c.model,
                   cust.full_name as customer_name, cust.cnic as customer_cnic, cust.phone as customer_phone
            FROM rentals r
            JOIN cars c ON r.car_id = c.id
            JOIN customers cust ON r.customer_id = cust.id
            WHERE r.status = 'Active'
        """
        params: List[Any] = []

        if search_term and search_term.strip():
            term = f"%{search_term.strip()}%"
            query += """ AND (
                r.id LIKE ? OR 
                c.car_number LIKE ? OR 
                cust.cnic LIKE ? OR 
                cust.full_name LIKE ?
            )"""
            params.extend([term, term, term, term])

        query += " ORDER BY r.return_date ASC"
        rows = db.fetch_all(query, tuple(params))
        return [dict(r) for r in rows]

    @classmethod
    def get_rental_statistics(cls) -> Dict[str, int]:
        """Calculates rental breakdown counts."""
        rows = db.fetch_all("""
            SELECT status, COUNT(*) as count 
            FROM rentals 
            GROUP BY status
        """)
        stats = {"Total": 0, "Active": 0, "Completed": 0, "Cancelled": 0}
        for r in rows:
            status = r["status"]
            count = r["count"]
            stats[status] = count
            stats["Total"] += count
        return stats
