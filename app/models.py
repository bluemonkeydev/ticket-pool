from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.db import get_db
from app import login_manager
import secrets
from datetime import datetime, timedelta

class User(UserMixin):
    def __init__(self, id, name, email, password_hash, is_admin=False, is_active=True, must_reset_password=True, reset_token=None, reset_token_expires=None, created_at=None):
        self.id = id
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.is_admin = bool(is_admin)
        self._is_active = bool(is_active)
        self.must_reset_password = bool(must_reset_password)
        self.reset_token = reset_token
        self.reset_token_expires = reset_token_expires
        self.created_at = created_at

    @property
    def is_active(self):
        return self._is_active

    @property
    def needs_password_setup(self):
        """Check if user needs to set up their password (no password hash)."""
        return not self.password_hash

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def create(name, email, is_admin=False):
        """Create a new user without a password - they must use password reset."""
        db = get_db()
        # Generate a reset token so they can set their password
        token = secrets.token_urlsafe(32)
        expires = datetime.now() + timedelta(days=7)  # Token valid for 7 days
        cursor = db.execute(
            '''INSERT INTO users (name, email, password_hash, is_admin, must_reset_password, reset_token, reset_token_expires)
               VALUES (?, ?, NULL, ?, 1, ?, ?)''',
            (name, email, is_admin, token, expires)
        )
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def generate_reset_token(user_id):
        """Generate a password reset token for an existing user."""
        db = get_db()
        token = secrets.token_urlsafe(32)
        expires = datetime.now() + timedelta(hours=24)  # Token valid for 24 hours
        db.execute(
            'UPDATE users SET reset_token = ?, reset_token_expires = ? WHERE id = ?',
            (token, expires, user_id)
        )
        db.commit()
        return token

    @staticmethod
    def get_by_reset_token(token):
        """Find a user by their reset token if it's still valid."""
        db = get_db()
        row = db.execute(
            'SELECT * FROM users WHERE reset_token = ? AND reset_token_expires > ?',
            (token, datetime.now())
        ).fetchone()
        if row:
            return User(**dict(row))
        return None

    @staticmethod
    def clear_reset_token(user_id):
        """Clear the reset token after password has been set."""
        db = get_db()
        db.execute(
            'UPDATE users SET reset_token = NULL, reset_token_expires = NULL WHERE id = ?',
            (user_id,)
        )
        db.commit()

    @staticmethod
    def get_by_id(user_id):
        db = get_db()
        row = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if row:
            return User(**dict(row))
        return None

    @staticmethod
    def get_by_email(email):
        db = get_db()
        row = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if row:
            return User(**dict(row))
        return None

    @staticmethod
    def get_all():
        db = get_db()
        rows = db.execute('SELECT * FROM users ORDER BY name').fetchall()
        return [User(**dict(row)) for row in rows]

    @staticmethod
    def get_all_active():
        db = get_db()
        rows = db.execute('SELECT * FROM users WHERE is_active = 1 ORDER BY name').fetchall()
        return [User(**dict(row)) for row in rows]

    @staticmethod
    def update(user_id, name=None, email=None, is_admin=None, is_active=None, password=None, must_reset_password=None):
        db = get_db()
        updates = []
        params = []

        if name is not None:
            updates.append('name = ?')
            params.append(name)
        if email is not None:
            updates.append('email = ?')
            params.append(email)
        if is_admin is not None:
            updates.append('is_admin = ?')
            params.append(is_admin)
        if is_active is not None:
            updates.append('is_active = ?')
            params.append(is_active)
        if password is not None:
            updates.append('password_hash = ?')
            params.append(generate_password_hash(password))
        if must_reset_password is not None:
            updates.append('must_reset_password = ?')
            params.append(must_reset_password)

        if updates:
            params.append(user_id)
            db.execute(f'UPDATE users SET {", ".join(updates)} WHERE id = ?', params)
            db.commit()


@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(int(user_id))


class Event:
    def __init__(self, id, name, event_date, total_tickets, notes, status, created_by, created_at, finalized_at=None):
        self.id = id
        self.name = name
        self.event_date = event_date
        self.total_tickets = total_tickets
        self.notes = notes
        self.status = status
        self.created_by = created_by
        self.created_at = created_at
        self.finalized_at = finalized_at

    @property
    def is_open(self):
        return self.status == 'open'

    @property
    def is_finalized(self):
        return self.status == 'finalized'

    def get_creator(self):
        return User.get_by_id(self.created_by)

    @staticmethod
    def create(name, event_date, total_tickets, created_by, notes=None):
        db = get_db()
        cursor = db.execute(
            'INSERT INTO events (name, event_date, total_tickets, notes, created_by) VALUES (?, ?, ?, ?, ?)',
            (name, event_date, total_tickets, notes, created_by)
        )
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def get_by_id(event_id):
        db = get_db()
        row = db.execute('SELECT * FROM events WHERE id = ?', (event_id,)).fetchone()
        if row:
            return Event(**dict(row))
        return None

    @staticmethod
    def get_all_open():
        db = get_db()
        rows = db.execute(
            'SELECT * FROM events WHERE status = ? ORDER BY event_date ASC',
            ('open',)
        ).fetchall()
        return [Event(**dict(row)) for row in rows]

    @staticmethod
    def get_all_past(limit=None):
        db = get_db()
        query = '''SELECT * FROM events
                   WHERE status IN ('finalized', 'cancelled')
                   ORDER BY event_date DESC'''
        if limit:
            query += f' LIMIT {limit}'
        rows = db.execute(query).fetchall()
        return [Event(**dict(row)) for row in rows]

    @staticmethod
    def get_past_events_within_months(months=24):
        """Get past events from the last N months."""
        db = get_db()
        rows = db.execute(
            '''SELECT * FROM events
               WHERE status IN ('finalized', 'cancelled')
               AND event_date >= date('now', ?)
               ORDER BY event_date DESC''',
            (f'-{months} months',)
        ).fetchall()
        return [Event(**dict(row)) for row in rows]

    @staticmethod
    def get_all():
        db = get_db()
        rows = db.execute('SELECT * FROM events ORDER BY event_date DESC').fetchall()
        return [Event(**dict(row)) for row in rows]

    @staticmethod
    def update(event_id, **kwargs):
        db = get_db()
        allowed = ['name', 'event_date', 'total_tickets', 'notes', 'status', 'finalized_at']
        updates = []
        params = []

        for key, value in kwargs.items():
            if key in allowed:
                updates.append(f'{key} = ?')
                params.append(value)

        if updates:
            params.append(event_id)
            db.execute(f'UPDATE events SET {", ".join(updates)} WHERE id = ?', params)
            db.commit()

    @staticmethod
    def delete(event_id):
        db = get_db()
        db.execute('DELETE FROM submissions WHERE event_id = ?', (event_id,))
        db.execute('DELETE FROM events WHERE id = ?', (event_id,))
        db.commit()


class Submission:
    def __init__(self, id, event_id, user_id, preferences, notes, allocated, submitted_at, updated_at, **kwargs):
        # **kwargs accepts and ignores any extra columns from old schema (ideal_tickets, min_tickets)
        self.id = id
        self.event_id = event_id
        self.user_id = user_id
        self.preferences = preferences  # Stored as comma-separated string: "4,2,1,0"
        self.notes = notes
        self.allocated = allocated
        self.submitted_at = submitted_at
        self.updated_at = updated_at

    @property
    def preferences_list(self):
        """Return preferences as a list of integers."""
        if not self.preferences:
            return []
        return [int(x) for x in self.preferences.split(',')]

    @property
    def first_choice(self):
        """Return the first (ideal) choice."""
        prefs = self.preferences_list
        return prefs[0] if prefs else 0

    @property
    def min_acceptable(self):
        """Return the minimum acceptable (last non-zero value)."""
        prefs = self.preferences_list
        non_zero = [p for p in prefs if p > 0]
        return min(non_zero) if non_zero else 0

    def get_user(self):
        return User.get_by_id(self.user_id)

    @staticmethod
    def create(event_id, user_id, preferences, notes=None):
        db = get_db()
        # preferences should be a list like [4, 2, 1, 0] - convert to string
        if isinstance(preferences, list):
            preferences = ','.join(str(p) for p in preferences)
        cursor = db.execute(
            '''INSERT INTO submissions (event_id, user_id, preferences, notes)
               VALUES (?, ?, ?, ?)''',
            (event_id, user_id, preferences, notes)
        )
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def get_by_id(submission_id):
        db = get_db()
        row = db.execute('SELECT * FROM submissions WHERE id = ?', (submission_id,)).fetchone()
        if row:
            return Submission(**dict(row))
        return None

    @staticmethod
    def get_by_event_and_user(event_id, user_id):
        db = get_db()
        row = db.execute(
            'SELECT * FROM submissions WHERE event_id = ? AND user_id = ?',
            (event_id, user_id)
        ).fetchone()
        if row:
            return Submission(**dict(row))
        return None

    @staticmethod
    def get_all_for_event(event_id):
        db = get_db()
        rows = db.execute(
            '''SELECT s.*, u.name as user_name
               FROM submissions s
               JOIN users u ON s.user_id = u.id
               WHERE s.event_id = ?
               ORDER BY u.name''',
            (event_id,)
        ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def update(submission_id, preferences=None, notes=None):
        db = get_db()
        updates = ['updated_at = CURRENT_TIMESTAMP']
        params = []

        if preferences is not None:
            if isinstance(preferences, list):
                preferences = ','.join(str(p) for p in preferences)
            updates.append('preferences = ?')
            params.append(preferences)
        if notes is not None:
            updates.append('notes = ?')
            params.append(notes)

        params.append(submission_id)
        db.execute(f'UPDATE submissions SET {", ".join(updates)} WHERE id = ?', params)
        db.commit()

    @staticmethod
    def update_allocation(submission_id, allocated):
        db = get_db()
        db.execute(
            'UPDATE submissions SET allocated = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (allocated, submission_id)
        )
        db.commit()

    @staticmethod
    def delete(submission_id):
        db = get_db()
        db.execute('DELETE FROM submissions WHERE id = ?', (submission_id,))
        db.commit()
