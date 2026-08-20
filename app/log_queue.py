# log_queue.py 
"""A queue for logging messages. used by all three proccesses, listener,messenger, and sub_worker. a seperate process is used to keep one process responsible for 
writing to the log table in the database. this is done to avoid multiple processes writing to the log table at the same time and causing a deadlock/ race condition."""

from datetime import datetime
from multiprocessing import Queue
from db import session_factory
from models import Log

log_queue = None  # will be set by set_queue() in each process

def set_queue(queue):
    """Bind this process's log_queue reference to the shared queue passed from main."""
    global log_queue
    log_queue = queue


def add_log(log_type, timestamp, log_message, log_level="INFO"):
    log_queue.put((log_type, timestamp, log_message, log_level))

def write_log(queue):
    set_queue(queue)
    session = session_factory()
    while True:
        try:
            log_type, timestamp, log_message, log_level = log_queue.get()
            if log_type is None:
                break
            new_log = Log(source=log_type, timestamp=timestamp, message=log_message, severity=log_level)
            session.add(new_log)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error writing log to database: {e}")
    session.close()

def export_log():
    """Export log messages from the database to a txt. Writes them to data/logs_<timestamp>.txt"""
    session = session_factory()
    logs = session.query(Log).all()
    with open(f"data/logs_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt", "w") as f:
        for log in logs:
            f.write(f"{log.timestamp}: [{log.severity}] {log.source} - {log.message}\n")
    session.close()

__all__ = ["add_log", "export_log"]