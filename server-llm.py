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


def main():
    remaining_messages = CONVERSATION_LENGTH
    model1 = 'llama3-70b-8192'  # Model for server
    model2 = 'llama3-70b-8192'  # Model for client
    user_topic = '¿Crees que es posible viajar en el tiempo?'

    # Personalities and opinions
    model1_opinion = 'Crees que los viajes en el tiempo son reales y de hecho estás convencido \
        de que eres un viajero del tiempo.'
    model2_opinion = 'No crees en los viajes en el tiempo y de hecho piensas que las personas que lo hacen \
        sufren de algún tipo de trastorno mental.'
    model1_personality = f'{model1_opinion} Inventate argumentos y datos para defender tu opinión.'
    model2_personality = f'{model2_opinion} Muestra datos reales y argumentos para defender tu opinión.'

    topic = f'Using arguments and examples, convince me of your opinion on: {user_topic}. \
        Keep responses to a single phrase. Do not repeat arguments. \
        NOT SAY THE NUMBER OF THE ARGUMENT. \
        Do not engage in roleplay. If you are told to be convinced, act accordingly.'
    
    topic = f'Usando argumentos y ejemplos, convénceme de tu opinión sobre este tema: {user_topic}. \
        Mantén las respuestas a una sola frase. No repitas argumentos.\
        NO DIGAS EL NÚMERO DEL ARGUMENTO\
        No te involucres en juegos de rol ni roleplay. Si se te indica de que te convenzacas con otro argumento, \
        actúa en consecuencia.'
 
    model1_name = generate_name(client, model1)  # Generate a name for the server model
    model2_name = generate_name(client, model2, model1_name)  # Generate a name for the client model

    # ============ CONNECTION PHASE ============
    server_socket = init_server()
    conn, addr = server_socket.accept()

    # ============ CONFIGURATION PHASE ============
    try:
        print(f"Conexión establecida con {addr}")
        data = conn.recv(1024).decode('utf-8')
        
        if data== "Iniciame":
            datos_iniciales = {
                "message": "Bienvenido al servidor",
                "configuration": {
                    "model": model2,
                    "topic": topic,
                    "personality": model2_personality,
                    "name": model2_name
                }
            }
            
            json_datos = json.dumps(datos_iniciales)
            
            conn.sendall(json_datos.encode('utf-8'))

        data = conn.recv(1024).decode('utf-8')
        if data != "Estoy listo":
            print("Error: No se reconoce el comando")
            sys.exit()
        
        # INITIALIZE CONVERSATION
        start_message = 'Expresa claramente tu creencia y posición sobre el tema en una sola frase clara. Este es el \
                        inicio de la conversación, por lo que no puedes hacer referencia a interacciones \
                        o argumentos pasados. No incluyas ejemplos o más elaboración.'

        print('Tema: ', topic)
        print('-' * 50)
        
        prompt = f"Context: 'Este es el primer mensaje de la conversación' \
                \nTema: {topic}\
                \nInstructiones: {start_message}\nTu opinión:"


        messages = [{"role": "system", "content":model1_personality},
                    {"role": "user", "content": prompt}]
        
        response = generate_response(client, model1, messages )

        print(f"Model 1 ({model1_name}):", response)
        print('-' * 50)

        messages.append({"role": "assistant", "content": response})

        remaining_messages -= 1

        conn.sendall(json.dumps({
                'name': model1_name,
                'message': response
            }).encode('utf-8'))
        

        while True:
            data = conn.recv(1024).decode('utf-8')
            client_msg = json.loads(data)

            print(f"Cliente ({client_msg['name']}) dice: {client_msg['message']}")
            print('-' * 50)

            messages = [{"role": "user", "content": client_msg['message']+ topic}]

            response = generate_response(client, model1, messages)
            print(f"Server ({model1_name}):", response)
            print('-' * 50)

            messages.append({"role": "assistant", "content": response})
            remaining_messages -= 1

            conn.sendall(json.dumps({
                'name': model1_name,
                'message': response
            }).encode('utf-8')) 

            if remaining_messages < 5:
                break
    except KeyboardInterrupt:
        print("\nServidor cerrado manualmente.")
    except  json.JSONDecodeError:
        print("\nHubo un error en la comunicación con el cliente")
    except Exception as e:
        print("\nHubo un error:", e)
    finally:
        conn.close()
        server_socket.close()


if __name__ == '__main__':
    main()
