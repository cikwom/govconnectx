"""Create the first system administrator using an interactive local command.

Run from backend/: python -m scripts.create_system_admin
"""
import re
from getpass import getpass

from app.core.security import hash_password
from app.database import Base, SessionLocal, engine
from app.models import Report, User  # noqa: F401


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).filter(User.role == "system_admin").count():
            raise SystemExit("A system administrator already exists. Use an authenticated admin account to manage roles.")

        email = input("Administrator email: ").strip().lower()
        full_name = " ".join(input("Administrator full name: ").split())
        password = getpass("Password (minimum 12 characters): ")
        confirmation = getpass("Confirm password: ")

        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            raise SystemExit("Enter a valid email address.")
        if len(full_name) < 2:
            raise SystemExit("Enter a full name with at least 2 characters.")
        if len(password) < 12:
            raise SystemExit("Use a password with at least 12 characters.")
        if password != confirmation:
            raise SystemExit("Passwords do not match.")
        if db.query(User).filter(User.email == email).first():
            raise SystemExit("An account with that email already exists.")

        admin = User(
            email=email,
            full_name=full_name,
            password_hash=hash_password(password),
            role="system_admin",
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print("System administrator created successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
