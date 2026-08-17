# messenger.py
import time
from datetime import datetime, UTC, timedelta
from config import RESEND_API_KEY, RESEND_FROM_EMAIL
import resend
import os

from db import session_factory
from models import Notification, Reading, Subscriber, Participant

POLL_INTERVAL_SECONDS = 5  # NFR-1: dispatch within 5s of ingestion
MAX_ATTEMPTS = 3
BACKOFF_SECONDS = 10


def get_dispatchable_notifications(session):
    """
    Return Notification rows eligible to send right now:
    - status == "pending" (never attempted), OR
    - status == "failed" AND attempts < MAX_ATTEMPTS AND
      (last_attempt_at is None or now - last_attempt_at >= BACKOFF_SECONDS)
    """

    pending_notifications = session.query(Notification).filter(Notification.status == "pending").all()

    cutoff = datetime.now(UTC) - timedelta(seconds=BACKOFF_SECONDS)

    failed_notifications = session.query(Notification).filter(
        Notification.status == "failed",
        Notification.attempts < MAX_ATTEMPTS,
        Notification.last_attempt_at.is_(None) | (Notification.last_attempt_at <= cutoff)
    ).all()

    return pending_notifications + failed_notifications



def resolve_message(session, notification):
    """
    Build the email subject/body for this notification.
    FR-2.2: template with [Name] resolved from Participants via notification.bib.
    """

    participant = session.query(Participant).filter(Participant.bib == notification.bib).first()
    if not participant:
        raise ValueError(f"No participant found for bib {notification.bib}")

    subscriber = session.query(Subscriber).filter(Subscriber.id == notification.subscriber_id).first()
    if not subscriber:
        raise ValueError(f"No subscriber found for id {notification.subscriber_id}")

    timing_point = notification.timing_point

    subject = f"Timing update for Athlete {participant.name}"
    body = f"<p>Hello {subscriber.name},</p><p>Athlete {participant.name} has just crossed the {timing_point} timing point!</p>"

    return subscriber.email, subject, body


    


def send_via_resend(to_email, subject, body):
    """
    Call the Resend API to send the email.
    """
    try:

        if resend is not None:
            resend.api_key = os.environ.get("RESEND_API_KEY") or RESEND_API_KEY

        r = resend.Emails.send({
        "from": os.environ.get("RESEND_FROM_EMAIL") or RESEND_FROM_EMAIL,
        "to": to_email,
        "subject": subject,
        "html": body
        })

        print(f"Resend API response: {r}")

    except Exception as e:
        return False, str(e)

    return True, None

def process_notification(session, notification):
    """
    Attempt to send one notification and update its row accordingly.
    """

    to_email, subject, body = resolve_message(session, notification)

    success, error_message = send_via_resend(to_email, subject, body)

    if success:
        notification.status = "sent"
        notification.sent_at = datetime.now(UTC)
    else:
        notification.attempts += 1
        notification.last_attempt_at = datetime.now(UTC)
        notification.error_message = error_message
        notification.status = "failed"
        if notification.attempts >= MAX_ATTEMPTS:
            print(f"Notification id={notification.id} failed after {MAX_ATTEMPTS} attempts. Giving up.")
        

    session.commit()


def run_worker():
    print("Dispatch worker starting...")
    while True:
        session = session_factory()
        try:
            notifications = get_dispatchable_notifications(session)
            for notification in notifications:
                process_notification(session, notification)
        except Exception as e:
            print(f"Worker loop error: {e}")
        finally:
            session.close()

        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    run_worker()
