# Ticket Allocation App

A web application for managing event ticket requests and allocations. Administrators can create events, and users can submit ticket requests with tiered preferences. The system helps fairly distribute limited tickets among requesters.

## Features

- **Event Management**: Create, edit, and manage events with configurable ticket quantities
- **Tiered Ticket Requests**: Users submit preferences (e.g., "I'd like 4 tickets, but would accept 2 or 1")
- **Allocation Workflow**: Admins can review requests and allocate tickets before finalizing
- **User Management**: Admin panel for managing users, roles, and account status
- **Email Notifications**: Optional AWS SES integration for password reset and welcome emails
- **Event History**: View all active and past events with statistics

## Tech Stack

- **Backend**: Python 3.11, Flask 3.0
- **Database**: SQLite
- **Authentication**: Flask-Login with secure password hashing
- **Forms**: Flask-WTF with CSRF protection
- **Email**: AWS SES (optional)
- **Deployment**: Docker with Gunicorn

## Quick Start

### Using Docker (Recommended)

1. **Build and run**:
   ```bash
   docker compose up --build
   ```

2. **Initialize the database** (in a separate terminal):
   ```bash
   docker compose exec web python init_db.py
   ```
   Follow the prompts to create an admin user.

3. **Access the app** at http://localhost:5000

### Local Development

1. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database**:
   ```bash
   python init_db.py
   ```

4. **Run the development server**:
   ```bash
   python run.py
   ```

5. **Access the app** at http://localhost:5000

## Configuration

Configure the app using environment variables or a `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key for sessions | `dev-secret-key...` |
| `DATABASE` | Path to SQLite database file | `./tickets.db` |
| `APP_NAME` | Application display name | `Ticket Allocation` |
| `APP_URL` | Base URL for email links | `http://localhost:5000` |
| `MAIL_ENABLED` | Enable email sending | `false` |
| `AWS_REGION` | AWS region for SES | `us-east-1` |
| `AWS_ACCESS_KEY_ID` | AWS access key | - |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | - |
| `SES_SENDER_EMAIL` | Verified SES sender email | `noreply@example.com` |

### Example `.env` file

```env
SECRET_KEY=your-secure-secret-key-here
APP_NAME=Company Ticket Allocation
APP_URL=https://tickets.yourcompany.com
MAIL_ENABLED=true
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
SES_SENDER_EMAIL=tickets@yourcompany.com
```

## Usage

### For Administrators

1. **Create an Event**: Set the event name, date, total available tickets, and optional notes
2. **Share with Users**: Users can view open events and submit ticket requests
3. **Review Requests**: See all submissions with user preferences
4. **Allocate Tickets**: Assign tickets to each user (can be any amount)
5. **Finalize**: Lock the event and notify users of their allocations

### For Users

1. **View Open Events**: See all events currently accepting requests
2. **Submit Request**: Enter tiered preferences (e.g., ideally 4, but would accept 2 or 1)
3. **Add Notes**: Optionally explain your request
4. **Check Status**: View your allocation once the event is finalized

## Docker Commands

```bash
# Start the app
docker compose up -d --build

# View logs
docker compose logs -f

# Stop the app
docker compose down

# Run database initialization
docker compose exec web python init_db.py

# Access the container shell
docker compose exec web /bin/bash
```

## Project Structure

```
.
├── app/
│   ├── routes/          # Flask blueprints (auth, events, admin)
│   ├── templates/       # Jinja2 HTML templates
│   ├── static/          # CSS and static assets
│   ├── models.py        # User, Event, Submission models
│   ├── forms.py         # WTForms form definitions
│   ├── email.py         # AWS SES email utilities
│   ├── db.py            # Database connection handling
│   └── schema.sql       # SQLite schema
├── config.py            # Configuration class
├── run.py               # Application entry point
├── init_db.py           # Database initialization script
├── docker-compose.yml   # Docker Compose configuration
├── Dockerfile           # Docker image definition
└── requirements.txt     # Python dependencies
```

## License

Private/Internal Use
