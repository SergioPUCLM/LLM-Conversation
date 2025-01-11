import socket
import json
import groq
import os
import sys
import time
import wave
import pyaudio
import threading
import signal
import numpy as np

from dotenv import load_dotenv
from google.cloud import texttospeech, speech

from interface import SpeakingWindow

CONVERSATION_TEMPERATURE = None
FREQUENCY_PENALTY = None
PRESENCE_PENALTY = None

# global variable interface
speaking_window = None
program_pid = os.getpid()

# global variables to control the audio
frames = []
audio_stream = None
p_audio = None

load_dotenv()  # Load the environment variables
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./google-credentials.json" # Set the Google credentials
client = groq.Groq(api_key=os.getenv('API_KEY_1'))


def generate_response(client, model,messages):
    """
    Generate a response from the model given the messages.
    Attributes:
    - client: Groq client
    - model: model name
    - messages: list of messages
    """
    chat_completion = client.chat.completions.create(
        messages=messages,  # List of messages
        model=model,  # Model name
        temperature=CONVERSATION_TEMPERATURE,  # Temperature (0 - 2)
        frequency_penalty=FREQUENCY_PENALTY,  # Avoid repeating the same words (0 - 2)
        presence_penalty=PRESENCE_PENALTY,  # Avoid repeating the same arguments (0 - 2)
    )
    return chat_completion.choices[0].message.content


def recv_all(conn):
    """
    Receive all the data from the client.
    Attributes:
    - conn: connection object
    """
    data = b''
    while True:  # Loop to receive all the data
        part = conn.recv(1024)
        data += part  # Append the data
        if len(part) < 1024:  # If the data is less than 1024 bytes, it means that there is no more data to receive
            break
    # Print raw data
    return data


def set_globals(config):
    """
    Set the global variables with the configuration received from the server.
    Attributes:
    - config: configuration dictionary (already parsed)
    """
    global CONVERSATION_TEMPERATURE
    global FREQUENCY_PENALTY
    global PRESENCE_PENALTY
    CONVERSATION_TEMPERATURE = config['conversation_temperature']
    FREQUENCY_PENALTY = config['frequency_penalty']
    PRESENCE_PENALTY = config['presence_penalty']

    
def send_listen(conn):  # Signal other model that we are about to speak and should start listening
    """
    Send a message asking to listen
    Attributes:
    - conn: connection object
    """
    time.sleep(0.1) # Small delay to avoid race conditions
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
    time.sleep(0.1) # Small delay to avoid race conditions
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
    time.sleep(0.1) # Small delay to avoid race conditions
    conn.sendall(json.dumps({
        'name': "system",
        'message': "STOP"
    }).encode('utf-8'))


def audio_callback(in_data, frame_count, time_info, status):
    """Callback for non-blocking audio recording"""
    frames.append(in_data)
    return (in_data, pyaudio.paContinue)

def hear():
    """Non-blocking audio recording function"""
    global frames, audio_stream, p_audio
    
    # Reset frames array
    frames = []
    
    # Initialize PyAudio
    p_audio = pyaudio.PyAudio()
    
    # Open audio stream (non-blocking)
    audio_stream = p_audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=44100,
        input=True,
        frames_per_buffer=1024,
        stream_callback=audio_callback
    )
    
    # Start the stream
    audio_stream.start_stream()

def stop_hearing():
    """Stop recording and process the audio"""
    global audio_stream, p_audio, frames
    
    if audio_stream:
        # Stop and close the stream
        audio_stream.stop_stream()
        audio_stream.close()
        p_audio.terminate()
        
        # Process the recorded audio
        audio_data = b''.join(frames)
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        
        # Amplify the audio
        gain_factor = 5.0
        amplified_audio_array = np.clip(audio_array * gain_factor, -32768, 32767)
        amplified_audio_data = amplified_audio_array.astype(np.int16).tobytes()
        
        # Save to WAV file
        filename = "recorded_speech.wav"
        if os.path.exists(filename):
            os.remove(filename)
            
        wf = wave.open(filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(p_audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(44100)
        wf.writeframes(amplified_audio_data)
        wf.close()
        
        # Convert to text
        try:
            text = speech_to_text(filename)
            speaking_window.update_listening(text)
            return text
        except Exception as e:
            print(f"Error converting speech to text: {e}")
            return ""

def speak(text):
    """Blocking function to convert text to speech and play it"""
    speaking_window.update_speaking(text)
    try:
        # Convert text to speech
        output_file = 'temp_speech.wav'
        text_to_speech(text, output_file)
        
        speaking_window.update_avatar(is_open=False)
        # Play the audio (blocking)
        play_audio(output_file)
        speaking_window.update_avatar(is_open=True)
        # Clean up
        if os.path.exists(output_file):
            os.remove(output_file)
        
    except Exception as e:
        print(f"Error in speak function: {e}")

def speech_to_text(audio_file):
    """
    Convert audio file to text using Google Cloud Speech-to-Text API.  
    """
    client = speech.SpeechClient()
    with open(audio_file, 'rb') as audio_file:
        content = audio_file.read()
    
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=44100,
        language_code="es-ES",
    )
    
    response = client.recognize(config=config, audio=audio)
    
    return response.results[0].alternatives[0].transcript

def text_to_speech(text, output_file):
    """
    Convert text to speech using Google Cloud Text-to-Speech API.
    """
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code="es-ES",
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
    """
    Play the audio file using PyAudio.
    """
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

def show_speaking_window(model):
    global speaking_window
    speaking_window = SpeakingWindow(model)
    speaking_window.window.mainloop()
    close_by_user_action()

def close_by_user_action():
    global speaking_window
    if speaking_window:
        if speaking_window.closed_by_user_action: 
            speaking_window = None
            os.kill(program_pid, signal.SIGINT)

def main():
    HOST = 'localhost'  # Localhost to use in same pc. FOR ONLINE USE, DO NOT CONNECT TO EDUROAM WIFI! 
    PORT = 4670

    try:
        # ============ CONNECTION PHASE ============
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a socket object
        client_socket.connect((HOST, PORT))  # Connect to the server
        print(f"Conectado al servidor en {HOST}:{PORT}")
       
        client_socket.sendall("Iniciame".encode('utf-8'))  # Send a request to be initialized
        print("Mensaje enviado: Iniciame")

        # ============ CONFIGURATION PHASE ============
        data = recv_all(client_socket)  # Receive the config from the server
        
        data_js = json.loads(data.decode('utf-8'))  # Parse the configuration
        config = data_js['configuration']
        mess = data_js['message']
        
        print("\n📡 Configuración inicial recibida del servidor:")
        print(json.dumps(mess, indent=4))  # Print the message contained in the configuration
        
        client_socket.sendall("Estoy listo".encode('utf-8'))  # Send a message to the server informing that we are ready
        print("\nMensaje enviado: Estoy listo")
        
        # Set the configuration variables
        model = config['model']  # Model to use
        topic = config['topic']  # Topic of the conversation
        personality = config['personality']  # Personality of the client
        name = config['name']  # Name of the client
        starting_model = config['starting_model']  # Starting model
        set_globals(config)  # Set the global variables with the configuration
        start_message = config['start_message']  # Start message

        # Start the speaking window thread
        window_thread = threading.Thread(target=show_speaking_window, args=(model,), daemon=True)
        window_thread.start()
        
        # ============ GREETING PHASE ============
        if starting_model == 0:  # 0 = Server starts, 1 = Client starts
            print("DEBUG: AWAITING LISTEN SIGNAL")
            data = recv_all(client_socket).decode('utf-8')  # Receive the LISTEN command
            server_msg = json.loads(data)  # Parse the data
            if not server_msg['message'] == "LISTEN":  # If the message is "LISTEN",
                print(f"Error: No se reconoce el comando. Datos recibidos: {data}")
                sys.exit()
            print("DEBUG: RECIEVED LISTEN SIGNAL")

            hear()  # Start listening

            send_speak(client_socket)  # Signal the client to start speaking because we are listening
            print("DEBUG: SENT SPEAK SIGNAL")


            print("DEBUG: AWAITING STOP SIGNAL")
            data = recv_all(client_socket).decode('utf-8')  # Receive the STOP command
            server_msg = json.loads(data)
            if not server_msg['message'] == "STOP":
                print(f"Error: No se reconoce el comando. Datos recibidos: {data}")
                sys.exit()
            print("DEBUG: RECIEVED STOP SIGNAL")

            message = stop_hearing()  # Stop listening and process the audio

            print(f"Server dice: {message}")
            print('-' * 50)
            messages = [{"role": "system", "content":personality},
                        {"role": "user", "content": topic + "\n\n------------------------------\n"+ message}]
          
            
            # Reply

            response = generate_response(client, model, messages)  # Generate a response from the model
            print(f"Cliente ({name}):", response)
            print('-' * 50)

            send_listen(client_socket)  # Signal the server to start listening
            print("DEBUG: SENT LISTEN SIGNAL")

            print("DEBUG: AWAITING SPEAK SIGNAL")
            data = recv_all(client_socket).decode('utf-8')  # Receive the SPEAK command
            server_msg = json.loads(data)

            if server_msg['name'] == "personality":
                print("DEBUG: PERSONALITY CHANGE SIGNAL RECIEVED, SWITCHING PERSONALITY")
                personality = server_msg['message']
                messages[0] = {"role": "system", "content":personality}

                data = recv_all(client_socket).decode('utf-8')  # Receive the LISTEN command
                server_msg = json.loads(data)
            
            if not server_msg['message'] == "SPEAK":
                print(f"Error: No se reconoce el comando. Datos recibidos: {data}")
                sys.exit()
            print("DEBUG: RECIEVED SPEAK SIGNAL")

            speak(response)  # Speak the response

            messages.append({"role": "assistant", "content": response})  # Append the response to the messages
           
            send_stop(client_socket)  # Signal the server to stop listening
            print("DEBUG: SENT STOP SIGNAL")

        else: # We start (Send a greeting to server)
            prompt = f"Context: 'Este es el primer mensaje de la conversación' \
                    \nTema: {topic}\
                    \nInstructiones: {start_message}\nTu opinión:"
            messages = [{"role": "system", "content":personality},
                        {"role": "user", "content": prompt}]

            response = generate_response(client, model, messages)  # Generate a response from the model
            print(f"Cliente ({name}):", response)
            print('-' * 50)
            messages.append({"role": "assistant", "content": response})  # Append our message to the messages

            send_listen(client_socket)  # Signal the server to start listening
            print("DEBUG: SENT LISTEN SIGNAL")

            print("DEBUG: AWAITING SPEAK SIGNAL")
            data = recv_all(client_socket).decode('utf-8')  # Receive the LISTEN command
            server_msg = json.loads(data)

            if server_msg['name'] == "personality":
                print("DEBUG: PERSONALITY CHANGE SIGNAL RECIEVED, SWITCHING PERSONALITY")
                personality = server_msg['message']
                messages[0] = {"role": "system", "content":personality}

                data = recv_all(client_socket).decode('utf-8')  # Receive the LISTEN command
                server_msg = json.loads(data)

            if not server_msg['message'] == "SPEAK":  # If the message is "SPEAK", start speaking
                print(f"Error: No se reconoce el comando. Datos recibidos: {data}")
                sys.exit()
            print("DEBUG: RECIEVED SPEAK SIGNAL")

            speak(response)  # Speak the response

            send_stop(client_socket)  # Signal the server to stop listening
            print("DEBUG: SENT STOP SIGNAL")

        # ============ CONVERSATION PHASE ============
        last_msg = False  # Flag to indicate if the client will be the last message
        while True:
            print("DEBUG: AWAITING LISTEN SIGNAL OR END SIGNAL OR END-IN-ONE SIGNAL OR PERSONALITY CHANGE")
            data = recv_all(client_socket).decode('utf-8')  # Receive the message from the server
            client_msg = json.loads(data)  # Parse the data
            
            # System message handling
            if client_msg['message'] == "END": # If we recieve an END, end the conversation
                print("DEBUG: END SIGNAL RECIEVED, STOPPING CONVERSATION INMEDIADELY")
                break
            elif client_msg['message'] == "END-IN-ONE":  # If the message is "END-IN-ONE", end the conversation after the client's message
                    print("DEBUG: END-IN-ONE SIGNAL RECIEVED, STOPPING CONVERSATION AFTER ANOTHER MESSAGE")
                    last_msg = True
            elif client_msg['name'] == 'personality' :  # If not, set the personality
                print("DEBUG: PERSONALITY CHANGE SIGNAL RECIEVED, SWITCHING PERSONALITY")
                personality = client_msg['message']
                messages[0] = {"role": "system", "content":personality}
            elif client_msg['message'] == "LISTEN":  # If we are told to LISTEN (server turn)
                print("DEBUG: RECIEVED LISTEN SIGNAL")

                hear()  # Start listening

                send_speak(client_socket)  # Signal the client to start speaking because we are listening
                print("DEBUG: SENT SPEAK SIGNAL")

                print("DEBUG: AWAITING STOP SIGNAL")
                data = recv_all(client_socket).decode('utf-8')  # Receive the STOP command
                print(f"DEBUG: DATA RECIEVED: {data}")
                server_msg = json.loads(data)
                if not server_msg['message'] == "STOP":
                    print(f"Error: No se reconoce el comando. Datos recibidos: {data}")
                    sys.exit()
                print("DEBUG: RECIEVED STOP SIGNAL")

                message = stop_hearing()  # Stop listening and process the audio

                print(f"Server dice: {message}")
                print('-' * 50)

                messages.append({"role": "user", "content": message})  # Append the message to the messages

                # Reply

                response = generate_response(client, model, messages)  # Generate a response from the model
                print(f"Cliente ({name}):", response)
                print('-' * 50)
                messages.append({"role": "assistant", "content": response})  # Append the response to the messages

                send_listen(client_socket)  # Signal the server to start listening
                print("DEBUG: SENT LISTEN SIGNAL")

                print("DEBUG: AWAITING SPEAK SIGNAL")
                data = recv_all(client_socket).decode('utf-8')  # Receive the SPEAK command
                server_msg = json.loads(data)
                
                if server_msg['name'] == "personality":
                    print("DEBUG: PERSONALITY CHANGE SIGNAL RECIEVED, SWITCHING PERSONALITY")
                    personality = server_msg['message']
                    messages[0] = {"role": "system", "content":personality}

                    data = recv_all(client_socket).decode('utf-8')  # Receive the LISTEN command
                    server_msg = json.loads(data)

                if not server_msg['message'] == "SPEAK":
                    print(f"Error: No se reconoce el comando. Datos recibidos: {data}")
                    sys.exit()
                print("DEBUG: RECIEVED SPEAK SIGNAL")

                speak(response)  # Speak the response

                if last_msg:
                    send_stop(client_socket)  # Signal the server to stop listening
                    print("DEBUG: SENT STOP SIGNAL")
                    break

                send_stop(client_socket)  # Signal the server to stop listening
                print("DEBUG: SENT STOP SIGNAL")
            else:
                print("Error: Orden de conversación inesperado")

    except ConnectionRefusedError:  # Handle connection error
        print("Error: No se pudo conectar al servidor. Asegurate de que el servidor esta en linea y la wifi no es eduroam.")
    except KeyboardInterrupt:  # Handle keyboard interruption
        print("\nSe ha cerrado el cliente manualmente.")
    except  json.JSONDecodeError:  # Handle JSON decoding error
        print("\nSe ha producido un error en la comunicación con el servidor")
    except Exception as e:  # Handle any other exception
        print("\nSe ha producido un error inesperado:", e)
    finally:
        client_socket.close()
        print("Conexión cerrada correctamente.")

if __name__ == "__main__":
    main()
