import socket
import json
import groq
import os
from dotenv import load_dotenv

#TODO: These constants should be sent by the server, where everything is configured
CONVERSATION_LENGTH = 15  # Number of messages the conversation will last
CONVERSATION_TEMPERATURE = 0.5  # Temperature (0 - 2)
SLEEP_TIME = 1  # Time to wait between messages
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


def main():
    HOST = 'localhost'  # Localhost to use in same pc. FOR ONLINE USE, DO NOT CONNECT TO EDUROAM WIFI! 
    PORT = 4670        

    try:
        # ============ CONNECTION PHASE ============
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a socket object
        client_socket.connect((HOST, PORT))  # Connect to the server
        print(f"Conectado al servidor en {HOST}:{PORT}")  # Print the connection message
       
        client_socket.sendall("Iniciame".encode('utf-8'))
        print("Mensaje enviado: Iniciame")

        # ============ CONFIGURATION PHASE ============
        data = client_socket.recv(1024)  # Receive the data from the server
        
        data_js = json.loads(data.decode('utf-8'))
        config = data_js['configuration']
        mess = data_js['message']
        
        print("\n📡 Configuración inicial recibida del servidor:")
        print(json.dumps(mess, indent=4))
        
        client_socket.sendall("Estoy listo".encode('utf-8'))
        print("\nMensaje enviado: Estoy listo")
        
        model = config['model']  # Model to use
        topic = config['topic']  # Topic of the conversation
        personality = config['personality']  # Personality of the client
        name = config['name']  # Name of the client

        data = client_socket.recv(1024).decode('utf-8')  
        serer_msg = json.loads(data)
        print(f"Server ({serer_msg['name']}) dice: {serer_msg['message']}")
        print('-' * 50)

        messages = [{"role": "system", "content":personality},
                    {"role": "user", "content": topic + "\n\n------------------------------\n"+ serer_msg['message']}]
        
        response = generate_response(client, model, messages )
        print(f"Cliente ({name}):", response)
        print('-' * 50)

        messages.append({"role": "assistant", "content": response})

        message_to_server = {
            'name': name,
            'message': response
        }
        client_socket.sendall(json.dumps(message_to_server).encode('utf-8'))

        while True:
            data = client_socket.recv(1024).decode('utf-8')
            client_msg = json.loads(data)
            print(f"Server ({client_msg['name']}) dice: {client_msg['message']}")
            print('-' * 50)
            messages = [{"role": "user", "content": client_msg['message']+topic}]
            response = generate_response(client, model, messages)
            print(f"Cliente ({name}):", response)
            print('-' * 50)
            messages.append({"role": "assistant", "content": response})
            message_to_server = {
                'name': name,
                'message': response
            }
            client_socket.sendall(json.dumps(message_to_server).encode('utf-8'))

    except ConnectionRefusedError:
        print("Error: No se pudo conectar al servidor. ¿Está en línea?")
    except KeyboardInterrupt:
        print("\nCerrando el cliente manualmente.")
    except  json.JSONDecodeError:
        print("\n Hubo un error en la comunicación con el servidor")
    except Exception as e:
        print("\nHubo un error:", e)
    finally:
        client_socket.close()
        print("Conexión cerrada.")

if __name__ == "__main__":
    main()
