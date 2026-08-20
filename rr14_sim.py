import socket
import time

HOST = "localhost"
PORT = 3099

# TODO (Bamboo): paste in one or more real pulses here, each as its own
# string in this list. Don't forget these need to end with the \t
# delimiter your listener splits on.
PULSES = [
    '{"ID":108,"PID":8,"TimingPoint":"STARTFINISH","Result":-10,"Time":56440.841,"Invalid":false,"Bib":8006}\t',
]


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        print(f"Connected to listener at {HOST}:{PORT}")

        for pulse in PULSES:
            s.sendall(pulse.encode("utf-8"))
            print(f"Sent: {pulse.strip()}")
            time.sleep(1)  # TODO (Bamboo): adjust or remove, just spacing sends out so you can watch listener output per-pulse


if __name__ == "__main__":
    main()