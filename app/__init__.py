from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import Config
from datetime import datetime

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    login_manager.init_app(app)
    csrf.init_app(app)

    from app import db
    db.init_app(app)

    from app.routes import auth, events, admin
    app.register_blueprint(auth.bp)
    app.register_blueprint(events.bp)
    app.register_blueprint(admin.bp)

    # Custom Jinja filters for datetime formatting
    def format_12hour(dt):
        """Format time in 12-hour format without leading zero."""
        hour = dt.hour % 12
        if hour == 0:
            hour = 12
        minute = dt.strftime('%M')
        ampm = 'AM' if dt.hour < 12 else 'PM'
        return f'{hour}:{minute} {ampm}'

    @app.template_filter('datetime')
    def format_datetime(value):
        """Format datetime as 'Mon Jan 15, 2024 at 7:30 PM'"""
        if value is None:
            return ''
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                return value
        date_part = value.strftime('%a %b %d, %Y')
        time_part = format_12hour(value)
        return f'{date_part} at {time_part}'

    @app.template_filter('datetime_short')
    def format_datetime_short(value):
        """Format datetime as 'Jan 15 at 7:30 PM'"""
        if value is None:
            return ''
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                return value
        date_part = value.strftime('%b %d')
        time_part = format_12hour(value)
        return f'{date_part} at {time_part}'

    return app
