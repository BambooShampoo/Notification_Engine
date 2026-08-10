from sqlalchemy import (
    Column, Integer, String, ForeignKey, DateTime, UniqueConstraint,func,Enum as SAEnum
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime


Base = declarative_base()


class Participant(Base):
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True)
    bid = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)

    subscribers = relationship("Subscriber", back_populates="participant")


class Subscriber(Base):
    __tablename__ = "subscribers"

    id = Column(Integer, primary_key=True)
    bid = Column(String, ForeignKey("participants.bid"), nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    subscribed_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        (UniqueConstraint("bid", "email", name="uq_subscriber_bid_email")),
    )

    participant = relationship("Participant", back_populates="subscribers")


class Reading(Base):
    __tablename__ = "readings"

    id = Column(Integer, primary_key=True)
    bid = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False) 



class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    bid = Column(String, nullable=False)
    subscriber_id = Column(Integer, ForeignKey("subscribers.id"), nullable=False)
    status = Column(SAEnum("pending", "sent", "failed", name="notification_status"), nullable=False)
    attempts = Column(Integer, default=0)
    last_attempt_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)


class SyncState(Base):
    __tablename__ = "sync_state"

    id = Column(Integer, primary_key=True)
    last_row_index = Column(Integer, nullable=False)


class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True)
    message = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)