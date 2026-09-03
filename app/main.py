# main.py
"""Main application for the Notification Engine. Runs the listener, logger,subscription worker and dispatch worker concurrently."""

from multiprocessing import Process,freeze_support
from listener import start_listener
from sub_worker import run_sub_worker
from messenger import run_worker
from load_participants import load_participants
from multiprocessing import Queue, Process
from log_queue import write_log, add_log, export_log, set_queue
from db import clear_all_tables
from datetime import datetime, UTC


if __name__ == "__main__":
    ## For Windows support, trying to package thing so that device that doesnt have IDE and python install can just run
    # freeze_support()  
    shared_log_queue = Queue() # for logging consistency
    set_queue(shared_log_queue)  # so main.py's own add_log() calls work too

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

    add_log(None, None, None, None)  # Signal the log process to terminate

    for process in (
        listener_process,
        sub_worker_process,
        dispatch_worker_process
    ):
        process.terminate()

    log_process.join(timeout=5)

    if log_process.is_alive():
        print("Warning: log process did not exit cleanly, forcing termination")
        log_process.terminate()
        log_process.join()
    
    for process in (
        listener_process,
        sub_worker_process,
        dispatch_worker_process
    ):
        process.join()
    
    add_log("MAIN", datetime.now(UTC), "All processes terminated","INFO")
    print("All processes terminated.")

    # We'll have no way to conduct an analysis of how engine ran otherwise 
    export_log()
    add_log("MAIN", datetime.now(UTC), f"Log exported to data/logs_{datetime.now(UTC)}.txt","INFO")

    # No use of data after race is comeplete, wipe to be ready for new race
    # clear_all_tables()
    # add_log("MAIN", datetime.now(UTC), f"All Tables Cleared for next race, Will populate upon running program again","INFO")




    