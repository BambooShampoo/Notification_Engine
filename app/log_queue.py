# log_queue.py 
"""A queue for logging messages. used by all three proccesses, listener,messenger, and sub_worker. a seperate process is used to keep one process responsible for 
writing to the log table in the database. this is done to avoid multiple processes writing to the log table at the same time and causing a race condition."""

from datetime import datetime
from multiprocessing import Queue
from db import session_factory
from models import Log
from config import DATA_DIR

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

# In case something happened mid race and we need to trace it.
def export_log():
    """Export log messages from the database to a txt. Writes them to data/logs_<timestamp>.txt"""
    session = session_factory()

    try:
        logs = session.query(Log).order_by(Log.timestamp.asc(), Log.id).all()
        filedir = f"logs_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
        outpath = DATA_DIR/filedir
        with open(outpath, "w", encoding="utf-8") as f:
            for log in logs:
                f.write(f"{log.timestamp}: [{log.severity}] {log.source} - {log.message}\n")

    finally:
        session.close()

    return outpath

__all__ = ["add_log", "export_log", "write_log", "set_queue"]