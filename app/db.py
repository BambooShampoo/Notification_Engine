# db.py

import os
from sqlalchemy import (create_engine, event)
from sqlalchemy.orm import sessionmaker
from models import Base

LOGGING = False  # for SQLAlchemy logging

# Define the path to the SQLite database file
BASE_DIR = os.path.dirname(__file__)          # points to app/
DB_PATH = os.path.join(BASE_DIR, "../data/sportstats.db")  # points to data/sportstats.db

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Create the database engine and session factory
engine = create_engine(f"sqlite:///{DB_PATH}", echo=LOGGING, connect_args={"check_same_thread": False})
print(f"Engine created successfully with DB_PATH: {DB_PATH}")

@event.listens_for(engine, "connect")
# Set SQLite to use Write-Ahead Logging (WAL) mode for better concurrency
def set_wal_mode(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA busy_timeout=5000;")  # wait up to 5s for a lock before raising
    cursor.close()

# Create database tables if they don't exist
Base.metadata.create_all(engine)
print("Database tables created successfully.")

# Create a session factory for database interactions
session_factory = sessionmaker(bind=engine)
print("Session factory created successfully.")

def has_data():
    """Return True if any table has at least one row."""
    with engine.connect() as connection:
        for table_name in ("notifications", "subscribers", "readings", "logs", "participants"):
            table = Base.metadata.tables[table_name]
            # TODO: check if this table has any row. Look at select(table).limit(1)
            # and .first() on the result. Return True as soon as you find one.
    return False

# Delete database, dont want to keep sensitive information laying around after race is done.
def clear_all_tables():
    table_names = ("notifications", "subscribers", "readings", "logs", "participants")
    with engine.begin() as connection:
        for table_name in table_names:
            connection.execute(Base.metadata.tables[table_name].delete())

#export engine and session_factory for use in other modules
__all__ = ["engine", "session_factory", "clear_all_tables", "has_data"]
