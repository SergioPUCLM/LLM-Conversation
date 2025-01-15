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
