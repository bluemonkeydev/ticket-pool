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


def send_password_reset_email(user, reset_url):
    """Send a password reset email to the user."""
    app_name = current_app.config.get('APP_NAME', 'Ticket Allocation')

    subject = f"{app_name} - Password Reset"

    body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2>Password Reset Request</h2>
        <p>Hi {user.name},</p>
        <p>We received a request to reset your password for {app_name}.</p>
        <p>Click the link below to set a new password:</p>
        <p><a href="{reset_url}" style="background-color: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Reset Password</a></p>
        <p>Or copy this link: <a href="{reset_url}">{reset_url}</a></p>
        <p>This link will expire in 1 hour.</p>
        <p>If you didn't request this, you can safely ignore this email.</p>
        <br>
        <p>Thanks,<br>{app_name}</p>
    </body>
    </html>
    """

    body_text = f"""
Password Reset Request

Hi {user.name},

We received a request to reset your password for {app_name}.

Click here to set a new password: {reset_url}

This link will expire in 1 hour.

If you didn't request this, you can safely ignore this email.

Thanks,
{app_name}
    """

    return send_email(user.email, subject, body_html, body_text)


def send_welcome_email(user, reset_url):
    """Send a welcome email to a new user with password setup link."""
    app_name = current_app.config.get('APP_NAME', 'Ticket Allocation')

    subject = f"Welcome to {app_name} - Set Your Password"

    body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2>Welcome to {app_name}!</h2>
        <p>Hi {user.name},</p>
        <p>An account has been created for you at {app_name}.</p>
        <p>Click the link below to set your password and get started:</p>
        <p><a href="{reset_url}" style="background-color: #27ae60; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Set Your Password</a></p>
        <p>Or copy this link: <a href="{reset_url}">{reset_url}</a></p>
        <br>
        <p>Thanks,<br>{app_name}</p>
    </body>
    </html>
    """

    body_text = f"""
Welcome to {app_name}!

Hi {user.name},

An account has been created for you at {app_name}.

Click here to set your password and get started: {reset_url}

Thanks,
{app_name}
    """

    return send_email(user.email, subject, body_html, body_text)
