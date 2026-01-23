#!/usr/bin/env python3
"""Initialize the database and create an admin user."""

import sys
from app import create_app
from app.db import init_db, get_db
from app.models import User
from flask import url_for

def main():
    app = create_app()

    with app.app_context():
        # Initialize database schema
        print("Initializing database...")
        init_db()
        print("Database initialized successfully.")

        # Check if admin exists
        db = get_db()
        admin = db.execute("SELECT * FROM users WHERE is_admin = 1").fetchone()

        if admin:
            print(f"Admin user already exists: {admin['email']}")
        else:
            # Create admin user
            print("\nCreating admin user...")
            email = input("Admin email: ").strip()
            name = input("Admin name: ").strip()

            if not email or not name:
                print("Error: Email and name are required.")
                sys.exit(1)

            user_id = User.create(name=name, email=email.lower(), is_admin=True)
            user = User.get_by_id(user_id)
            print(f"\nAdmin user created: {email}")
            print(f"Password reset token: {user.reset_token}")
            print("Use this token to set your password at: /reset-password/<token>")

if __name__ == '__main__':
    main()
