import socket
import json
import groq
import os
import sys
import time
import wave
import pyaudio
import numpy as np
import random

from dotenv import load_dotenv
from google.cloud import texttospeech, speech

from interface import DebateConfigInterface

# NOTE: NOW IN INTERFACE
# CONVERSATION_LENGTH = 9  # Number of messages the conversation will last
# CONVERSATION_TEMPERATURE = 1  # Temperature (0 - 2)
# CONVINCE_TIME = 2  # Turns to start convince the other
# CONVINCE_TIME_DEFINITIVE = 1  # Turns to convince the other fully
# FREQUENCY_PENALTY = 0.8  # Avoid repeating the same words (0 - 2)
# PRESENCE_PENALTY = 0.5  # Avoid repeating the same arguments (0 - 2)

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
    Outputs:
    - response: generated response
    """
    chat_completion = client.chat.completions.create(
        messages=messages,  # List of messages
        model=model,  # Model name
        temperature=CONVERSATION_TEMPERATURE,  # Temperature (0 - 2)
        frequency_penalty=FREQUENCY_PENALTY,  # Avoid repeating the same words (0 - 2)
        presence_penalty=PRESENCE_PENALTY,  # Avoid repeating the same arguments (0 - 2)
    )
    return chat_completion.choices[0].message.content


def generate_name(client, model, blacklisted=None):
    """
    Generate a name for an LLM model.
    Attributes:
    - client: Groq client
    - model: model that will generate the name
    - blacklisted: name to avoid (if specified)
    Outputs:
    - name: generated name
    """
    if blacklisted is None:
        prompt = 'Date un nombre de persona en español de UNA SOLA PALABRA. No simules una respuesta, solo necesito un nombre. El nombre no puede ser un número ni un digito.'
    else:
        prompt = f'Date un nombre de persona en español de UNA SOLA PALABRA que no sea {blacklisted}. No simules una respuesta, solo necesito un nombre. El nombre no puede ser un número ni un digito.'
    
    message = [{"role": "user", "content": prompt}]
    name = generate_response(client, model,message)
    name = name.replace('\n', '')
    name = ''.join(e for e in name if e.isalnum())
    return name


def init_server():
    """
    Initialize the server socket.
    """
    HOST = '0.0.0.0'  # 0.0.0.0 to accept connections from any IP
    PORT = 4670  # Port to listen on
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a socket object
    server_socket.bind((HOST, PORT))  # Bind to the port
    server_socket.listen(1)  # Wait for a connection
    print(f"Servidor escuchando en {HOST}:{PORT}...")
    return server_socket


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


def check_personality_change(winner, messages_left, conn, model1_personality, model2_personality, model1_opinion, model2_opinion):
    """
    Check if a personality change is needed.
    Attributes:
    - winner: winner of the debate
    - messages_left: remaining messages
    - conn: connection object
    - model1_personality: original personality of the server
    - model2_personality: original personality of the client
    - model1_opinion: original opinion of the server
    - model2_opinion: original opinion of the client
    Outputs:
    - model1_new_personality: new personality for the server if it was changed, None otherwise
    """
    model1_new_personality = None  # New personality for the server
    model2_new_personality = None  # New personality for the client
    if messages_left == CONVINCE_TIME:  # Halfway through convincing
        if winner == 0:  # Server wins, convince the client (halfway)
            model1_new_personality = f"Tu punto de vista original era: {model1_personality}. Sin embargo, los argumentos presentados han comenzado a persuadirte, y estás empezando a cambiar tu perspectiva hacia esta visión: {model2_opinion}. Muestra señales sutiles de estar convencido y ajusta gradualmente tu postura. Reconoce la fuerza de los argumentos del otro interlocutor, pero mantén algunas reservas. Mantén tus explicaciones breves y directas al grano. Comunica claramente tu cambio de postura y explica brevemente por qué has comenzado a cambiar de opinión."
        else:  # Client wins, convince the server (halfway)
            model2_new_personality = f"Tu punto de vista original era: {model2_personality}. Sin embargo, los argumentos presentados han comenzado a persuadirte, y estás empezando a cambiar tu perspectiva hacia esta visión: {model1_opinion}. Muestra señales sutiles de estar convencido y ajusta gradualmente tu postura. Reconoce la fuerza de los argumentos del otro interlocutor, pero mantén algunas reservas. Mantén tus explicaciones breves y directas al grano. Comunica claramente tu cambio de postura y explica brevemente por qué has comenzado a cambiar de opinión."
    elif messages_left == CONVINCE_TIME_DEFINITIVE:  # Fully convinced
        if winner == 0:  # Server wins, convince the client (fully)
            model1_new_personality = f"Tu punto de vista original era: {model1_personality}. Sin embargo, después de escuchar los argumentos presentados, ahora estás completamente convencido de este punto de vista: {model2_opinion}. Informa al otro interlocutor que has cambiado de opinión, expresa claramente tu acuerdo con su perspectiva y explica brevemente por qué sus argumentos te convencieron. Mantén tu explicación concisa y directa al grano. Comunica claramente tu cambio de postura y explica brevemente por qué has cambiado de opinión."
        else:  # Client wins, convince the server (fully)
            model2_new_personality = f"Tu punto de vista original era: {model2_personality}. Sin embargo, después de escuchar los argumentos presentados, ahora estás completamente convencido de este punto de vista: {model1_opinion}. Informa al otro interlocutor que has cambiado de opinión, expresa claramente tu acuerdo con su perspectiva y explica brevemente por qué sus argumentos te convencieron. Mantén tu explicación concisa y directa al grano. Comunica claramente tu cambio de postura y explica brevemente por qué has cambiado de opinión."

    if model2_new_personality is not None:
        conn.sendall(json.dumps({  # Send the new personality to the client
            'name': "personality",  # Client reconizes personality messages as petitions to change personality
            'message': model2_new_personality
        }).encode('utf-8'))
    return model1_new_personality


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
            return text
        except Exception as e:
            print(f"Error converting speech to text: {e}")
            return ""

def speak(text):
    """Blocking function to convert text to speech and play it"""
    try:
        # Convert text to speech
        output_file = 'temp_speech.wav'
        text_to_speech(text, output_file)
        
        # Play the audio (blocking)
        play_audio(output_file)
        
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


def main():
    # Initialize interface and get configuration
    interface = DebateConfigInterface()
    config = interface.get_config()
    
    # Update global variables with configuration
    global CONVERSATION_LENGTH, CONVERSATION_TEMPERATURE, CONVINCE_TIME
    global CONVINCE_TIME_DEFINITIVE, FREQUENCY_PENALTY, PRESENCE_PENALTY

    CONVERSATION_LENGTH = int(config["CONVERSATION_LENGTH"])
    CONVERSATION_TEMPERATURE = config["CONVERSATION_TEMPERATURE"]
    CONVINCE_TIME = int(config["CONVINCE_TIME"])
    CONVINCE_TIME_DEFINITIVE = int(config["CONVINCE_TIME_DEFINITIVE"])
    FREQUENCY_PENALTY = config["FREQUENCY_PENALTY"]
    PRESENCE_PENALTY = config["PRESENCE_PENALTY"]

    remaining_messages = CONVERSATION_LENGTH  # Remaining messages in the conversation
    
    # Initialize other variables
    model1 = config["model1"]
    model2 = config["model2"]

    # Set up personalities based on config
    model1_opinion = config["model1_opinion"]
    model2_opinion = config["model2_opinion"]
    model1_personality_custom = config["model1_personality"]
    model2_personality_custom = config["model2_personality"]

    # Using proper string concatenation for multi-line strings
    model1_personality = (
        f'Tu opinion es: {model1_opinion}\n\n'
        f'\nTu personalidad es: {model1_personality_custom}'
        '\nUsa argumentos, razones, ejemplos y experiencias personales.'
    )

    model2_personality = (
        f'{model2_opinion} '
        f'\nTu personalidad es: {model2_personality_custom} '
        '\nUsa argumentos, razones, ejemplos y experiencias personales.'
    )

    user_topic = config["topic"]

    topic = (
        f'Con tus propios metodos, convenceme de tu opinión en este tema: {user_topic}. '
        'Muy importante, tus argumentos deben ser breves y concisos, de una oración como mucho. '
        'No repitas argumentos u opiniones. NO DIGAS EL NUMERO DEL ARGUMENTO. '
        'No hagas roleplay ni asumas un rol. Si se te pide que te convenzas, hazlo de manera natural. '
        'Comunica un solo argumento o idea por mensaje para que la conversación sea clara y efectiva. '
        'Si citas a alguien, no lo hagas mas de una vez.'
    )

    start_message = (
        'Expresa claramente tu creencia y posicion sobre el tema en una sola frase clara. '
        'Este es el inicio de la conversacion, por lo que no puedes hacer referencia a '
        'interacciones o argumentos pasados. No incluyas ejemplos o mas elaboracion.'
    )

    model1_name = generate_name(client, model1)  # Generate a name for the server model
    model2_name = generate_name(client, model2, model1_name)  # Generate a name for the client model

    starting_model = random.choice([0, 1]) # 0 = Server starts, 1 = Client starts
    starting_model = 0  #FIXME: THIS IS HERE FOR TESTING PURPOSES. REMOVE THIS LINE ONCE TESTING IS DONE
    winner = random.choice([0, 1])  # What model "wins" the debate (0 = Server, 1 = Client)

    # ============ CONNECTION PHASE ============
    server_socket = init_server()
    conn, addr = server_socket.accept()

    # ============ CONFIGURATION PHASE ============
    try:
        print(f"Conexión establecida con {addr}") 
        data = recv_all(conn).decode('utf-8')  # Receive petition to be initialized
        
        if data== "Iniciame":  # Check the petition
            datos_iniciales = {  # Send the initial configuration to the client
                "message": "Bienvenido al servidor",
                "configuration": {
                    "model": model2,
                    "topic": topic,
                    "personality": model2_personality,
                    "name": model2_name,
                    "starting_model": starting_model,
                    "conversation_temperature": CONVERSATION_TEMPERATURE,
                    "frequency_penalty": FREQUENCY_PENALTY,
                    "presence_penalty": PRESENCE_PENALTY,
                    "start_message": start_message
                }
            }
            
            json_datos = json.dumps(datos_iniciales)  # Pack into a json object
            conn.sendall(json_datos.encode('utf-8'))  # Send the config to the client

        data = recv_all(conn).decode('utf-8')  # Receive the confirmation message from the client that config was received
        if data != "Estoy listo":  # Check the confirmation
            print(f"Error: No se reconoce el comando. Datos recibidos: {data}")
            sys.exit()
        
        # ============ GREETING PHASE ============
        print('Tema: ', topic)
        print('-' * 50)
        
        if starting_model == 0: # We start (Send a greeting to client)
            prompt = f"Context: 'Este es el primer mensaje de la conversación' \
                    \nTema: {topic}\
                    \nInstructiones: {start_message}\nTu opinión:"
            messages = [{"role": "system", "content":model1_personality},
                        {"role": "user", "content": prompt}]
            response = generate_response(client, model1, messages)

            print(f"Server ({model1_name}) dice:", response)
            print('-' * 50)

            send_listen(conn)  # Signal the client to start listening
            print("DEBUG: SENT LISTEN SIGNAL")
            
            print("DEBUG: AWAITING SPEAK SIGNAL")
            # Receive signal to start speaking
            data = recv_all(conn).decode('utf-8')  
            client_msg = json.loads(data)
            if not client_msg['message'] == "SPEAK":
                print(f"Error: No se reconoce el comando. Se esperaba 'SPEAK' y se recibió {client_msg['message']}")
                sys.exit()
            print("DEBUG: RECEIVED SPEAK SIGNAL")

            speak(response)  # Speak the response

            messages.append({"role": "assistant", "content": response})  # Append our response to the message history
            remaining_messages -= 1  # Decrease the remaining messages

            send_stop(conn)  # Signal the client to stop listening
            print("DEBUG: SENT STOP SIGNAL")

        else:
            messages = [{"role": "system", "content":model2_personality},
                        {"role": "user", "content": topic}]
        

        # ============ CONVERSATION PHASE ============
        while True:  # Loop to keep the conversation going
            # Message count checks
            remaining_messages -= 1
            if remaining_messages <= 0:  # If we are out of messages, break the loop
                print("DEBUG: NO MORE MESSAGES")
                break
            new_personality = check_personality_change(winner, remaining_messages, conn, model1_personality, model2_personality, model1_opinion, model2_opinion)
            if new_personality is not None:  # If we need to change the personality, do so
                model1_personality = new_personality
                messages[0] = {"role": "system", "content":model1_personality}
            
            print("DEBUG: AWAITING LISTEN SIGNAL")
            # Receive signal to start listening
            data = recv_all(conn).decode('utf-8')
            print(f"DEBUG: DATA: {data}")
            client_msg = json.loads(data)
            if not client_msg['message'] == "LISTEN":
                print(f"Error: No se reconoce el comando. Datos recibidos: {data}")
                sys.exit()
            print("DEBUG: RECEIVED LISTEN SIGNAL")

            hear()  # Start listening

            send_speak(conn)  # Signal the client to start speaking because we are listening
            print("DEBUG: SENT SPEAK SIGNAL")

            print("DEBUG: AWAITING STOP SIGNAL")
             # Receive signal to stop listening
            data = recv_all(conn).decode('utf-8')
            client_msg = json.loads(data)
            if not client_msg['message'] == "STOP":
                print(f"Error: No se reconoce el comando. Datos recibidos: {data}")
                sys.exit()
            print("DEBUG: RECEIVED STOP SIGNAL")

            message = stop_hearing()  # Stop listening and process the audio

            print(f"Cliente ({model2_name}) dice: {message}")
            print('-' * 50)
            messages.append({"role": "user", "content": message})  # Append the client's message to the message history


            # Message count checks
            remaining_messages -= 1
            if remaining_messages <= 0:  # If we are out of messages, break the loop
                print("DEBUG: NO MORE MESSAGES")
                break
            new_personality = check_personality_change(winner, remaining_messages, conn, model1_personality, model2_personality, model1_opinion, model2_opinion)
            if new_personality is not None:  # If we need to change the personality, do so
                model1_personality = new_personality
                messages[0] = {"role": "system", "content":model1_personality}
            if remaining_messages == 1:  # A single message is left, send a message to the client informing them
                time.sleep(0.1)  # Wait to avoid race conditions
                conn.sendall(json.dumps({  # Send the end message to the client
                    'name': "system",
                    'message': "END-IN-ONE"
                }).encode('utf-8'))


            # Send a message to the client
            prompt = f"{client_msg['message']}\nTema: {topic}\nPersonalidad: {model1_personality}\nRespuesta:"
            messages.append({"role": "user", "content": prompt})  # Create a message to send to the model
            response = generate_response(client, model1, messages)  # Generate a response
            print(f"Server ({model1_name}):", response)
            print('-' * 50)
            messages.append({"role": "assistant", "content": response})  # Append our response to the message history

            send_listen(conn)  # Signal the client to start listening
            print("DEBUG: SENT LISTEN SIGNAL")

            print("DEBUG: AWAITING SPEAK SIGNAL")
            # Receive signal to start speaking
            data = recv_all(conn).decode('utf-8')
            client_msg = json.loads(data)
            if not client_msg['message'] == "SPEAK":
                print(f"Error: No se reconoce el comando. Datos recibidos: {data}")
                sys.exit()
            print("DEBUG: RECEIVED SPEAK SIGNAL")

            speak(response)  # Speak the response

            send_stop(conn)  # Signal the client to stop listening
            print("DEBUG: SENT STOP SIGNAL")


    except KeyboardInterrupt:  # Handle the keyboard interruption
        print("\nSe ha cerrado el servidor manualmente.")
    #except  json.JSONDecodeError:  # Handle JSON decoding error
        #print("\nSe ha producido un error en la comunicación con el cliente")
    #except Exception as e:  # Handle any other exception
        #print("\nSe ha producido un error inesperado:", e)
    finally:  # Close the connection
        conn.close()
        server_socket.close()
        print("Conexión cerrada correctamente.")


if __name__ == '__main__':
    main()
