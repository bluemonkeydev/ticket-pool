"""Email utility module using AWS SES."""

import boto3
from botocore.exceptions import ClientError
from flask import current_app
import logging

logger = logging.getLogger(__name__)


def send_email(to, subject, body_html, body_text=None):
    """
    Send an email using AWS SES.

    If MAIL_ENABLED is False, logs the email instead of sending.
    Returns True on success, False on failure.
    """
    config = current_app.config

    if not config.get('MAIL_ENABLED'):
        logger.info(f"[EMAIL DISABLED] Would send to: {to}")
        logger.info(f"[EMAIL DISABLED] Subject: {subject}")
        logger.info(f"[EMAIL DISABLED] Body: {body_text or body_html}")
        print(f"\n{'='*50}")
        print(f"EMAIL (disabled - not sent)")
        print(f"To: {to}")
        print(f"Subject: {subject}")
        print(f"Body:\n{body_text or body_html}")
        print(f"{'='*50}\n")
        return True

    try:
        client = boto3.client(
            'ses',
            region_name=config.get('AWS_REGION'),
            aws_access_key_id=config.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=config.get('AWS_SECRET_ACCESS_KEY')
        )

        response = client.send_email(
            Source=config.get('SES_SENDER_EMAIL'),
            Destination={'ToAddresses': [to]},
            Message={
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {
                    'Html': {'Data': body_html, 'Charset': 'UTF-8'},
                    'Text': {'Data': body_text or body_html, 'Charset': 'UTF-8'}
                }
            }
        )
        logger.info(f"Email sent to {to}: {response['MessageId']}")
        return True

    except ClientError as e:
        logger.error(f"Failed to send email to {to}: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending email to {to}: {str(e)}")
        return False


def send_magic_link_email(user, login_url):
    """Send a magic link login email to the user."""
    app_name = current_app.config.get('APP_NAME', 'Ticket Allocation')

    subject = f"{app_name} - Your Login Link"

    body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2>Your Login Link</h2>
        <p>Hi {user.name},</p>
        <p>Click the button below to log in to {app_name}:</p>
        <p><a href="{login_url}" style="background-color: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Log In</a></p>
        <p>Or copy this link: <a href="{login_url}">{login_url}</a></p>
        <p>This link will expire in 15 minutes and can only be used once.</p>
        <p>If you didn't request this, you can safely ignore this email.</p>
        <br>
        <p>Thanks,<br>{app_name}</p>
    </body>
    </html>
    """

    body_text = f"""
Your Login Link

Hi {user.name},

Click here to log in to {app_name}: {login_url}

This link will expire in 15 minutes and can only be used once.

If you didn't request this, you can safely ignore this email.

Thanks,
{app_name}
    """

    return send_email(user.email, subject, body_html, body_text)


def send_welcome_email(user, login_url):
    """Send a welcome email to a new user with their first login link."""
    app_name = current_app.config.get('APP_NAME', 'Ticket Allocation')

    subject = f"Welcome to {app_name}"

    body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2>Welcome to {app_name}!</h2>
        <p>Hi {user.name},</p>
        <p>An account has been created for you at {app_name}.</p>
        <p>Click the button below to log in and get started:</p>
        <p><a href="{login_url}" style="background-color: #27ae60; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Log In</a></p>
        <p>Or copy this link: <a href="{login_url}">{login_url}</a></p>
        <p>This link will expire in 15 minutes. After that, you can request a new one from the login page.</p>
        <br>
        <p>Thanks,<br>{app_name}</p>
    </body>
    </html>
    """

    body_text = f"""
Welcome to {app_name}!

Hi {user.name},

An account has been created for you at {app_name}.

Click here to log in and get started: {login_url}

This link will expire in 15 minutes. After that, you can request a new one from the login page.

Thanks,
{app_name}
    """

    return send_email(user.email, subject, body_html, body_text)


def send_allocation_email(user, event, requested_tickets, allocated_tickets):
    """Send an email notifying a user of their ticket allocation."""
    app_name = current_app.config.get('APP_NAME', 'Ticket Pool')
    app_url = current_app.config.get('APP_URL', '')

    subject = f"{app_name} - Ticket Allocation for {event.name}"

    req_word = "ticket" if requested_tickets == 1 else "tickets"
    alloc_word = "ticket" if allocated_tickets == 1 else "tickets"

    if allocated_tickets > 0:
        message = f"Great news! You requested {requested_tickets} {req_word} and have been allocated <strong>{allocated_tickets} {alloc_word}</strong> for {event.name}."
        message_text = f"Great news! You requested {requested_tickets} {req_word} and have been allocated {allocated_tickets} {alloc_word} for {event.name}."
    else:
        message = f"You requested {requested_tickets} {req_word}, but unfortunately we were unable to allocate any tickets for {event.name} this time."
        message_text = message

    event_url = f"{app_url}/events/{event.id}" if app_url else ""

    body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2>Ticket Allocation Update</h2>
        <p>Hi {user.name},</p>
        <p>{message}</p>
        <p><strong>Event:</strong> {event.name}</p>
        <p><strong>Date:</strong> {event.event_date}</p>
        {f'<p><a href="{event_url}" style="background-color: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">View Event Details</a></p>' if event_url else ''}
        <br>
        <p>Thanks,<br>{app_name}</p>
    </body>
    </html>
    """

    body_text = f"""
Ticket Allocation Update

Hi {user.name},

{message_text}

Event: {event.name}
Date: {event.event_date}

{f'View event details: {event_url}' if event_url else ''}

Thanks,
{app_name}
    """

    return send_email(user.email, subject, body_html, body_text)
