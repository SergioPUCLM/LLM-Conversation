import socket
import os
import sys
import time

import pyaudio
import wave
from google.cloud import texttospeech, speech

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./bamboo.json"

HOST = 'localhost'  # Localhost to use in same pc. FOR ONLINE USE, DO NOT CONNECT TO EDUROAM WIFI! 
PORT = 4670


def text_to_speech(text, output_file):
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code="es-ES",
        #name="es-ES-Standard-A",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    with open(output_file, "wb") as out:
        out.write(response.audio_content)
        print(f'Audio content written to file {output_file}')

def play_audio(file_path):
    # Open the WAV file
    wf = wave.open(file_path, 'rb')
    
    # Initialize PyAudio
    p = pyaudio.PyAudio()
    
    # Open stream
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)
    
    # Read data in chunks and play
    data = wf.readframes(1024)
    while data:
        stream.write(data)
        data = wf.readframes(1024)
    
    # Clean up
    stream.stop_stream()
    stream.close()
    p.terminate()
    wf.close()


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

# engine = pyttsx3.init()
# engine.say('TU MADRE ES TAN GORDA QUE CUANDO SALE DEL AGUA EN LA PLAYA, EMERGE LA ATLANTIDA')
# engine.runAndWait()

text = 'EN UN LUGAR de la Mancha, de cuyo nombre no quiero acordarme, no ha mucho tiempo que vivía un hidalgo de los de lanza en astillero, adarga antigua, rocín flaco y galgo corredor.'
output_file = 'output.wav'

text_to_speech(text, output_file)
play_audio(output_file)

signal = 'STOP'
client_socket.sendall(signal.encode()) # Send the signal to the server
client_socket.close()
