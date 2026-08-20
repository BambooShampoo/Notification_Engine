# db.py

import os
from sqlalchemy import (create_engine, event)
from sqlalchemy.orm import sessionmaker
from models import Base

LOGGING = False  # Set to True to enable SQLAlchemy logging

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

#export engine and session_factory for use in other modules
__all__ = ["engine", "session_factory"]    
