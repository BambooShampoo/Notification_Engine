# multiple_decoders.py
"""Multiple decoders from different timing points. For resting engine"""



import socket
import threading
import time

TIMING_POINTS = {"START", "FINISH", "SPLIT1"}

HOST = "localhost"
PORT = 3099

# seperate pulses for each timing point, each pulse should be a string that ends with the \t delimiter your listener splits on. The pulses should be in the format of the JSON object that the listener expects.
PULSES_START = [
    '{"ID":115,"PID":8,"TimingPoint":"START","Result":-10,"Time":56440.841,"Invalid":false,"Bib":6767}\t',
    '{"ID":110,"PID":8,"TimingPoint":"START","Result":-10,"Time":56440.841,"Invalid":false,"Bib":8398}\t',
    '{"ID":100,"PID":8,"TimingPoint":"START","Result":-10,"Time":56440.841,"Invalid":false,"Bib":8397}\t',
    '{"ID":105,"PID":8,"TimingPoint":"START","Result":-10,"Time":56440.841,"Invalid":false,"Bib":7}\t',
    '{"ID":108,"PID":8,"TimingPoint":"START","Result":-10,"Time":56440.841,"Invalid":false,"Bib":6868}\t',
]

PULSES_SPLIT1 = [
    '{"ID":115,"PID":8,"TimingPoint":"SPLIT1","Result":-10,"Time":56440.841,"Invalid":false,"Bib":6767}\t',
    '{"ID":110,"PID":8,"TimingPoint":"SPLIT1","Result":-10,"Time":56440.841,"Invalid":false,"Bib":8398}\t',
    '{"ID":100,"PID":8,"TimingPoint":"SPLIT1","Result":-10,"Time":56440.841,"Invalid":false,"Bib":8397}\t',
    '{"ID":105,"PID":8,"TimingPoint":"SPLIT1","Result":-10,"Time":56440.841,"Invalid":false,"Bib":7}\t',
    '{"ID":108,"PID":8,"TimingPoint":"SPLIT1","Result":-10,"Time":56440.841,"Invalid":false,"Bib":6868}\t',
]

PULSES_FINISH = [
    '{"ID":115,"PID":8,"TimingPoint":"FINISH","Result":-10,"Time":56440.841,"Invalid":false,"Bib":6767}\t',
    '{"ID":116,"PID":8,"TimingPoint":"FINISH","Result":-10,"Time":56440.841,"Invalid":false,"Bib":8398}\t',
    '{"ID":117,"PID":8,"TimingPoint":"FINISH","Result":-10,"Time":56440.841,"Invalid":false,"Bib":8397}\t',
    '{"ID":118,"PID":8,"TimingPoint":"FINISH","Result":-10,"Time":56440.841,"Invalid":false,"Bib":7}\t',
    '{"ID":119,"PID":8,"TimingPoint":"FINISH","Result":-10,"Time":56440.841,"Invalid":false,"Bib":6868}\t',
]

# Pulse should depend on what tming point the decoder is simulating. For example, if the decoder is simulating a START timing point, it should send pulses for all bib numbers at the START timing point. If the decoder is simulating a FINISH timing point, it should send pulses for all bib numbers at the FINISH timing point, and so on.
def send_pulses(timing_point,pulses):
    if timing_point == "SPLIT1":
        print(f"[{timing_point}] Waiting 2 minutes before sending pulses...")
        time.sleep(120)  # Add a delay before starting the next timing point
    elif timing_point == "FINISH":
        print(f"[{timing_point}] Waiting 4 minutes before sending pulses...")
        time.sleep(240) 
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        print(f"Connected to listener at {HOST}:{PORT}")
        print(f"[{timing_point}] Sending pulses...")
        for pulse in pulses:
            s.sendall(pulse.encode("utf-8"))
            print(f"Sent: {pulse.strip()}")
            time.sleep(1)

def main():
    # create threads for each timing point and connect to the listener respectively, sending pulses for each timing point
    threads = []
    for timing_point in TIMING_POINTS:
        if timing_point == "START":
            pulses = PULSES_START
        elif timing_point == "SPLIT1":
            pulses = PULSES_SPLIT1
        elif timing_point == "FINISH":
            pulses = PULSES_FINISH
        else:
            pulses = []

        thread = threading.Thread(target=send_pulses, args=(timing_point,pulses))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()