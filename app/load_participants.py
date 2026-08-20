# load_participants.py
"""load participants from data/participants.csv into the database. Populate the participants table."""

import csv
from pathlib import Path

from models import Participant
from db import session_factory

def load_participants():
    participants_path = Path(__file__).resolve().parent.parent / "data" / "participants.csv"
    session = session_factory()
    try:
        existing_bibs = {
            int(bib) for (bib,) in session.query(Participant.bib).all()
        }
        with participants_path.open("r", newline="") as f:
            reader = csv.DictReader(f)

            for row in reader:
                raw_bib = row["NUMBER"].strip()
                name = f"{row['FNAME']} {row['LNAME']}".strip()
                if not raw_bib.isdigit() or not name:
                    continue

                bib = int(raw_bib)
                if not bib or bib in existing_bibs:
                    continue

                participant = Participant(
                    bib=bib,
                    name=name,
                )
                session.add(participant)
                existing_bibs.add(bib)

        session.commit()
    finally:
        session.close()

if __name__ == "__main__":
    load_participants()
