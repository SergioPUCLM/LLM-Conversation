import socket
import json
import groq
import os
from dotenv import load_dotenv

CONVERSATION_LENGTH = None
CONVERSATION_TEMPERATURE = None
CONVINCE_TIME = None
CONVINCE_TIME_DEFINITIVE = None
FREQUENCY_PENALTY = None
PRESENCE_PENALTY = None

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


def set_globals(config):
    """
    Set the global variables with the configuration received from the server.
    Attributes:
    - config: configuration dictionary (already parsed)
    """
    global CONVERSATION_LENGTH
    global CONVERSATION_TEMPERATURE
    global CONVINCE_TIME
    global CONVINCE_TIME_DEFINITIVE
    global FREQUENCY_PENALTY
    global PRESENCE_PENALTY
    CONVERSATION_LENGTH = config['conversation_length']
    CONVERSATION_TEMPERATURE = config['conversation_temperature']
    CONVINCE_TIME = config['convince_time']
    CONVINCE_TIME_DEFINITIVE = config['convince_time_definitive']
    FREQUENCY_PENALTY = config['frequency_penalty']
    PRESENCE_PENALTY = config['presence_penalty']


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
        data = client_socket.recv(1024)  # Receive the config from the server
        
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
        set_globals(config)  # Set the global variables with the configuration

        # ============ GREETING PHASE ============
        data = recv_all(client_socket).decode('utf-8')  # Receive the greeting from the server
        serer_msg = json.loads(data)  # Parse the data
        print(f"Server ({serer_msg['name']}) dice: {serer_msg['message']}")
        print('-' * 50)  

        messages = [{"role": "system", "content":personality},
                    {"role": "user", "content": topic + "\n\n------------------------------\n"+ serer_msg['message']}]
        
        response = generate_response(client, model, messages)  # Generate a response from the model
        print(f"Cliente ({name}):", response)
        print('-' * 50)

        messages.append({"role": "assistant", "content": response})  # Append the response to the messages

        message_to_server = {  # Create a message to send to the server
            'name': name,
            'message': response
        }  
        client_socket.sendall(json.dumps(message_to_server).encode('utf-8'))  # Send the message to the server

        # ============ CONVERSATION PHASE ============
        while True:
            data = recv_all(client_socket).decode('utf-8')  # Receive the message from the server
            client_msg = json.loads(data)  # Parse the data
            print(f"Server ({client_msg['name']}) dice: {client_msg['message']}")
            print('-' * 50)
            messages = [{"role": "user", "content": client_msg['message']+topic}]  # Append the message to the messages
            response = generate_response(client, model, messages)  # Generate a response from the model
            print(f"Cliente ({name}):", response)
            print('-' * 50)
            messages.append({"role": "assistant", "content": response})  # Append the response to the messages
            message_to_server = {  # Create a message to send to the server
                'name': name,
                'message': response
            }
            client_socket.sendall(json.dumps(message_to_server).encode('utf-8'))  # Send the message to the server

    except ConnectionRefusedError:  # Handle connection error
        print("Error: No se pudo conectar al servidor. Asegurate de que el servidor esta en linea y la wifi no es eduroam.")
    except KeyboardInterrupt:  # Handle keyboard interruption
        print("\nSe ha cerrado el cliente manualmente.")
    except  json.JSONDecodeError:  # Handle JSON decoding error
        print("\nSe ha producido un error en la comunicación con el servidor")
    #except Exception as e:  # Handle any other exception
        print("\nSe ha producido un error inesperado:", e)
    finally:
        client_socket.close()
        print("Conexión cerrada.")

if __name__ == "__main__":
    main()
