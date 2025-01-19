import socket
import json
import threading

from utils.common_utils import show_speaking_window
from utils.communication_utils import recv_all
from utils.conversation_utils import ConversationManagerClient


def check_message(messages, client_socket):
        """
        Check if the message is a system message
        """
        data = recv_all(client_socket).decode('utf-8')
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
                return (True, None)

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
            return (True, None)

        if server_msg['name'] == "personality":
            print("DEBUG: PERSONALITY CHANGE SIGNAL RECIEVED, SWITCHING PERSONALITY")
            personality = server_msg['message']
            messages[0] = {"role": "system", "content":personality}
            
            data = recv_all(client_socket).decode('utf-8')  # Receive the LISTEN command
            server_msg = json.loads(data)

        return (False, server_msg)

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
        start_message = config['start_message']  # Start message

        # load the manager with the configuration
        cm = ConversationManagerClient(config['conversation_temperature'], config['frequency_penalty'], config['presence_penalty'])  # Create a ConversationManager object
        
        # Start the speaking window thread
        window_thread = threading.Thread(target=show_speaking_window, args=("Client",name,), daemon=True)
        window_thread.start()
        
        # ============ GREETING PHASE ============
        if starting_model == 0:  # 0 = Server starts, 1 = Client starts
            message = cm.conversation_listen(conn=client_socket)  # Listen to the server
            
            messages = [{"role": "system", "content":personality},
                        {"role": "user", "content": topic + "\n\n------------------------------\n"+ message["content"]}]
                
        else: # We start (Send a greeting to server)

            # start the conversation
            messages = cm.start_conversation(personality, model, topic, start_message, client_socket)
    
            # Listen the server
            message = cm.conversation_listen(client_socket)
            messages.append(message)

        # ============ CONVERSATION PHASE ============
        while True:
            # Speak
            response = cm.conversation_generate_response(client_socket,model,messages)

            end, msg = check_message(messages, client_socket)
            if end:
                break
            
            cm.conversation_speak_text(client_socket,response,msg)
            
            # Listen the server
            end, msg = check_message(messages, client_socket)
            if end:
                break

            message = cm.conversation_listen_data(client_socket, msg)
            messages.append(message)
            
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
        #print(messages)
        print("Conexión cerrada correctamente.")

if __name__ == "__main__":
    main()
