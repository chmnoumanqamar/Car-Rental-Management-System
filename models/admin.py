"""
Admin Model
Manages Administrator entities, authentication, and admin account updates.
"""

from typing import Optional, List, Dict, Any
from database import db
from utils.security import hash_password, verify_password
from utils.helpers import logger

class Admin:
    """Represents a system administrator entity."""

    def __init__(
        self,
        id: int,
        username: str,
        full_name: str,
        email: str,
        created_at: str = ""
    ):
        self.id = id
        self.username = username
        self.full_name = full_name
        self.email = email
        self.created_at = created_at

    @classmethod
    def authenticate(cls, username: str, password_plain: str) -> Optional["Admin"]:
        """Authenticates admin credentials safely using password hashing."""
        if not username or not password_plain:
            return None
        
        row = db.fetch_one(
            "SELECT * FROM admins WHERE username = ?",
            (username.strip(),)
        )
        if not row:
            logger.warning(f"Admin login failed: username '{username}' not found.")
            return None
        
        if verify_password(row["password"], password_plain):
            logger.info(f"Admin '{username}' logged in successfully.")
            return cls(
                id=row["id"],
                username=row["username"],
                full_name=row["full_name"],
                email=row["email"],
                created_at=row["created_at"]
            )
        else:
            logger.warning(f"Admin login failed: Invalid password for username '{username}'.")
            return None

    @classmethod
    def get_by_id(cls, admin_id: int) -> Optional["Admin"]:
        """Retrieves admin by ID."""
        row = db.fetch_one("SELECT * FROM admins WHERE id = ?", (admin_id,))
        if row:
            return cls(
                id=row["id"],
                username=row["username"],
                full_name=row["full_name"],
                email=row["email"],
                created_at=row["created_at"]
            )
        return None

    @classmethod
    def update_profile(
        cls,
        admin_id: int,
        full_name: str,
        email: str,
        new_password: Optional[str] = None
    ) -> bool:
        """Updates admin name, email, and optionally changes password."""
        try:
            if new_password and new_password.strip():
                pw_hash = hash_password(new_password.strip())
                db.execute_query(
                    "UPDATE admins SET full_name = ?, email = ?, password = ? WHERE id = ?",
                    (full_name.strip(), email.strip(), pw_hash, admin_id)
                )
            else:
                db.execute_query(
                    "UPDATE admins SET full_name = ?, email = ? WHERE id = ?",
                    (full_name.strip(), email.strip(), admin_id)
                )
            logger.info(f"Admin ID {admin_id} profile updated.")
            return True
        except Exception as e:
            logger.error(f"Error updating admin profile: {e}")
            return False
