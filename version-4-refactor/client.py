import os
import sys
import socket
import json
import time
import threading

import groq

from dotenv import load_dotenv

from utils.common_utils import hear, stop_hearing, speak, show_speaking_window
from utils.communication_utils import send_listen, send_speak, send_stop

CONVERSATION_TEMPERATURE = None
FREQUENCY_PENALTY = None
PRESENCE_PENALTY = None

load_dotenv()  # Load the environment variables
client = groq.Groq(api_key=os.getenv('API_KEY_2'))


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
        window_thread = threading.Thread(target=show_speaking_window, args=("Client",name,), daemon=True)
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
            server_msg = json.loads(data)  # Parse the data
            
            # System message handling
            if server_msg['message'] == "END": # If we recieve an END, end the conversation
                print("DEBUG: END SIGNAL RECIEVED, STOPPING CONVERSATION INMEDIADELY")
                break
            elif server_msg['message'] == "END-IN-ONE":  # If the message is "END-IN-ONE", end the conversation after the client's message
                    print("DEBUG: END-IN-ONE SIGNAL RECIEVED, STOPPING CONVERSATION AFTER ANOTHER MESSAGE")
                    last_msg = True
            elif server_msg['name'] == 'personality' :  # If not, set the personality
                print("DEBUG: PERSONALITY CHANGE SIGNAL RECIEVED, SWITCHING PERSONALITY")
                personality = server_msg['message']
                messages[0] = {"role": "system", "content":personality}
            elif server_msg['message'] == "LISTEN":  # If we are told to LISTEN (server turn)
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

                send_listen(client_socket)  # Signal the server to start listening
                print("DEBUG: SENT LISTEN SIGNAL")

                print("DEBUG: AWAITING SPEAK SIGNAL")
                

                data = recv_all(client_socket).decode('utf-8')  # Receive the SPEAK command
                try:
                    server_msg = json.loads(data)
                except json.JSONDecodeError:
                    # Split the message in two parts because the server sends two messages at once 
                    # (END or END-IN-ONE and CHANGE PERSONALITY)    
                    split = data.split("}",1)
                    server_msg = json.loads(split[0] + "}")

                    # NOTE: CHECK PERSONALITY CHANGE, END OR END IN ONE
                    if server_msg['message'] == "END": # If we recieve an END, end the conversation
                        print("DEBUG: END SIGNAL RECIEVED, STOPPING CONVERSATION INMEDIADELY")
                        break
                
                    elif server_msg['message'] == "END-IN-ONE":  # If the message is "END-IN-ONE", end the conversation after the client's message
                        print("DEBUG: END-IN-ONE SIGNAL RECIEVED, STOPPING CONVERSATION AFTER ANOTHER MESSAGE")
                 
                        last_msg = True

                    server_msg = json.loads(split[1])
                    if server_msg['name'] == "personality":
                        print("DEBUG: PERSONALITY CHANGE SIGNAL RECIEVED, SWITCHING PERSONALITY")
                        personality = server_msg['message']
                        messages[0] = {"role": "system", "content":personality}
                        
                        data = recv_all(client_socket).decode('utf-8')  # Receive the LISTEN command
                        server_msg = json.loads(data)

                # NOTE: CHECK PERSONALITY CHANGE, END OR END IN ONE
                if server_msg['message'] == "END": # If we recieve an END, end the conversation
                    print("DEBUG: END SIGNAL RECIEVED, STOPPING CONVERSATION INMEDIADELY")
                    break
            
                elif server_msg['message'] == "END-IN-ONE":  # If the message is "END-IN-ONE", end the conversation after the client's message
                    print("DEBUG: END-IN-ONE SIGNAL RECIEVED, STOPPING CONVERSATION AFTER ANOTHER MESSAGE")
                
                    last_msg = True
                    data = recv_all(client_socket).decode('utf-8')  # Receive the LISTEN command
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
                
                response = generate_response(client, model, messages)  # Generate a response from the model
                print(f"Cliente ({name}):", response)
                print('-' * 50)
                messages.append({"role": "assistant", "content": response})  # Append the response to the messages

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
        #print(split) FIXME: Uncomment this line to debug the split
    except Exception as e:  # Handle any other exception
        print("\nSe ha producido un error inesperado:", e)
    finally:
        client_socket.close()
        print("Conexión cerrada correctamente.")

if __name__ == "__main__":
    main()
