# listener.py
# Listen to bind socket to 3099, accept connections, and handle incoming data
from sqlalchemy.exc import OperationalError
import time
import socket
import json
from datetime import datetime, UTC, timedelta

from db import session_factory
from models import Notification, Reading, Subscriber
from load_participants import load_participants

HOST = "127.0.0.1"
PORT = 3099
DELIMITER = "\t"


def handle_client(conn, addr):
    print(f"RR14 connected from {addr}")
    buffer = ""
    with conn:
        while True:
            data = conn.recv(4096)
            if not data:
                print("RR14 disconnected")
                break
            buffer += data.decode("utf-8", errors="replace")

            parts = buffer.split(DELIMITER)
            buffer = parts.pop()  # last part may be incomplete, hold for next recv

            for part in parts:
                trimmed = part.strip()
                if trimmed:
                    process_pulse(trimmed)

def trigger_notification(session, bib, timing_point, max_retries):
    for attempt in range(max_retries):
            try:
                subscribers = session.query(Subscriber).filter(Subscriber.bib == bib).all()
                for subscriber in subscribers:
                    notification = Notification(
                        bib=bib,
                        timing_point=timing_point,
                        subscriber_id=subscriber.id,
                        status="pending"
                    )
                    session.add(notification)
                session.commit()
                print(f"Queued {len(subscribers)} notifications for bib={bib}")
                return
            except OperationalError as e:
                session.rollback()
                print(f"DB locked, retrying ({attempt+1}/{max_retries}): {e}")
                time.sleep(0.5 * (attempt + 1))

    print(f"Failed to queue notifications for bib={bib} after {max_retries} attempts")

def process_pulse(raw):
    try:
        message = json.loads(raw)
    except json.JSONDecodeError:
        print(f"Bad JSON, skipping: {raw!r}")
        return

    if message.get("Invalid") is True:
        print(f"Invalid message, skipping: {raw!r}")
        return

    try:
        bib = int(message["Bib"])
    except (KeyError, ValueError):
        print(f"Missing or invalid Bib, skipping: {raw!r}")
        return  

    
    try:
        timing_point = message["TimingPoint"]
    except KeyError:
        print(f"Missing TimingPoint, skipping: {raw!r}")
        return

    session = session_factory()
    try:
        timestamp = datetime.now(UTC)
        reading = Reading(bib=bib, timing_point=timing_point, timestamp=timestamp)

        session.add(reading)
        session.commit()
        print(f"Row written: bib={bib}, timestamp={timestamp}")

        cutoff = timestamp - timedelta(seconds=60)
        duplicate = session.query(Reading).filter(
            Reading.bib == bib,
            Reading.timing_point == timing_point,
            Reading.timestamp > cutoff,
            Reading.id != reading.id
        ).first()

        


        if duplicate:
            print(f"Duplicate reading found for bib={bib} within 60 seconds, skipping notification.")
        else:
            try:
                trigger_notification(session, bib, timing_point, 3)
            except Exception as e:
                print(f"Error triggering notification for bib={bib}: {e}")

    except Exception as e:
        print(f"Error writing row: {e}")
        session.rollback()
    finally:
        session.close()

    


def start_listener():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f"Listening for RR14 on {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        handle_client(conn, addr)


if __name__ == "__main__":
    load_participants()
    start_listener()
