# main.py
"""Main application for the Notification Engine. Runs the listener, logger,subscription worker and dispatch worker concurrently."""

from multiprocessing import Queue,Process,freeze_support
from listener import start_listener
from sub_worker import run_sub_worker
from messenger import run_worker
from load_participants import load_participants
from log_queue import write_log, add_log, export_log, set_queue
from db import clear_all_tables, has_data
from datetime import datetime, UTC


if __name__ == "__main__":
    # For Windows support, trying to package thing so that device that doesnt have IDE and python install can just run
    freeze_support()  
    shared_log_queue = Queue() # for logging consistency
    set_queue(shared_log_queue)  # so main.py's own add_log() calls work too

    if has_data():
        while True:
            answer = input("Existing race data found. Wipe it before starting? (Y/N): ").strip().lower()
            if answer in ("y", "n"):
                break
            print("Please type Y or N.")

        if answer == "y":
            # TODO: export_log() first, so the old race's logs are saved before the wipe
            export_log()
            clear_all_tables()
            add_log("MAIN", datetime.now(UTC), f"All Tables Cleared for next race, Ready for new race","INFO")
    
    # Load participants from CSV into the database
    load_participants()
    add_log("MAIN", datetime.now(UTC), "added participants from CSV to database","INFO")


    # Start the listener, subscription worker, and dispatch worker in separate processes
    listener_process = Process(target=start_listener, args=(shared_log_queue,))
    sub_worker_process = Process(target=run_sub_worker, args=(shared_log_queue,)) # for new subscribers mid race
    dispatch_worker_process = Process(target=run_worker, args=(shared_log_queue,))
    log_process = Process(target=write_log, args=(shared_log_queue,))

    listener_process.start()
    sub_worker_process.start()
    dispatch_worker_process.start()
    log_process.start()

    # CTRL + C froze terminal, needed a another way to close program without starting new terminal
    while True:
        user_input = input("Type 'exit' to terminate the application: ")
        if user_input.strip().lower() == "exit":
            break

    add_log("MAIN", datetime.now(UTC), "Terminating all processes","INFO")
    print("Terminating all processes...")

    producers = (listener_process, sub_worker_process, dispatch_worker_process)

    for process in producers:
        process.terminate()
    for process in producers:
        process.join()

    add_log("MAIN", datetime.now(UTC), "All producers terminated", "INFO")

    add_log(None, None, None, None)  # Signal the log process to terminate
    log_process.join(timeout=5)

    if log_process.is_alive():
        print("Warning: log process did not exit cleanly, forcing termination")
        log_process.terminate()
        log_process.join()
        
    out_path = export_log()
    print(f"Log exported to {out_path}")




    