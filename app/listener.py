# listener.py
# Listen to bind socket to 3099, accept connections, and handle incoming data
from threading import Thread

from sqlalchemy.exc import OperationalError
import time
import socket
import json
from datetime import datetime, UTC, timedelta

from log_queue import set_queue, add_log
from db import session_factory
from models import Notification, Reading, Subscriber

HOST = "127.0.0.1"
PORT = 3099
DELIMITER = "\t"
MAX_NOTIF_ATTEMPTS = 3


def handle_client(conn, addr):
    add_log("LISTENER", datetime.now(UTC), f"RR14 connected from {addr}","INFO")
    print(f"RR14 connected from {addr}")
    buffer = ""
    with conn:
        while True:
            data = conn.recv(4096)

            if not data:
                add_log("LISTENER", datetime.now(UTC), "RR14 disconnected","INFO")
                print("RR14 disconnected")
                break
            
            buffer += data.decode("utf-8", errors="replace")

            parts = buffer.split(DELIMITER)
            buffer = parts.pop()  # last part may be incomplete, hold for next recv

            for part in parts:
                trimmed = part.strip()
                if trimmed: # wont process incomplete package if pulse is too big
                    process_pulse(trimmed)

def trigger_notification(session, bib, timing_point, max_retries):
    for attempt in range(max_retries):
            try:
                # adding a pending notification for whatever bib crossed, anyone subscribed to this bib will have 'pending' notif
                subscribers = session.query(Subscriber).filter(Subscriber.bib == bib).all()
                for subscriber in subscribers:
                    notification = Notification(
                        bib=bib,
                        timing_point=timing_point,
                        subscriber_id=subscriber.id,
                        status="pending"
                    )
                    session.add(notification)
                    add_log("LISTENER", datetime.now(UTC), f"Queued notification for bib={bib}, timing_point={timing_point}, subscriber_id={subscriber.id}","INFO")
                session.commit()
                print(f"Queued {len(subscribers)} notifications for bib={bib}")
                return
            
            except OperationalError as e:
                session.rollback() # Keep things atomic
                add_log("LISTENER", datetime.now(UTC), f"DB locked, retrying ({attempt+1}/{max_retries}): {e}","ERROR")
                print(f"DB locked, retrying ({attempt+1}/{max_retries}): {e}")
                time.sleep(0.5 * (attempt + 1))

    print(f"Failed to queue notifications for bib={bib} after {max_retries} attempts")
    add_log("LISTENER", datetime.now(UTC), f"Failed to queue notifications for bib={bib} after {max_retries} attempts","ERROR")

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
        add_log("LISTENER", timestamp, f"Row written in Reading: bib={bib}, timing_point={timing_point}, timestamp={timestamp}","INFO")
        # print(f"Row written: bib={bib}, timestamp={timestamp}")


        # Mainly for the people at the finish line lingering near finish mat
        cutoff = timestamp - timedelta(seconds=60)
        duplicate = session.query(Reading).filter(
            Reading.bib == bib,
            Reading.timing_point == timing_point,
            Reading.timestamp > cutoff,
            Reading.id != reading.id
        ).first()

        if duplicate: # still keep the reading so that this works for however long dup is around finish mat or any other mat
            add_log("LISTENER", timestamp, f"Duplicate reading found for bib={bib} within 60 seconds, skipping notification.","ERROR")
            print(f"Duplicate reading found for bib={bib} within 60 seconds, skipping notification.")
        else:
            try: # first detection
                trigger_notification(session, bib, timing_point, MAX_NOTIF_ATTEMPTS)
            except Exception as e:
                add_log("LISTENER", timestamp, f"Error triggering notification for bib={bib}: {e}","ERROR")
                print(f"Error triggering notification for bib={bib}: {e}")

    except Exception as e:
        print(f"Error writing row: {e}")
        session.rollback()
    finally:
        session.close()

    


def start_listener(queue):
    set_queue(queue)
    add_log("LISTENER", datetime.now(UTC), "Starting listener","INFO")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()

    add_log("LISTENER", datetime.now(UTC), f"Listening for RR14 on {HOST}:{PORT}","INFO")
    print(f"Listening for RR14 on {HOST}:{PORT}")

    # Old setup only able to handle one connection, threads for races that have more than one decoder (Start, Splits, Finishes)
    while True:
        conn, addr = server.accept()
        Thread(target=handle_client, args=(conn, addr), daemon=True).start()
