# model.py

from sqlalchemy import (
    Column, Index, Integer, String, ForeignKey, DateTime, UniqueConstraint,func,Enum as SAEnum
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime


Base = declarative_base()


class Participant(Base):
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True)
    bib = Column(Integer, unique=True, nullable=False)
    name = Column(String, nullable=False)

    subscribers = relationship("Subscriber", back_populates="participant")


class Subscriber(Base):
    __tablename__ = "subscribers"

    id = Column(Integer, primary_key=True)
    bib = Column(Integer, ForeignKey("participants.bib"), nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    subscribed_at = Column(DateTime, server_default=func.now(), nullable=False) # from the form template, cant be bothered to change what form adds

    __table_args__ = (
        (UniqueConstraint("bib", "email", name="uq_subscriber_bib_email")),
    )

    participant = relationship("Participant", back_populates="subscribers")


class Reading(Base):
    __tablename__ = "readings"

    id = Column(Integer, primary_key=True)
    bib = Column(Integer, nullable=False)
    timing_point = Column(String, nullable=True)
    timestamp = Column(DateTime, nullable=False) 

    __table_args__ = (
        (Index("idx_readings_bib_timestamp", "bib", "timing_point", "timestamp")),
    )


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    bib = Column(Integer, nullable=False)
    timing_point = Column(String, nullable=True)
    subscriber_id = Column(Integer, ForeignKey("subscribers.id"), nullable=False)
    status = Column(SAEnum("pending", "sent", "failed", name="notification_status"), nullable=False)
    attempts = Column(Integer, default=0)
    last_attempt_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)


# class SyncState(Base):
#     __tablename__ = "sync_state"

#     id = Column(Integer, primary_key=True)
#     last_row_index = Column(Integer, nullable=False)


class Log(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True)
    source = Column(String, nullable=False)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    message = Column(String, nullable=False)
    severity = Column(String, nullable=True) # optional