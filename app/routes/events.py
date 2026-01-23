from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app.models import Event, Submission, User
from app.forms import EventForm, SubmissionForm, CreatorSubmissionForm

bp = Blueprint('events', __name__)

def parse_preferences(pref_string):
    """Parse comma-separated preferences string into list of ints."""
    if not pref_string:
        return []
    return [int(x) for x in pref_string.split(',')]

def get_first_choice(pref_string):
    """Get first (ideal) choice from preferences string."""
    prefs = parse_preferences(pref_string)
    return prefs[0] if prefs else 0

def get_min_acceptable(pref_string):
    """Get minimum acceptable (smallest non-zero) from preferences string."""
    prefs = parse_preferences(pref_string)
    non_zero = [p for p in prefs if p > 0]
    return min(non_zero) if non_zero else 0

@bp.route('/dashboard')
@login_required
def dashboard():
    open_events = Event.get_all_open()
    past_events = Event.get_all_past()

    # Build a dict of creator info and stats for all events
    creators = {}
    event_stats = {}
    user_submissions = {}

    for event in open_events + past_events:
        # Creator info
        if event.created_by not in creators:
            creator = User.get_by_id(event.created_by)
            creators[event.created_by] = creator.name if creator else 'Unknown'

        # Event stats
        submissions = Submission.get_all_for_event(event.id)
        total_requested = sum(get_first_choice(s['preferences']) for s in submissions)
        event_stats[event.id] = {
            'submission_count': len(submissions),
            'total_requested': total_requested
        }

        # Check if current user has submitted
        user_sub = Submission.get_by_event_and_user(event.id, current_user.id)
        user_submissions[event.id] = user_sub is not None

    return render_template('events/dashboard.html',
                           open_events=open_events,
                           past_events=past_events,
                           creators=creators,
                           event_stats=event_stats,
                           user_submissions=user_submissions)

@bp.route('/events/create', methods=['GET', 'POST'])
@login_required
def create_event():
    form = EventForm()
    if form.validate_on_submit():
        Event.create(
            name=form.name.data,
            event_date=form.event_date.data,
            total_tickets=form.total_tickets.data,
            notes=form.notes.data,
            created_by=current_user.id
        )
        flash('Event created successfully!', 'success')
        return redirect(url_for('events.dashboard'))
    return render_template('events/create.html', form=form)

@bp.route('/events/<int:event_id>')
@login_required
def event_detail(event_id):
    event = Event.get_by_id(event_id)
    if not event:
        flash('Event not found.', 'error')
        return redirect(url_for('events.dashboard'))

    submissions = Submission.get_all_for_event(event_id)
    user_submission = Submission.get_by_event_and_user(event_id, current_user.id)
    creator = event.get_creator()

    # Calculate stats using new preferences format
    total_first_choice = sum(get_first_choice(s['preferences']) for s in submissions)
    total_min = sum(get_min_acceptable(s['preferences']) for s in submissions)
    total_allocated = sum(s['allocated'] or 0 for s in submissions)

    return render_template('events/detail.html',
                           event=event,
                           submissions=submissions,
                           user_submission=user_submission,
                           creator=creator,
                           total_first_choice=total_first_choice,
                           total_min=total_min,
                           total_allocated=total_allocated,
                           parse_preferences=parse_preferences,
                           get_first_choice=get_first_choice,
                           get_min_acceptable=get_min_acceptable)

@bp.route('/events/<int:event_id>/submit', methods=['GET', 'POST'])
@login_required
def submit_interest(event_id):
    event = Event.get_by_id(event_id)
    if not event:
        flash('Event not found.', 'error')
        return redirect(url_for('events.dashboard'))

    if not event.is_open:
        flash('This event is no longer accepting submissions.', 'error')
        return redirect(url_for('events.event_detail', event_id=event_id))

    existing = Submission.get_by_event_and_user(event_id, current_user.id)
    form = SubmissionForm()

    if existing:
        if request.method == 'GET':
            form.preferences.data = existing.preferences
            form.notes.data = existing.notes

    if form.validate_on_submit():
        if existing:
            Submission.update(
                existing.id,
                preferences=form.preferences.data,
                notes=form.notes.data
            )
            flash('Your submission has been updated.', 'success')
        else:
            Submission.create(
                event_id=event_id,
                user_id=current_user.id,
                preferences=form.preferences.data,
                notes=form.notes.data
            )
            flash('Your interest has been submitted.', 'success')
        return redirect(url_for('events.event_detail', event_id=event_id))

    return render_template('events/submit.html', event=event, form=form, existing=existing)

@bp.route('/events/<int:event_id>/withdraw', methods=['POST'])
@login_required
def withdraw_interest(event_id):
    event = Event.get_by_id(event_id)
    if not event or not event.is_open:
        flash('Cannot withdraw from this event.', 'error')
        return redirect(url_for('events.dashboard'))

    submission = Submission.get_by_event_and_user(event_id, current_user.id)
    if submission:
        Submission.delete(submission.id)
        flash('Your submission has been withdrawn.', 'success')
    return redirect(url_for('events.event_detail', event_id=event_id))

@bp.route('/events/<int:event_id>/allocate', methods=['GET', 'POST'])
@login_required
def allocate(event_id):
    event = Event.get_by_id(event_id)
    if not event:
        flash('Event not found.', 'error')
        return redirect(url_for('events.dashboard'))

    if event.created_by != current_user.id and not current_user.is_admin:
        flash('Only the event creator can allocate tickets.', 'error')
        return redirect(url_for('events.event_detail', event_id=event_id))

    if event.is_finalized:
        flash('This event has already been finalized.', 'error')
        return redirect(url_for('events.event_detail', event_id=event_id))

    submissions = Submission.get_all_for_event(event_id)

    if request.method == 'POST':
        action = request.form.get('action')

        # Save allocations
        for sub in submissions:
            allocated = request.form.get(f'allocated_{sub["id"]}', '0')
            try:
                allocated = int(allocated) if allocated else 0
            except ValueError:
                allocated = 0
            Submission.update_allocation(sub['id'], allocated)

        if action == 'finalize':
            Event.update(event_id, status='finalized', finalized_at=datetime.now())
            flash('Allocations have been finalized.', 'success')
            return redirect(url_for('events.event_detail', event_id=event_id))
        else:
            flash('Draft saved.', 'success')
            return redirect(url_for('events.allocate', event_id=event_id))

    # Refresh submissions after potential save
    submissions = Submission.get_all_for_event(event_id)
    total_first_choice = sum(get_first_choice(s['preferences']) for s in submissions)
    total_min = sum(get_min_acceptable(s['preferences']) for s in submissions)
    total_allocated = sum(s['allocated'] or 0 for s in submissions)

    return render_template('events/allocate.html',
                           event=event,
                           submissions=submissions,
                           total_first_choice=total_first_choice,
                           total_min=total_min,
                           total_allocated=total_allocated,
                           parse_preferences=parse_preferences,
                           get_first_choice=get_first_choice,
                           get_min_acceptable=get_min_acceptable)

@bp.route('/events/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = Event.get_by_id(event_id)
    if not event:
        flash('Event not found.', 'error')
        return redirect(url_for('events.dashboard'))

    if event.created_by != current_user.id and not current_user.is_admin:
        flash('You do not have permission to edit this event.', 'error')
        return redirect(url_for('events.event_detail', event_id=event_id))

    if event.is_finalized:
        flash('Cannot edit a finalized event.', 'error')
        return redirect(url_for('events.event_detail', event_id=event_id))

    form = EventForm()

    if request.method == 'GET':
        form.name.data = event.name
        form.event_date.data = event.event_date if isinstance(event.event_date, datetime) else datetime.fromisoformat(event.event_date)
        form.total_tickets.data = event.total_tickets
        form.notes.data = event.notes

    if form.validate_on_submit():
        Event.update(
            event_id,
            name=form.name.data,
            event_date=form.event_date.data,
            total_tickets=form.total_tickets.data,
            notes=form.notes.data
        )
        flash('Event updated successfully.', 'success')
        return redirect(url_for('events.event_detail', event_id=event_id))

    return render_template('events/edit.html', event=event, form=form)

@bp.route('/events/<int:event_id>/cancel', methods=['POST'])
@login_required
def cancel_event(event_id):
    event = Event.get_by_id(event_id)
    if not event:
        flash('Event not found.', 'error')
        return redirect(url_for('events.dashboard'))

    if event.created_by != current_user.id and not current_user.is_admin:
        flash('You do not have permission to cancel this event.', 'error')
        return redirect(url_for('events.event_detail', event_id=event_id))

    Event.update(event_id, status='cancelled')
    flash('Event has been cancelled.', 'success')
    return redirect(url_for('events.dashboard'))

@bp.route('/events/<int:event_id>/unfinalize', methods=['POST'])
@login_required
def unfinalize_event(event_id):
    event = Event.get_by_id(event_id)
    if not event:
        flash('Event not found.', 'error')
        return redirect(url_for('events.dashboard'))

    if event.created_by != current_user.id and not current_user.is_admin:
        flash('You do not have permission to un-finalize this event.', 'error')
        return redirect(url_for('events.event_detail', event_id=event_id))

    if not event.is_finalized:
        flash('This event is not finalized.', 'error')
        return redirect(url_for('events.event_detail', event_id=event_id))

    Event.update(event_id, status='open', finalized_at=None)
    flash('Event has been un-finalized. You can now make adjustments.', 'success')
    return redirect(url_for('events.allocate', event_id=event_id))

@bp.route('/events/<int:event_id>/submit-for-user', methods=['GET', 'POST'])
@login_required
def submit_for_user(event_id):
    """Allow event creator to submit interest on behalf of any user."""
    event = Event.get_by_id(event_id)
    if not event:
        flash('Event not found.', 'error')
        return redirect(url_for('events.dashboard'))

    # Only event creator can submit for others
    if event.created_by != current_user.id:
        flash('Only the event creator can submit on behalf of others.', 'error')
        return redirect(url_for('events.event_detail', event_id=event_id))

    if not event.is_open:
        flash('This event is no longer accepting submissions.', 'error')
        return redirect(url_for('events.event_detail', event_id=event_id))

    # Get all active users for the dropdown
    all_users = User.get_all_active()

    # Get users who already have submissions
    existing_submissions = Submission.get_all_for_event(event_id)
    users_with_submissions = {s['user_id'] for s in existing_submissions}

    # Filter to users without submissions
    available_users = [u for u in all_users if u.id not in users_with_submissions]

    form = CreatorSubmissionForm()
    form.user_id.choices = [(u.id, u.name) for u in available_users]

    if not available_users:
        flash('All users have already submitted their interest.', 'info')
        return redirect(url_for('events.event_detail', event_id=event_id))

    if form.validate_on_submit():
        Submission.create(
            event_id=event_id,
            user_id=form.user_id.data,
            preferences=form.preferences.data,
            notes=form.notes.data
        )
        user = User.get_by_id(form.user_id.data)
        flash(f'Interest submitted for {user.name}.', 'success')
        return redirect(url_for('events.event_detail', event_id=event_id))

    return render_template('events/submit_for_user.html', event=event, form=form)
