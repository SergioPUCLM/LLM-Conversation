import groq
import random
import time
import socket
import json
import sys
import os
from dotenv import load_dotenv

CONVERSATION_LENGTH = 15  # Number of messages the conversation will last
CONVERSATION_TEMPERATURE = 0.5  # Temperature (0 - 2)
CONVINCE_TIME = 4  # Turns to start convince the other
CONVINCE_TIME_DEFINITIVE = 2  # Turns to convince the other fully
FREQUENCY_PENALTY = 0.5  # Avoid repeating the same words (0 - 2)
PRESENCE_PENALTY = 0.8  # Avoid repeating the same arguments (0 - 2)

load_dotenv()  # Load the environment variables
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


def generate_name(client, model, blacklisted=None):
    """
    Generate a name for an LLM model.
    Attributes:
    - client: Groq client
    - model: model that will generate the name
    - blacklisted: name to avoid (if specified)
    """
    if blacklisted is None:
        prompt = 'Date un nombre en español de UNA SOLA PALABRA. No simules una respuesta, solo necesito un nombre. El nombre no puede ser un número ni un digito.'
    else:
        prompt = f'Date un nombre en español de UNA SOLA PALABRA que no sea {blacklisted}. No simules una respuesta, solo necesito un nombre. El nombre no puede ser un número ni un digito.'
    
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
    """
    data = b''
    while True:  # Loop to receive all the data
        part = conn.recv(1024)
        data += part  # Append the data
        if len(part) < 1024:  # If the data is less than 1024 bytes, it means that there is no more data to receive
            break
    return data


def main():
    remaining_messages = CONVERSATION_LENGTH
    model1 = 'llama3-70b-8192'  # Model for server
    model2 = 'llama3-70b-8192'  # Model for client
    user_topic = '¿Crees que es posible viajar en el tiempo?'

    # Personalities and opinions
    model1_opinion = 'Crees que los viajes en el tiempo son reales y de hecho estás convencido de que eres un viajero del tiempo.'
    model2_opinion = 'No crees en los viajes en el tiempo y de hecho piensas que las personas que lo hacen sufren de algún tipo de trastorno mental.'
    model1_personality = f'{model1_opinion} Inventate argumentos y datos para defender tu opinión.'
    model2_personality = f'{model2_opinion} Muestra datos reales y argumentos para defender tu opinión.'

    topic = f'Con tus propios metodos, convenceme de tu opinión en este tema: {user_topic}. Manten tus respuestas a una sola frase. No repitas argumentos u opiniones. NO DIGAS EL NUMERO DEL ARGUMENTO. No hagas roleplay ni asumas un rol. Si se te pide que te convenzas, hazlo de manera natural.'

    start_message = f'Expresa claramente tu creencia y posicion sobre el tema en una sola frase clara. Este es el inicio de la conversacion, por lo que no puedes hacer referencia a interacciones o argumentos pasados. No incluyas ejemplos o mas elaboracion.'
 
    model1_name = generate_name(client, model1)  # Generate a name for the server model
    model2_name = generate_name(client, model2, model1_name)  # Generate a name for the client model

    starting_model = random.choice([0, 1]) # 0 = Server starts, 1 = Client starts

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
                    "conversation_length": CONVERSATION_LENGTH,
                    "conversation_temperature": CONVERSATION_TEMPERATURE,
                    "convince_time": CONVINCE_TIME,
                    "convince_time_definitive": CONVINCE_TIME_DEFINITIVE,
                    "frequency_penalty": FREQUENCY_PENALTY,
                    "presence_penalty": PRESENCE_PENALTY,
                    "start_message": start_message
                }
            }
            
            json_datos = json.dumps(datos_iniciales)  # Pack into a json object
            conn.sendall(json_datos.encode('utf-8'))  # Send the config to the client

        data = recv_all(conn).decode('utf-8')  # Receive the confirmation message from the client that config was received
        if data != "Estoy listo":  # Check the confirmation
            print("Error: No se reconoce el comando")
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
            
            response = generate_response(client, model1, messages )

            print(f"Server ({model1_name}) dice:", response)
            print('-' * 50)

            messages.append({"role": "assistant", "content": response})  # Append the response to the messages

            remaining_messages -= 1  # Decrease the remaining messages

            conn.sendall(json.dumps({  # Send the greeting to the client
                    'name': model1_name,
                    'message': response
                }).encode('utf-8'))

        # No else case. If we start, the client will have to send a message outside of the loop to compensate    
        

        # ============ CONVERSATION PHASE ============
        while remaining_messages > 0:  # Loop to keep the conversation going
            data = recv_all(conn).decode('utf-8')  # Receive mesage from the client
            client_msg = json.loads(data)

            print(f"Cliente ({client_msg['name']}) dice: {client_msg['message']}")
            print('-' * 50)

            messages = [{"role": "user", "content": client_msg['message']+ topic}]  # Create a message to send to the model

            response = generate_response(client, model1, messages)  # Generate a response
            print(f"Server ({model1_name}):", response)
            print('-' * 50)

            messages.append({"role": "assistant", "content": response})  # Append the response to the messages
            remaining_messages -= 1

            conn.sendall(json.dumps({  # Send the response to the client
                'name': model1_name,
                'message': response
            }).encode('utf-8')) 

            if remaining_messages < 5:#FIXME: Conversation needs to start dying out in this point
                break
    except KeyboardInterrupt:  # Handle the keyboard interruption
        print("\nSe ha cerrado el servidor manualmente.")
    except  json.JSONDecodeError:  # Handle JSON decoding error
        print("\nSe ha producido un error en la comunicación con el servidor")
    except Exception as e:  # Handle any other exception
        print("\nSe ha producido un error inesperado:", e)
    finally:  # Close the connection
        conn.close()
        server_socket.close()


if __name__ == '__main__':
    main()
