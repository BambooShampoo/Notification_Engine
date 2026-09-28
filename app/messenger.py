# messenger.py
import time
from datetime import datetime, UTC, timedelta
from zoneinfo import ZoneInfo
from config import RESEND_API_KEY, RESEND_FROM_EMAIL
import resend
import os
from log_queue import add_log, set_queue

from db import session_factory
from models import Notification, Subscriber, Participant

POLL_INTERVAL_SECONDS = 5  # dispatch within 5s of ingestion
MAX_ATTEMPTS = 3
BACKOFF_SECONDS = 10

def update_notification_status(notification, succeed):
    timestamp = datetime.now(UTC)
    notification.last_attempt_at = timestamp
    if succeed:
        notification.sent_at = timestamp
        notification.status = "sent"
    else:
        notification.status = "failed"
    notification.attempts += 1

    return


# get pending notifications along with any failed ones that could be retried
def get_dispatchable_notifications(session):
    """
    Return Notification rows eligible to send right now:
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
    """

    # in case sub_worker.py had loading participants
    participant = session.query(Participant).filter(Participant.bib == notification.bib).first()
    if not participant:
        add_log("MESSENGER", datetime.now(UTC), f"No participant found for bib {notification.bib}","ERROR")
        raise ValueError(f"No participant found for bib {notification.bib}")
    
    # in case sub_worker.py had issue adding subscriber
    subscriber = session.query(Subscriber).filter(Subscriber.id == notification.subscriber_id).first()
    if not subscriber:
        add_log("MESSENGER", datetime.now(UTC), f"No subscriber found for id {notification.subscriber_id}","ERROR")
        raise ValueError(f"No subscriber found for id {notification.subscriber_id}")
    
    now = datetime.now(UTC)
    timeofday = now.astimezone(ZoneInfo("America/Los_Angeles")).strftime("%I:%M%p").lstrip("0")

    timing_point = notification.timing_point
    subject = f"Timing update for Athlete {participant.name}"
    body = f"""
    <body>
        <p>Hello {subscriber.name}!</p>
        <p>Athlete {participant.name} has crossed the {timing_point} timing point at {timeofday}!
        <br><br>For additional information and to see their results, visit the event website at https://sportstats.one.
        <br><br>Thanks for following the race,<br>Tyler From SportStats West
        <br><br><small><i>This is an automated message from SportStats West. Please do not reply to this email.
        <br>Brought to you by the MinhT notification engine, fresh updates straight to you ;)</i></small></p>
    </body>
    """
        

    return subscriber.email, subject, body


    
def send_via_resend(to_email, subject, body):
    """
    Call the Resend API to send the email.
    """
    try:
        add_log("MESSENGER", datetime.now(UTC), f"attempting to send email: Subject: {subject}","INFO")
        if resend is not None:
            resend.api_key = os.environ.get("RESEND_API_KEY") or RESEND_API_KEY

        # Resued Resend API example code to keep simple
        r = resend.Emails.send({
        "from": os.environ.get("RESEND_FROM_EMAIL") or RESEND_FROM_EMAIL,
        "to": to_email,
        "subject": subject,
        "html": body
        })

        print(f"Resend API response: {r}")

    except Exception as e:
        add_log("MESSENGER", datetime.now(UTC), f"Error sending email: {e}","ERROR")
        return False, str(e)

    return True, None

def process_notification(session, notification):
    """
    Attempt to send one notification and update its row accordingly.
    """
    add_log("MESSENGER", datetime.now(UTC), f"Processing notification: id={notification.id}","INFO")

    try:
        to_email, subject, body = resolve_message(session, notification)

    except Exception as e:
        add_log("MESSENGER", datetime.now(UTC), f"Error resolving message for notification id={notification.id}: {e}","ERROR")
        print(f"Error resolving message for notification id={notification.id}: {e}")
        update_notification_status(notification, False)
        session.commit()
        return

    success, error_message = send_via_resend(to_email, subject, body)

    if success:
        update_notification_status(notification, True)
        add_log("MESSENGER", datetime.now(UTC), f"Notification id={notification.id} sent successfully","INFO")
    else:
        update_notification_status(notification, False)
        notification.error_message = error_message
        add_log("MESSENGER", datetime.now(UTC), f"Notification id={notification.id} failed: {error_message}","ERROR")
        
        if notification.attempts >= MAX_ATTEMPTS:
            add_log("MESSENGER", datetime.now(UTC), f"Notification id={notification.id} failed after {MAX_ATTEMPTS} attempts. Giving up.","ERROR")
            print(f"Notification id={notification.id} failed after {MAX_ATTEMPTS} attempts. Giving up.")
        

    session.commit()
    return


def run_worker(queue):
    set_queue(queue)
    add_log("MESSENGER", datetime.now(UTC), "Messenger worker started","INFO")
    
    print("Messenger worker starting...")
    while True:
        session = session_factory()
        try:
            notifications = get_dispatchable_notifications(session)
            for notification in notifications:
                process_notification(session, notification)
        except Exception as e:
            add_log("MESSENGER", datetime.now(UTC), f"Worker loop error: {e}","ERROR")
            print(f"Worker loop error: {e}")
        finally:
            session.close()

        time.sleep(POLL_INTERVAL_SECONDS)


