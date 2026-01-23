from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app.forms import LoginForm, ChangePasswordForm, PasswordResetRequestForm, PasswordResetForm
from app.email import send_password_reset_email

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
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact an administrator.', 'error')
                return render_template('auth/login.html', form=form)
            login_user(user, remember=form.remember_me.data)
            # Check if user needs to reset password (first login)
            if user.must_reset_password:
                flash('Please set a new password to continue.', 'info')
                return redirect(url_for('auth.change_password'))
            next_page = request.args.get('next')
            return redirect(next_page or url_for('events.dashboard'))
        flash('Invalid email or password.', 'error')
    return render_template('auth/login.html', form=form)


@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('events.dashboard'))

    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.get_by_email(form.email.data.lower())
        if user:
            token = User.generate_reset_token(user.id)
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            send_password_reset_email(user, reset_url)
        # Always show same message to not reveal if email exists
        flash('If an account exists with that email, a password reset link has been sent.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html', form=form)


@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('events.dashboard'))

    user = User.get_by_reset_token(token)
    if not user:
        flash('Invalid or expired reset link.', 'error')
        return redirect(url_for('auth.forgot_password'))

    form = PasswordResetForm()
    if form.validate_on_submit():
        User.update(user.id, password=form.password.data, must_reset_password=False)
        User.clear_reset_token(user.id)
        flash('Your password has been set. You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))

@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    # If must reset, don't require current password
    require_current = not current_user.must_reset_password

    if form.validate_on_submit():
        if require_current and not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'error')
            return render_template('auth/change_password.html', form=form, require_current=require_current)

        User.update(current_user.id, password=form.new_password.data, must_reset_password=False)
        flash('Password changed successfully.', 'success')
        return redirect(url_for('events.dashboard'))

    return render_template('auth/change_password.html', form=form, require_current=require_current)
