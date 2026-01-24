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
    if len(sys.argv) != 3:
        print("Usage: python docker-init-db.py <admin_email> <admin_name>")
        print("Example: python docker-init-db.py admin@company.com 'Admin User'")
        sys.exit(1)

    email = sys.argv[1]
    name = sys.argv[2]

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
            User.create(name=name, email=email.lower(), is_admin=True)
            print(f"Admin user created: {email}")
            print("Login via magic link sent to this email.")

if __name__ == '__main__':
    main()
