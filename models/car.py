"""
Car Model
Manages vehicle inventory, search, filters, categorization, and status transitions.
"""

from typing import Optional, List, Dict, Any, Tuple
from database import db
from utils.helpers import logger

class Car:
    """Represents a vehicle in the rental fleet."""

    def __init__(
        self,
        id: int,
        car_number: str,
        brand: str,
        model: str,
        year: int,
        color: str,
        category: str,
        daily_rate: float,
        status: str = "Available",
        created_at: str = ""
    ):
        self.id = id
        self.car_number = car_number
        self.brand = brand
        self.model = model
        self.year = year
        self.color = color
        self.category = category
        self.daily_rate = float(daily_rate)
        self.status = status
        self.created_at = created_at

    def to_dict(self) -> Dict[str, Any]:
        """Converts car object to dictionary."""
        return {
            "id": self.id,
            "car_number": self.car_number,
            "brand": self.brand,
            "model": self.model,
            "year": self.year,
            "color": self.color,
            "category": self.category,
            "daily_rate": self.daily_rate,
            "status": self.status,
            "created_at": self.created_at
        }

    @classmethod
    def from_row(cls, row) -> "Car":
        """Creates Car object from sqlite3.Row."""
        return cls(
            id=row["id"],
            car_number=row["car_number"],
            brand=row["brand"],
            model=row["model"],
            year=row["year"],
            color=row["color"],
            category=row["category"],
            daily_rate=row["daily_rate"],
            status=row["status"],
            created_at=row["created_at"]
        )

    @classmethod
    def add_car(
        cls,
        car_number: str,
        brand: str,
        model: str,
        year: int,
        color: str,
        category: str,
        daily_rate: float,
        status: str = "Available"
    ) -> Tuple[bool, str, Optional[int]]:
        """Adds a new car to inventory with duplicate check."""
        try:
            clean_num = car_number.strip().upper()
            existing = cls.get_car_by_number(clean_num)
            if existing:
                return False, f"Car with registration number '{clean_num}' already exists.", None

            car_id = db.execute_query("""
                INSERT INTO cars (car_number, brand, model, year, color, category, daily_rate, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                clean_num,
                brand.strip(),
                model.strip(),
                int(year),
                color.strip(),
                category.strip(),
                float(daily_rate),
                status
            ))
            logger.info(f"Added new car {clean_num} (ID: {car_id}) to fleet.")
            return True, "Car added successfully.", car_id
        except Exception as e:
            logger.error(f"Error adding car: {e}")
            return False, f"Database error: {str(e)}", None

    @classmethod
    def update_car(
        cls,
        car_id: int,
        car_number: str,
        brand: str,
        model: str,
        year: int,
        color: str,
        category: str,
        daily_rate: float,
        status: str
    ) -> Tuple[bool, str]:
        """Updates car attributes."""
        try:
            clean_num = car_number.strip().upper()
            existing = cls.get_car_by_number(clean_num)
            if existing and existing.id != car_id:
                return False, f"Another car with registration number '{clean_num}' already exists."

            db.execute_query("""
                UPDATE cars
                SET car_number = ?, brand = ?, model = ?, year = ?, color = ?, category = ?, daily_rate = ?, status = ?
                WHERE id = ?
            """, (
                clean_num,
                brand.strip(),
                model.strip(),
                int(year),
                color.strip(),
                category.strip(),
                float(daily_rate),
                status,
                car_id
            ))
            logger.info(f"Updated car ID {car_id} ({clean_num}).")
            return True, "Car details updated successfully."
        except Exception as e:
            logger.error(f"Error updating car {car_id}: {e}")
            return False, f"Database error: {str(e)}"

    @classmethod
    def delete_car(cls, car_id: int) -> Tuple[bool, str]:
        """Safely deletes a car if not tied to active rentals."""
        try:
            # Check for active rentals
            active = db.fetch_one(
                "SELECT COUNT(*) as count FROM rentals WHERE car_id = ? AND status = 'Active'",
                (car_id,)
            )
            if active and active["count"] > 0:
                return False, "Cannot delete car: This vehicle is currently rented out in an active rental."

            # Check for past rental history
            history = db.fetch_one(
                "SELECT COUNT(*) as count FROM rentals WHERE car_id = ?",
                (car_id,)
            )
            if history and history["count"] > 0:
                # Instead of cascading delete that breaks financial history, mark as Maintenance/Decommissioned or delete if forced
                # Let's see if we should delete or notify
                try:
                    db.execute_query("DELETE FROM cars WHERE id = ?", (car_id,))
                    logger.info(f"Deleted car ID {car_id}.")
                    return True, "Car deleted successfully."
                except Exception:
                    return False, "Cannot delete car with existing rental records. Consider setting its status to 'Maintenance'."
            
            db.execute_query("DELETE FROM cars WHERE id = ?", (car_id,))
            logger.info(f"Deleted car ID {car_id}.")
            return True, "Car deleted successfully."
        except Exception as e:
            logger.error(f"Error deleting car ID {car_id}: {e}")
            return False, f"Database error: {str(e)}"

    @classmethod
    def get_car_by_id(cls, car_id: int) -> Optional["Car"]:
        """Fetches car by ID."""
        row = db.fetch_one("SELECT * FROM cars WHERE id = ?", (car_id,))
        return cls.from_row(row) if row else None

    @classmethod
    def get_car_by_number(cls, car_number: str) -> Optional["Car"]:
        """Fetches car by registration number."""
        row = db.fetch_one("SELECT * FROM cars WHERE UPPER(car_number) = ?", (car_number.strip().upper(),))
        return cls.from_row(row) if row else None

    @classmethod
    def update_status(cls, car_id: int, status: str) -> bool:
        """Updates car status."""
        try:
            db.execute_query("UPDATE cars SET status = ? WHERE id = ?", (status, car_id))
            logger.info(f"Car ID {car_id} status changed to '{status}'.")
            return True
        except Exception as e:
            logger.error(f"Failed to update car status: {e}")
            return False

    @classmethod
    def get_all_cars(
        cls,
        search_term: str = "",
        category: str = "All",
        status: str = "All"
    ) -> List["Car"]:
        """Fetches cars with parameterized search and category/status filtering."""
        query = "SELECT * FROM cars WHERE 1=1"
        params: List[Any] = []

        if search_term and search_term.strip():
            term = f"%{search_term.strip()}%"
            query += " AND (car_number LIKE ? OR brand LIKE ? OR model LIKE ? OR color LIKE ?)"
            params.extend([term, term, term, term])

        if category and category != "All":
            query += " AND category = ?"
            params.append(category)

        if status and status != "All":
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY brand ASC, model ASC"
        rows = db.fetch_all(query, tuple(params))
        return [cls.from_row(r) for r in rows]

    @classmethod
    def get_available_cars(
        cls,
        brand: str = "",
        category: str = "All",
        max_price: Optional[float] = None,
        model: str = "",
        search_term: str = ""
    ) -> List["Car"]:
        """Fetches only Available cars matching search and filter criteria."""
        query = "SELECT * FROM cars WHERE status = 'Available'"
        params: List[Any] = []

        if search_term and search_term.strip():
            term = f"%{search_term.strip()}%"
            query += " AND (car_number LIKE ? OR brand LIKE ? OR model LIKE ?)"
            params.extend([term, term, term])

        if brand and brand != "All" and brand.strip():
            query += " AND UPPER(brand) = ?"
            params.append(brand.strip().upper())

        if category and category != "All" and category.strip():
            query += " AND category = ?"
            params.append(category.strip())

        if model and model.strip():
            query += " AND model LIKE ?"
            params.append(f"%{model.strip()}%")

        if max_price is not None and max_price > 0:
            query += " AND daily_rate <= ?"
            params.append(float(max_price))

        query += " ORDER BY daily_rate ASC, brand ASC"
        rows = db.fetch_all(query, tuple(params))
        return [cls.from_row(r) for r in rows]

    @classmethod
    def get_car_statistics(cls) -> Dict[str, int]:
        """Calculates fleet breakdown counts."""
        rows = db.fetch_all("""
            SELECT status, COUNT(*) as count 
            FROM cars 
            GROUP BY status
        """)
        stats = {"Total": 0, "Available": 0, "Rented": 0, "Maintenance": 0}
        for r in rows:
            status = r["status"]
            count = r["count"]
            stats[status] = count
            stats["Total"] += count
        return stats
