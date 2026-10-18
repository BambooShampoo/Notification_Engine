# sub_worker.py

"""Sub-worker for processing notifications. Adding to the database from polling the Google Sheet."""

import csv
from time import sleep
import requests

from log_queue import add_log, set_queue
from models import Participant, Subscriber
from datetime import datetime, UTC

def fetch_csv(url):
    """Fetch CSV data from a URL and return it as a list of dictionaries."""
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad responses
    decoded_content = response.content.decode("utf-8")
    reader = csv.DictReader(decoded_content.splitlines())
    return list(reader)

def add_subscribers_from_csv(csv_data, session):
    """Add subscribers to the database from CSV data."""

    count_added = 0

    for row in csv_data:
        try:
            bib = int(row.get("Bib number", "").strip())
        except (ValueError, TypeError):
            continue  # Skip rows with invalid bib values
        #name = f"{row.get('Your Name', '')}".strip()
        email = row.get("Email", "").strip()

        if not bib or not email:
        #if not bib or not name or not email:
            continue  # Skip incomplete rows

        # no way to check for valid bibs with the google form, must check here
        participant = session.query(Participant).filter_by(bib=bib).first()
        if not participant:
            # skip adding subscriber if participant does not exist
            print(f"Skipping subscriber for bib={bib} as participant does not exist.")
            continue

        #subscriber = Subscriber(bib=bib, name=name, email=email)
        subscriber = Subscriber(bib=bib, email=email)

        if session.query(Subscriber).filter_by(bib=bib, email=email).first():
            continue  # Skip if subscriber already exists
        try:
            session.add(subscriber)
            session.commit()
            count_added += 1
            add_log("SUB_WORKER", datetime.now(UTC), f"Added subscriber for bib={bib}","INFO")
            print(f"Added subscriber: <{email}> for bib={bib}")
        except Exception as e:
            add_log("SUB_WORKER", datetime.now(UTC), f"Error adding subscriber for bib={bib}: {e}","ERROR")
            print(f"Error adding subscriber: {e}")
            session.rollback()
            
    if count_added > 0:
        print(f"Added {count_added} subscribers to the database.")

def run_sub_worker(queue):
    """Run the sub-worker to fetch and add subscribers from Google Sheets."""
    set_queue(queue)
    from db import session_factory
    from config import GOOGLE_SHEETS_CSV_URL
    add_log("SUB_WORKER", datetime.now(UTC), "Starting sub-worker","INFO")

    while True:
        session = session_factory()
        try:
            # fetching entire list each time, volume wont be big so optimization wont be nessesary *for now*
            csv_data = fetch_csv(GOOGLE_SHEETS_CSV_URL)
            add_subscribers_from_csv(csv_data, session)
        except Exception as e:
            print(f"Error processing subscribers: {e}")
            add_log("SUB_WORKER", datetime.now(UTC), f"Error processing subscribers: {e}","ERROR")
        finally:
            session.close()
        sleep(10)  # Updates from the google sheet wont be translated until we poll it, must do this constantly
    
    
    


