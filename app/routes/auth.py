from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app.forms import LoginForm
from app.email import send_magic_link_email

bp = Blueprint('auth', __name__)

@bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('events.dashboard'))
    return redirect(url_for('auth.login'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('events.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_email(form.email.data.lower())
        if user and user.is_active:
            token = User.generate_login_token(user.id)
            login_url = url_for('auth.verify_login', token=token, _external=True)
            send_magic_link_email(user, login_url)
        # Always show same message to not reveal if email exists
        flash('If an account exists with that email, a login link has been sent.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/login.html', form=form)


@bp.route('/verify/<token>')
def verify_login(token):
    if current_user.is_authenticated:
        return redirect(url_for('events.dashboard'))

    user = User.get_by_login_token(token)
    if not user:
        flash('Invalid or expired login link. Please request a new one.', 'error')
        return redirect(url_for('auth.login'))

    if not user.is_active:
        flash('Your account has been deactivated. Please contact an administrator.', 'error')
        return redirect(url_for('auth.login'))

    # Clear the token (single-use)
    User.clear_login_token(user.id)

    # Log the user in with remember=True for 1 year session
    login_user(user, remember=True)
    flash(f'Welcome, {user.name}!', 'success')

    next_page = request.args.get('next')
    return redirect(next_page or url_for('events.dashboard'))


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))
