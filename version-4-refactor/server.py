import os
import sys
import socket
import json
import time
import random
import threading

import groq

from dotenv import load_dotenv

from interface import DebateConfigInterface
from utils.common_utils import hear, stop_hearing, speak, show_speaking_window
from utils.communication_utils import send_listen, send_speak, send_stop

# NOTE: NOW IN INTERFACE
# CONVERSATION_LENGTH = 9  # Number of messages the conversation will last
# CONVERSATION_TEMPERATURE = 1  # Temperature (0 - 2)
# CONVINCE_TIME = 2  # Turns to start convince the other
# CONVINCE_TIME_DEFINITIVE = 1  # Turns to convince the other fully
# FREQUENCY_PENALTY = 0.8  # Avoid repeating the same words (0 - 2)
# PRESENCE_PENALTY = 0.5  # Avoid repeating the same arguments (0 - 2)



load_dotenv()  # Load the environment variables
api_key = os.getenv('API_KEY_1')  # Get the API key
client = groq.Groq(api_key=api_key)


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
    if messages_left == CONVINCE_TIME and CONVINCE_TIME != 0:  # Halfway through convincing
        if winner == 0:  # Server wins, convince the client (halfway)
            model2_new_personality = f"Tu punto de vista original era: {model2_personality}. Sin embargo, los argumentos presentados han comenzado a persuadirte, y estás empezando a cambiar tu perspectiva hacia esta visión: {model1_opinion}. Muestra señales sutiles de estar convencido y ajusta gradualmente tu postura. Reconoce la fuerza de los argumentos del otro interlocutor, pero mantén algunas reservas. Mantén tus explicaciones breves y directas al grano. Comunica claramente tu cambio de postura y explica brevemente por qué has comenzado a cambiar de opinión."
        else:  # Client wins, convince the server (halfway)
            model1_new_personality = f"Tu punto de vista original era: {model1_personality}. Sin embargo, los argumentos presentados han comenzado a persuadirte, y estás empezando a cambiar tu perspectiva hacia esta visión: {model2_opinion}. Muestra señales sutiles de estar convencido y ajusta gradualmente tu postura. Reconoce la fuerza de los argumentos del otro interlocutor, pero mantén algunas reservas. Mantén tus explicaciones breves y directas al grano. Comunica claramente tu cambio de postura y explica brevemente por qué has comenzado a cambiar de opinión."
    elif messages_left == CONVINCE_TIME_DEFINITIVE:  # Fully convinced
        if winner == 0:  # Server wins, convince the client (fully)
            model2_new_personality = f"Tu punto de vista original era: {model2_personality}. Sin embargo, después de escuchar los argumentos presentados, ahora estás completamente convencido de este punto de vista: {model1_opinion}. Informa al otro interlocutor que has cambiado de opinión, expresa claramente tu acuerdo con su perspectiva y explica brevemente por qué sus argumentos te convencieron. Mantén tu explicación concisa y directa al grano. Comunica claramente tu cambio de postura y explica brevemente por qué has cambiado de opinión."
        else:  # Client wins, convince the server (fully)
            model1_new_personality = f"Tu punto de vista original era: {model1_personality}. Sin embargo, después de escuchar los argumentos presentados, ahora estás completamente convencido de este punto de vista: {model2_opinion}. Informa al otro interlocutor que has cambiado de opinión, expresa claramente tu acuerdo con su perspectiva y explica brevemente por qué sus argumentos te convencieron. Mantén tu explicación concisa y directa al grano. Comunica claramente tu cambio de postura y explica brevemente por qué has cambiado de opinión."

    if model2_new_personality is not None:
        time.sleep(0.1) # Small delay to avoid race conditions
        print("DEBUG: SENDING NEW PERSONALITY TO CLIENT")
        conn.sendall(json.dumps({  # Send the new personality to the client
            'name': "personality",  # Client reconizes personality messages as petitions to change personality
            'message': model2_new_personality
        }).encode('utf-8'))
    return model1_new_personality

def start_conversation(model_personality, model, topic, start_message, conn):
    """
    Start the conversation with the client.
    """
    prompt = f"Context: 'Este es el primer mensaje de la conversación' \
                \nTema: {topic}\
                \nInstructiones: {start_message}\nTu opinión:"
    messages = [{"role": "system", "content":model_personality},
            {"role": "user", "content": prompt}]
    response = generate_response(client, model, messages)

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

    send_stop(conn)  # Signal the client to stop listening
    print("DEBUG: SENT STOP SIGNAL")

    return messages

def conversation_listen(conn):
    """
    Listen to the conversation with the client.
    """
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


    return ({"role": "user", "content": message}) 

def check_message_count(remaining_messages, conn, starting_model):
    """
    Check the remaining messages and send a signal to the client if needed.
    """
    if remaining_messages <= 0:  # If we are out of messages, break the loop
        print("DEBUG: NO MORE MESSAGES")
        print("DEBUG:  SENDING END SIGNAL")
        time.sleep(0.1)
        conn.sendall(json.dumps({
            'name': "system",
            'message': "END"
        }).encode('utf-8'))
        return True

    elif remaining_messages == 1 and starting_model == 1:  # A single message is left, send a message to the client informing them
        if not CONVERSATION_LENGTH%2 == 0:
            print("DEBUG: SENDING END")
            time.sleep(0.1)
            conn.sendall(json.dumps({
                'name': "system",
                'message': "END-IN-ONE"
            }).encode('utf-8'))

    return False       

def main():
    # Initialize interface and get configuration
    try: 
        config_interface = DebateConfigInterface()
        config = config_interface.get_config()

        # Check if the user closed the window
        if config_interface.closed_by_user_action:
            print("La ventana de configuración ha sido cerrada.")
            sys.exit(0)            
  
    except Exception as e:
        print(f"Error al obtener la configuración: {e}")
        sys.exit(1)

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
    #winner (0 = Server, 1 = Client)
    winner = 0  if (starting_model == 0 and CONVERSATION_LENGTH % 2 == 0) or (starting_model == 1 and CONVERSATION_LENGTH % 2 != 0)  else 1 
    
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
        
        # Start the speaking window thread
        window_thread = threading.Thread(target=show_speaking_window, args=("Server",model1_name,), daemon=True)
        window_thread.start()

        # ============ GREETING PHASE ============
        print('Tema: ', topic)
        print('-' * 50)
        
        if starting_model == 0: # We start (Send a greeting to client)

            messages = start_conversation(model_personality=model1_personality, model=model1, topic=topic, start_message=start_message, conn=conn)
            remaining_messages -= 1  # Decrease the remaining messages

           
        else:
            messages = [{"role": "system", "content":model2_personality},
                        {"role": "user", "content": topic}]
        

        # ============ CONVERSATION PHASE ============
        while True:  # Loop to keep the conversation going
            # Listen client
            message = conversation_listen(conn)
            messages.append(message)  # Append the message to the message history
            remaining_messages -= 1

            # Message count checks
            if check_message_count(remaining_messages, conn, starting_model):
                break

            new_personality = check_personality_change(winner, remaining_messages, conn, model1_personality, model2_personality, model1_opinion, model2_opinion)
            if new_personality is not None:  # If we need to change the personality, do so
                model1_personality = new_personality
                messages[0] = {"role": "system", "content":model1_personality}
            
            response = generate_response(client, model1, messages)  # Generate a response

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

            # Message count checks
            remaining_messages -= 1
            
            if check_message_count(remaining_messages, conn, starting_model):
                break

            new_personality = check_personality_change(winner, remaining_messages, conn, model1_personality, model2_personality, model1_opinion, model2_opinion)
            if new_personality is not None:  # If we need to change the personality, do so
                model1_personality = new_personality
                messages[0] = {"role": "system", "content":model1_personality}
            



    except KeyboardInterrupt:  # Handle the keyboard interruption
        print("\nSe ha cerrado el servidor manualmente.")
    except  json.JSONDecodeError:  # Handle JSON decoding error
        print("\nSe ha producido un error en la comunicación con el cliente")
    except Exception as e:  # Handle any other exception
        print("\nSe ha producido un error inesperado:", e)
    finally:  # Close the connection
        conn.close()
        server_socket.close()
        print("Conexión cerrada correctamente.")


if __name__ == '__main__':
    main()
