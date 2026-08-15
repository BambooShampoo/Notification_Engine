"""
Seeds one Participant, one Subscriber, and one pending Notification
so the dispatch worker has something real to process.

Throwaway testing script, same role as fake_rr14.py played for the listener.
Not part of the real system, Sheets sync (FR-1.2) will replace this.
"""

from db import session_factory
from models import Participant, Subscriber, Notification

# EDIT THESE before running
TEST_BIB = 6080
TEST_PARTICIPANT_NAME = "David DuMa"
TEST_SUBSCRIBER_NAME = "Tyler"
TEST_SUBSCRIBER_EMAIL = "tylernvmt@gmail.com"  # use an address you can check
TEST_TIMING_POINT = "FINISH"


def seed():
    session = session_factory()
    try:
        participant = Participant(bib=TEST_BIB, name=TEST_PARTICIPANT_NAME)
        session.add(participant)
        session.commit()
        print(f"Created participant: {participant.name} (bib={participant.bib})")

        subscriber = Subscriber(
            bib=TEST_BIB,
            name=TEST_SUBSCRIBER_NAME,
            email=TEST_SUBSCRIBER_EMAIL,
        )
        session.add(subscriber)
        session.commit()
        print(f"Created subscriber: {subscriber.name} <{subscriber.email}>")

        notification = Notification(
            bib=TEST_BIB,
            timing_point=TEST_TIMING_POINT,
            subscriber_id=subscriber.id,
            status="pending",
        )
        session.add(notification)
        session.commit()
        print(f"Created pending notification id={notification.id} for bib={TEST_BIB}")

    except Exception as e:
        print(f"Seed failed: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    seed()