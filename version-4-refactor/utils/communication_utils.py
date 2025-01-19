import json
import time


TIME_TO_SLEEP = 0.1

def send_listen(conn):  # Signal other model that we are about to speak and should start listening
    """
    Send a message asking to listen
    Attributes:
    - conn: connection object
    """
    time.sleep(TIME_TO_SLEEP) # Small delay to avoid race conditions
    conn.sendall(json.dumps({
        'name': "system",
        'message': "LISTEN"
    }).encode('utf-8'))


def send_speak(conn):
    """
    Send a message asking to speak
    Attributes:
    - conn: connection object
    """
    time.sleep(TIME_TO_SLEEP) # Small delay to avoid race conditions
    conn.sendall(json.dumps({
        'name': "system",
        'message': "SPEAK"
    }).encode('utf-8'))


def send_stop(conn):
    """
    Send a message asking to stop listening
    Attributes:
    - conn: connection object
    """
    time.sleep(TIME_TO_SLEEP) # Small delay to avoid race conditions
    conn.sendall(json.dumps({
        'name': "system",
        'message': "STOP"
    }).encode('utf-8'))

def recv_all(conn):
    """
    Receive all the data from the client.
    Attributes:
    - conn: connection object
    Outputs:
    - data: received data
    """
    data = b''
    while True:  # Loop to receive all the data
        part = conn.recv(1024)
        data += part  # Append the data
        if len(part) < 1024:  # If the data is less than 1024 bytes, it means that there is no more data to receive
            break
    return data