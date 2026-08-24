import os
import sys
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv

# config.py lives in app/, .env lives one level up in project root

# Determine the base directory
if getattr(sys, 'frozen', False):
    # Running as a frozen executable
    BASE_DIR = Path(sys.executable).parent
else:
    # Running as a script
    BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "database.db"
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

RESEND_API_KEY = os.environ["RESEND_API_KEY"]
RESEND_FROM_EMAIL = os.environ["RESEND_FROM_EMAIL"]

GOOGLE_SHEET_RANGE = os.environ.get("GOOGLE_SHEET_RANGE", "Sheet1!A:D")
GOOGLE_SHEET_NAME, _, GOOGLE_SHEET_COLUMNS = GOOGLE_SHEET_RANGE.partition("!")
GOOGLE_SHEETS_CSV_URL = (os.environ.get("GOOGLE_SHEETS_CSV_URL") or
    f"https://docs.google.com/spreadsheets/d/{quote(os.environ['GOOGLE_SHEET_ID'])}/gviz/tq?tqx=out:csv&sheet={quote(GOOGLE_SHEET_NAME)}&range={quote(GOOGLE_SHEET_COLUMNS)}"
)

LISTENER_HOST = os.environ.get("LISTENER_HOST", "127.0.0.1")
LISTENER_PORT = int(os.environ.get("LISTENER_PORT", 3099))

ADMIN_API_HOST = os.environ.get("ADMIN_API_HOST", "0.0.0.0")
ADMIN_API_PORT = int(os.environ.get("ADMIN_API_PORT", 8000))