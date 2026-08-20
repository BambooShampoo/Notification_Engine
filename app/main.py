# main.py
"""Main application for the Notification Engine. Runs the listener, subscription worker and dispatch worker concurrently."""

from multiprocessing import Process
from listener import start_listener
from sub_worker import run_sub_worker
from messenger import run_worker
from load_participants import load_participants

if __name__ == "__main__":
    # Load participants from CSV into the database
    load_participants()

    # Start the listener, subscription worker, and dispatch worker in separate processes
    listener_process = Process(target=start_listener)
    sub_worker_process = Process(target=run_sub_worker)
    dispatch_worker_process = Process(target=run_worker)

    listener_process.start()
    sub_worker_process.start()
    dispatch_worker_process.start()

    # on input "exit"from the console, terminate all processes
    while True:
        user_input = input("Type 'exit' to terminate the application: ")
        if user_input.strip().lower() == "exit":
            print("Terminating all processes...")
            for process in (
                listener_process,
                sub_worker_process,
                dispatch_worker_process,
            ):
                process.terminate()
            break

    for process in (
        listener_process,
        sub_worker_process,
        dispatch_worker_process,
    ):
        process.join()