# SportStats Notification Engine

Real-time email notifications for race subscribers. When a bib crosses a RaceResult 14 (RR14) timing point, subscribers mapped to that bib get an email within 5 seconds.

## What it does

- Listens for live bib-crossing data from RR14 over a raw TCP socket, handling multiple concurrent decoder connections (e.g. Start, Split, Finish mats reporting simultaneously).
- Deduplicates repeat reads of the same bib/timing point within a 60-second window.
- Looks up which subscribers are mapped to that bib and queues a notification for each.
- Sends the notification email via the Resend API, retrying failed sends up to 3 times with a 10-second backoff.
- Syncs new subscribers from a Google Form (via its linked Sheet) every 10 seconds.
- Logs every process's activity to a single `logs` table via a dedicated writer process, and exports the full log to a timestamped `.txt` file on shutdown.

## How it works

Four independent processes, launched from one entry point, coordinating through a shared SQLite database file (WAL mode, so they can read/write concurrently without locking each other out) and a shared `multiprocessing.Queue` for logging:

| Process | File | Job |
|---|---|---|
| Listener | `listener.py` | Binds a TCP socket, accepts multiple concurrent RR14 connections (one thread per connection), writes readings, triggers notifications |
| Subscriber sync | `sub_worker.py` | Polls the published Google Sheet CSV every 10s, inserts new subscribers |
| Dispatch worker | `messenger.py` | Polls the DB every 5s for pending/retryable notifications, sends via Resend |
| Log writer | `log_queue.py` | Single dedicated writer for the `logs` table, reads from a shared queue so the other three processes never write to it directly (avoids write contention) |

Each process is a separate OS process (`multiprocessing.Process`), not a thread, so a crash in one doesn't take down the others. Within the listener process, each accepted TCP connection runs on its own thread, since threads share memory cheaply and each pulse is handled with its own short-lived DB session.

The log queue is created once in `main.py` and passed explicitly into each process at startup — this matters on Windows, where the default process start method (`spawn`) re-imports modules fresh in each child, so a queue created at module import time would silently end up as separate, disconnected queues per process instead of one shared queue.

Participants (bib → name) are loaded once at startup from a CSV, not synced continuously.

## Requirements

**Software**
- Python 3.12
- Packages: `sqlalchemy`, `resend`, `requests`, `python-dotenv`
  ```
  pip install sqlalchemy resend requests python-dotenv
  ```

**Accounts / infrastructure**
- A [Resend](https://resend.com) account with a verified sending domain
- A Google Form (for subscriber signup) with its linked Sheet published to the web as CSV

## Manual setup (not automated)

These steps have to happen once per event, outside the code, before running:

1. **`.env` file** — create one project root above `app/`, containing:
   ```
   RESEND_API_KEY=...
   RESEND_FROM_EMAIL=...
   GOOGLE_SHEETS_CSV_URL=...
   ```
   (or `GOOGLE_SHEET_ID` + `GOOGLE_SHEET_RANGE` if not using a direct CSV URL — see `config.py`)

2. **Resend domain verification** — add the MX/TXT/DKIM records Resend gives you to your domain's DNS (manually, or via your registrar/Cloudflare). Sends will stay sandboxed to your own inbox until this is verified.

3. **Google Form + Sheet** — create the subscription Form, then in the linked Sheet: File → Share → Publish to web → CSV. Copy that URL into `.env`. No Google Cloud service account or billing needed.

4. **`data/participants.csv`** — drop this in before first run, with columns `NUMBER,FNAME,LNAME`. This is your bib list for the race. Re-running skips bibs already in the DB, so updating this file and restarting is safe.

5. **RR14 configuration** — point RaceResult 14's export/output settings at the listener's host and port (default `127.0.0.1:3099`), sending tab-delimited JSON pulses. Multiple RR14 devices (e.g. one per timing point) can connect to the same host/port simultaneously.

## Running it

From inside `app/`:

```bash
python main.py
```

This will:
1. Load `data/participants.csv` into the database (skipping bibs already loaded)
2. Start the listener, subscriber sync, dispatch worker, and log writer as separate processes
3. Wait for console input — type `exit` (or press Ctrl+C) to shut down

Shutdown sequence: the three producer processes (listener, sub-worker, dispatch worker) are terminated immediately. The log writer is signaled via a sentinel value and allowed to drain any queued-but-unwritten log messages before it exits, so the log table reflects everything that happened up to shutdown. Once it's confirmed to have exited (or force-terminated after a 5-second timeout), the full log table is exported to `data/logs_<timestamp>.txt`.

To run the listener standalone for testing, `multiple_decoders.py` simulates several RR14 decoders at different timing points (Start/Split/Finish) connecting concurrently and sending sample pulses — useful for exercising the multi-connection handling without real hardware.

## Known limitations

- **No crash recovery**: if one of the three producer processes dies mid-run, `main.py` just hangs waiting on the others. No restart, no alert.
- **Hard shutdown for producers**: `exit` sends `.terminate()` (SIGTERM) to the listener, sub-worker, and dispatch worker immediately — no graceful drain of an in-flight send or DB commit. (The log writer is the exception — see above.)
- **No admin interface**: no way to check logs/counts/status live without querying the DB directly or waiting for the shutdown export.
- **Subscriber emails are not encrypted at rest.**
- **Google Sheet CSV URL is publicly readable** if leaked (no auth gate) — accepted tradeoff for a low-sensitivity subscriber list at this scale.

None of the above blocks running at a small race, but none of it is race-day-hardened either.
