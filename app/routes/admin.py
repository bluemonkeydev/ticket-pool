from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from app.models import User, Event
from app.forms import UserForm, AdminCreateUserForm
from app.email import send_welcome_email

bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.', 'error')
            return redirect(url_for('events.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
@admin_required
def index():
    users = User.get_all()
    events = Event.get_all()
    return render_template('admin/index.html', users=users, events=events)

@bp.route('/users')
@login_required
@admin_required
def users():
    users = User.get_all()
    return render_template('admin/users.html', users=users)

@bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    form = AdminCreateUserForm()
    if form.validate_on_submit():
        existing = User.get_by_email(form.email.data.lower())
        if existing:
            flash('Email already registered.', 'error')
            return render_template('admin/add_user.html', form=form)

        user_id = User.create(
            name=form.name.data,
            email=form.email.data.lower(),
            is_admin=form.is_admin.data
        )
        user = User.get_by_id(user_id)
        reset_url = url_for('auth.reset_password', token=user.reset_token, _external=True)
        send_welcome_email(user, reset_url)
        flash('User created successfully. A welcome email has been sent with instructions to set their password.', 'success')
        return redirect(url_for('admin.users'))
    return render_template('admin/add_user.html', form=form)

@bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.get_by_id(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('admin.users'))

    form = UserForm()

    if request.method == 'GET':
        form.name.data = user.name
        form.email.data = user.email
        form.is_admin.data = user.is_admin
        form.is_active.data = user.is_active

    if form.validate_on_submit():
        # Check if email is taken by another user
        existing = User.get_by_email(form.email.data.lower())
        if existing and existing.id != user_id:
            flash('Email already in use by another user.', 'error')
            return render_template('admin/edit_user.html', form=form, user=user)

        update_kwargs = {
            'name': form.name.data,
            'email': form.email.data.lower(),
            'is_admin': form.is_admin.data,
            'is_active': form.is_active.data
        }

        if form.password.data:
            update_kwargs['password'] = form.password.data

        User.update(user_id, **update_kwargs)
        flash('User updated successfully.', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/edit_user.html', form=form, user=user)

@bp.route('/users/<int:user_id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def toggle_user_active(user_id):
    user = User.get_by_id(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('admin.users'))

    if user.id == current_user.id:
        flash('You cannot deactivate yourself.', 'error')
        return redirect(url_for('admin.users'))

    User.update(user_id, is_active=not user.is_active)
    status = 'activated' if not user.is_active else 'deactivated'
    flash(f'User {status} successfully.', 'success')
    return redirect(url_for('admin.users'))

@bp.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def toggle_user_admin(user_id):
    user = User.get_by_id(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('admin.users'))

    if user.id == current_user.id:
        flash('You cannot remove your own admin rights.', 'error')
        return redirect(url_for('admin.users'))

    User.update(user_id, is_admin=not user.is_admin)
    status = 'granted admin rights' if not user.is_admin else 'removed admin rights'
    flash(f'User {status}.', 'success')
    return redirect(url_for('admin.users'))

@bp.route('/events/<int:event_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_event(event_id):
    event = Event.get_by_id(event_id)
    if not event:
        flash('Event not found.', 'error')
        return redirect(url_for('admin.index'))

    Event.delete(event_id)
    flash('Event deleted successfully.', 'success')
    return redirect(url_for('admin.index'))
