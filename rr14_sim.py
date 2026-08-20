import socket
import time

HOST = "localhost"
PORT = 3099

PULSES = [
    #'{"ID":110,"PID":8,"TimingPoint":"STARTFINISH","Result":-10,"Time":56440.841,"Invalid":false,"Bib":8398}\t',
    #'{"ID":100,"PID":8,"TimingPoint":"STARTFINISH","Result":-10,"Time":56440.841,"Invalid":false,"Bib":8397}\t',
    #'{"ID":105,"PID":8,"TimingPoint":"STARTFINISH","Result":-10,"Time":56440.841,"Invalid":false,"Bib":7}\t',
    #'{"ID":108,"PID":8,"TimingPoint":"STARTFINISH","Result":-10,"Time":56440.841,"Invalid":false,"Bib":6868}\t',
    '{"ID":115,"PID":8,"TimingPoint":"STARTFINISH","Result":-10,"Time":56440.841,"Invalid":false,"Bib":6767}\t',
]


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        print(f"Connected to listener at {HOST}:{PORT}")

        for pulse in PULSES:
            s.sendall(pulse.encode("utf-8"))
            print(f"Sent: {pulse.strip()}")
            time.sleep(1)


if __name__ == "__main__":
    main()