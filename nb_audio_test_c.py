import socket
import os
import sys
import time
import pyttsx3


HOST = 'localhost'  # Localhost to use in same pc. FOR ONLINE USE, DO NOT CONNECT TO EDUROAM WIFI! 
PORT = 4670
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a socket object
client_socket.connect((HOST, PORT))  # Connect to the server

print('Connected to server in port ', PORT)

signal = 'LISTEN'
client_socket.sendall(signal.encode()) # Send the signal to the server

recv_signal = client_socket.recv(1024).decode()  # Receive the signal from the server
if not recv_signal == 'SPEAK':
    print('Server did not send SPEAK signal')
    client_socket.close()
    sys.exit()

engine = pyttsx3.init()
engine.say('TU MADRE ES TAN GORDA QUE CUANDO SALE DEL AGUA EN LA PLAYA, EMERGE LA ATLANTIDA')
engine.runAndWait()

signal = 'STOP'
client_socket.sendall(signal.encode()) # Send the signal to the server
client_socket.close()
