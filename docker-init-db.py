#!/usr/bin/env python3
"""Initialize the database and create an admin user for Docker deployment."""

import os
import sys

# Set environment variable for database path if not set
if not os.environ.get('DATABASE'):
    os.environ['DATABASE'] = '/data/tickets.db'

from app import create_app
from app.db import init_db, get_db
from app.models import User

def main():
    if len(sys.argv) != 4:
        print("Usage: python docker-init-db.py <admin_email> <admin_name> <temp_password>")
        print("Example: python docker-init-db.py admin@company.com 'Admin User' temppass123")
        sys.exit(1)

    email = sys.argv[1]
    name = sys.argv[2]
    password = sys.argv[3]

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
            User.create(name=name, email=email.lower(), password=password, is_admin=True)
            print(f"Admin user created: {email}")
            print("Note: This user will need to set a new password on first login.")

if __name__ == '__main__':
    main()
