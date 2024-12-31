import groq
import random
import time
import socket
import json
import sys
import os
import pyttsx3
from dotenv import load_dotenv

CONVERSATION_LENGTH = 15  # Number of messages the conversation will last
CONVERSATION_TEMPERATURE = 1  # Temperature (0 - 2)
CONVINCE_TIME = 4  # Turns to start convince the other
CONVINCE_TIME_DEFINITIVE = 2  # Turns to convince the other fully
FREQUENCY_PENALTY = 0.8  # Avoid repeating the same words (0 - 2)
PRESENCE_PENALTY = 0.5  # Avoid repeating the same arguments (0 - 2)

load_dotenv()  # Load the environment variables
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
    
    messages = [{"role": "user", "content": prompt}]
    name = generate_response(client, model,messages)
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
            'name': "system",  # Client reconizes system messages as petitions to change personality
            'message': model2_new_personality
        }).encode('utf-8'))
    return model1_new_personality


def speak_debug(text, voice_id='HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_ES-MX_SABINA_11.0', rate=175):
    """
    Speak the text using a debug local built-in TTS.
    Attributes:
    - text: text to speak
    - voice_id: voice id to use (if no real one is selected, it uses the firs as failsafe)
    - rate: speaking rate
    """
    engine = pyttsx3.init()  # Initialize the TTS engine
    engine.setProperty('voice', voice_id)  # Set the voice
    engine.setProperty('rate', rate)  # Set the rate
    engine.say(text)  # Speak the text
    engine.runAndWait()  # Wait for the TTS to finish (BLOCKING FOR TCP COMMUNICATION OF THE MESSAGE)


def hear_debug():
    print("THIS FUNCTION IS NOT IMPLEMENTED YET, THE MACHINE NEEDS TO START LISTENING HERE")
    return "DEBUG MESSAGE"
    

def send_message(conn, name, message):
    """
    Helper function to send a message to the client in the correct JSON format.
    """
    conn.sendall(json.dumps({'name': name, 'message': message}).encode('utf-8'))

def recv_message(conn):
    """
    Helper function to receive a message from the client in the correct JSON format.
    """
    data = recv_all(conn).decode('utf-8')
    return json.loads(data)

def main():
    remaining_messages = CONVERSATION_LENGTH
    model1 = 'llama3-70b-8192'  # Model for server
    model2 = 'llama3-70b-8192'  # Model for client
    user_topic = '¿Crees que la tortilla de patatas esta mejor con o sin ketchup?'
    context = []  # Context of the conversation

    # Personalities and opinions
    model1_opinion = 'Te gusta mucho el ketchup, especialmente en la tortilla de patatas, y crees que es una combinación deliciosa.'
    model2_opinion = 'No te gusta el ketchup en la tortilla de patatas, prefieres disfrutar del sabor original de la tortilla sin añadirle ningún condimento adicional.'
    model1_personality = f'{model1_opinion} Usa argumentos, razones, ejemplos y experiencias personales para defender tu punto de vista.'
    model2_personality = f'{model2_opinion} Usa argumentos, razones, ejemplos y experiencias personales para defender tu punto de vista.'

    topic = f'Con tus propios metodos, convenceme de tu opinión en este tema: {user_topic}. Muy importante, tus argumentos deben ser breves y concisos, de una oración como mucho. No repitas argumentos u opiniones. NO DIGAS EL NUMERO DEL ARGUMENTO. No hagas roleplay ni asumas un rol. Si se te pide que te convenzas, hazlo de manera natural. Comunica un solo argumento o idea por mensaje para que la conversación sea clara y efectiva. Si citas a alguien, no lo hagas mas de una vez.'

    start_message = f'Expresa claramente tu creencia y posicion sobre el tema en una sola frase clara. Este es el inicio de la conversacion, por lo que no puedes hacer referencia a interacciones o argumentos pasados. No incluyas ejemplos o mas elaboracion.'

    model1_name = generate_name(client, model1)  # Generate a name for the server model
    model2_name = generate_name(client, model2, model1_name)  # Generate a name for the client model

    starting_model = random.choice([0, 1]) # 0 = Server starts, 1 = Client starts
    winner = random.choice([0, 1])  # What model "wins" the debate (0 = Server, 1 = Client)

    # ============ CONNECTION PHASE ============ 
    server_socket = init_server()
    conn, addr = server_socket.accept()

    # ============ CONFIGURATION PHASE ============ 
    try:
        print(f"Conexión establecida con {addr}") 
        data = recv_all(conn).decode('utf-8')  # Receive petition to be initialized
        
        if data == "Iniciame":  # Check the petition
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
            send_message(conn, "system", json_datos)  # Send the config to the client

        data = recv_all(conn).decode('utf-8')  # Receive the confirmation message from the client that config was received
        if data != "Estoy listo":  # Check the confirmation
            print("Error: No se reconoce el comando")
            sys.exit()
        
        # ============ GREETING PHASE ============ 
        print('Tema: ', topic)
        print('-' * 50)
        
        if starting_model == 0: # We start (Send a greeting to client)
            send_message(conn, "system", "LISTEN")  # Signal client to start listening
            data = recv_message(conn)
            if data['message'] != "LISTENING":
                print("Error: Client failed to confirm LISTENING state.")
                sys.exit()

            prompt = f"Context: 'Este es el primer mensaje de la conversación' \
                    \nTema: {topic}\
                    \nInstructiones: {start_message}\nTu opinión:"

            messages = [{"role": "system", "content": model1_personality},
                        {"role": "user", "content": prompt}]
            
            response = generate_response(client, model1, messages)

            print(f"Server ({model1_name}) dice:", response)
            print('-' * 50)
            speak_debug(response)

            messages.append({"role": "assistant", "content": response})  # Append the response to the message history

            send_message(conn, model1_name, response)  # Send the greeting to the client
            send_message(conn, "system", "STOP")  # Signal client that we are done speaking
        
        while True:  # Loop to keep the conversation going
            remaining_messages -= 1
            if remaining_messages <= 0:  # If we are out of messages, break the loop
                break
            new_personality = check_personality_change(winner, remaining_messages, conn, model1_personality, model2_personality, model1_opinion, model2_opinion)
            if new_personality is not None:  # If we need to change the personality, do so
                model1_personality = new_personality
                messages[0] = {"role": "system", "content": model1_personality}

            data = recv_message(conn)
            if data['message'] != "LISTEN":
                print("Error: Client failed to initiate LISTEN state.")
                sys.exit()
            send_message(conn, "system", "LISTENING")  # Confirm to client we are listening

            data = recv_message(conn)
            print(f"Cliente ({data['name']}) dice: {data['message']}")
            print('-' * 50)

            if remaining_messages == 1:  # A single message is left, send a message to the client informing them
                send_message(conn, "system", "END-IN-ONE")

            send_message(conn, "system", "LISTEN")  # Signal client to start listening
            data = recv_message(conn)
            if data['message'] != "LISTENING":
                print("Error: Client failed to confirm LISTENING state.")
                sys.exit()

            prompt = f"{data['message']}\nTema: {topic}\nPersonalidad: {model1_personality}\nRespuesta:"
            messages = [{"role": "user", "content": prompt}]  # Create a message to send to the model
            response = generate_response(client, model1, messages)  # Generate a response
            print(f"Server ({model1_name}):", response)
            print('-' * 50)
            speak_debug(response)
            messages.append({"role": "assistant", "content": response})  # Append the response to the message history
            send_message(conn, model1_name, response)  # Send the response to the client
            send_message(conn, "system", "STOP")  # Signal client that we are done speaking

        send_message(conn, "system", "END")  # Send the end message to the client

    except KeyboardInterrupt:  # Handle the keyboard interruption
        print("\nSe ha cerrado el servidor manualmente.")
    except json.JSONDecodeError:  # Handle JSON decoding error
        print("\nSe ha producido un error en la comunicación con el servidor")
    except Exception as e:  # Handle any other exception
        print("\nSe ha producido un error inesperado:", e)
    finally:  # Close the connection
        conn.close()
        server_socket.close()
        print("Conexión cerrada correctamente.")


if __name__ == '__main__':
    main()
