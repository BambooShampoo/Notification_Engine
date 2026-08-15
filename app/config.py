import os
from pathlib import Path
from dotenv import load_dotenv

# config.py lives in app/, .env lives one level up in project root
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

RESEND_API_KEY = os.environ["RESEND_API_KEY"]
RESEND_FROM_EMAIL = os.environ["RESEND_FROM_EMAIL"]

GOOGLE_SERVICE_ACCOUNT_FILE = os.environ["GOOGLE_SERVICE_ACCOUNT_FILE"]
GOOGLE_SHEET_ID = os.environ["GOOGLE_SHEET_ID"]
GOOGLE_SHEET_RANGE = os.environ.get("GOOGLE_SHEET_RANGE", "Sheet1!A:D")

LISTENER_HOST = os.environ.get("LISTENER_HOST", "127.0.0.1")
LISTENER_PORT = int(os.environ.get("LISTENER_PORT", 3099))

ADMIN_API_HOST = os.environ.get("ADMIN_API_HOST", "0.0.0.0")
ADMIN_API_PORT = int(os.environ.get("ADMIN_API_PORT", 8000))