import socket
import os
import sys
import time
import pyaudio
import wave 
import numpy as np


# Define a callback function to handle audio input (non-blocking)
def audio_callback(in_data, frame_count, time_info, status):
    frames.append(in_data)  # Append the incoming audio data to the frames list
    return (in_data, pyaudio.paContinue)  # Continue recording


# ========================================== SERVER INITIALIZATION ==========================================
HOST = '0.0.0.0'  # 0.0.0.0 to accept connections from any IP
PORT = 4670  # Port to listen on
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a socket object
server_socket.bind((HOST, PORT))  # Bind to the port
print('Server bound to port ', PORT)
server_socket.listen(1)  # Wait for a connection
conn, addr = server_socket.accept()  # Establish connection with client
print('Connected to client with IP ', addr)


# ========================================== MAIN PROGRAM ==========================================
recv_signal = conn.recv(1024).decode()  # Receive the signal from the client
if not recv_signal == 'LISTEN':
    print('Client did not send LISTEN signal')
    conn.close()
    sys.exit()

# --- Start Listening (Non-Blocking) ---
p = pyaudio.PyAudio()  # Create an interface to PortAudio
frames = []  # Initialize array to store frames

# Open audio stream (non-blocking)
stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024, stream_callback=audio_callback)
print("Started listening for audio...")
# --- End Start Listening ---

signal = 'SPEAK'
conn.sendall(signal.encode()) # Send the signal to the client

recv_signal = conn.recv(1024).decode()  # Receive the signal from the client
if not recv_signal == 'STOP':
    print('Client did not send STOP signal')
    conn.close()
    sys.exit()

# --- Stop Listening Here ---
# Stop the audio stream when the listening ends.
stream.stop_stream()
stream.close()
p.terminate()  # Close the audio interface

print("Stopped listening for audio.")
# --- End Stop Listening ---

# ========================================== AUDIO PROCESSING ==========================================

# --- Amplify Audio Volume ---
# Convert frames to numpy array for manipulation
audio_data = b''.join(frames)
audio_array = np.frombuffer(audio_data, dtype=np.int16)

# Apply a gain factor to amplify the volume (e.g., 2.0 for doubling the volume)
gain_factor = 5.0  # Amplify the volume by 5 times
amplified_audio_array = np.clip(audio_array * gain_factor, -32768, 32767)  # Ensure no clipping

# Convert back to byte data
amplified_audio_data = amplified_audio_array.astype(np.int16).tobytes()

# --- Save the amplified audio to a .wav file ---
filename = "amplified_recorded_audio.wav"
if os.path.exists(filename):  # Remove the file if it already exists
    os.remove(filename)
wf = wave.open(filename, 'wb')
wf.setnchannels(1)  # Mono audio
wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))  # Set the sample width
wf.setframerate(44100)  # 44.1kHz sample rate
wf.writeframes(amplified_audio_data)  # Write the amplified frames to the file
wf.close()

print(f"Amplified audio saved to {filename}")