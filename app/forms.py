from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, IntegerField, TextAreaField, DateTimeLocalField, SelectField, HiddenField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, ValidationError

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])

class AdminCreateUserForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    is_admin = BooleanField('Administrator')

class UserForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    is_admin = BooleanField('Administrator')
    is_active = BooleanField('Active')

class EventForm(FlaskForm):
    name = StringField('Event Name', validators=[DataRequired(), Length(min=2, max=200)])
    event_date = DateTimeLocalField('Event Date & Time', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')
    total_tickets = IntegerField('Total Tickets Available', validators=[DataRequired(), NumberRange(min=1)])
    notes = TextAreaField('Notes (optional)', validators=[Optional(), Length(max=1000)])

class SubmissionForm(FlaskForm):
    # Preferences stored as comma-separated string: "4,2,1,0"
    preferences = HiddenField('Preferences', validators=[DataRequired()])
    notes = TextAreaField('Notes (optional)', validators=[Optional(), Length(max=500)])

    def validate_preferences(self, field):
        if not field.data:
            raise ValidationError('Please select your ticket preferences.')
        try:
            prefs = [int(x) for x in field.data.split(',')]
            if not prefs or prefs[0] == 0:
                raise ValidationError('Please select at least one ticket preference.')
            # Verify preferences are in descending order and end with 0
            for i in range(1, len(prefs)):
                if prefs[i] >= prefs[i-1]:
                    raise ValidationError('Each choice must be less than the previous.')
            if prefs[-1] != 0:
                raise ValidationError('Preferences must end with 0.')
        except ValueError:
            raise ValidationError('Invalid preference format.')

class CreatorSubmissionForm(FlaskForm):
    user_id = SelectField('Employee', validators=[DataRequired()], coerce=int)
    preferences = HiddenField('Preferences', validators=[DataRequired()])
    notes = TextAreaField('Notes (optional)', validators=[Optional(), Length(max=500)])

    def validate_preferences(self, field):
        if not field.data:
            raise ValidationError('Please select ticket preferences.')
        try:
            prefs = [int(x) for x in field.data.split(',')]
            if not prefs or prefs[0] == 0:
                raise ValidationError('Please select at least one ticket preference.')
            for i in range(1, len(prefs)):
                if prefs[i] >= prefs[i-1]:
                    raise ValidationError('Each choice must be less than the previous.')
            if prefs[-1] != 0:
                raise ValidationError('Preferences must end with 0.')
        except ValueError:
            raise ValidationError('Invalid preference format.')
