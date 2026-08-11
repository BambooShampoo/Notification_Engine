# Listen to bind socket to 3099, accept connections, and handle incoming data
import socket
import json
from datetime import datetime, UTC

from db import session_factory
from models import Reading

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


def process_pulse(raw):
    try:
        message = json.loads(raw)
    except json.JSONDecodeError:
        print(f"Bad JSON, skipping: {raw!r}")
        return

    # TODO (Bamboo): skip if message["Invalid"] is True
    if message.get("Invalid") is True:
        print(f"Invalid message, skipping: {raw!r}")
        return

    # TODO (Bamboo): pull the bib out (message["Bib"]), cast to int
    try:
        bib = int(message["Bib"])
    except (KeyError, ValueError):
        print(f"Missing or invalid Bib, skipping: {raw!r}")
        return  

    # TODO (Bamboo): open a session from session_factory, create a
    # Reading(bib=..., timestamp=datetime.utcnow()), add + commit,
    # close the session. Print the row after commit to confirm it wrote.
    session = session_factory()
    try:
        reading = Reading(bib=bib, timestamp=datetime.now(UTC))
        session.add(reading)
        session.commit()
        print(f"Row written: bib={bib}")
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
    start_listener()
