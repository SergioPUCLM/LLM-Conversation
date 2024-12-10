import socket
import json
import groq

CONVERSATION_LENGTH = 15
CONVERSATION_TEMPERATURE = 0.5
SLEEP_TIME = 1
CONVINCE_TIME = 4
CONVINCE_TIME_DEFINITIVE = 2
FREQUENCY_PENALTY = 0.5
PRESENCE_PENALTY = 0.8

API_KEY_2 = open('api-key1.txt', 'r').read().strip()

client = groq.Groq(api_key=API_KEY_2)

def generate_response(client, model,messages):
    chat_completion = client.chat.completions.create(
        messages=messages,
        model=model,
        temperature=CONVERSATION_TEMPERATURE,
        frequency_penalty=FREQUENCY_PENALTY,
        presence_penalty=PRESENCE_PENALTY,
    )
    return chat_completion.choices[0].message.content

def generate_name(client, model, blacklisted=None):
    if blacklisted is None:
        prompt = 'Give yoursef a SINGLE WORD spanish name. Do not simulate a response, I just need a name.'
    else:
        prompt = f'Give yoursef a SINGLE WORD spanish name that is not {blacklisted}. Do not simulate a response, I just need a name.'
    
    messages = [{"role": "user", "content": prompt}]
    name = generate_response(client, model,messages)
    name = name.replace('\n', '')
    name = ''.join(e for e in name if e.isalnum())
    return name


def main():

    HOST = 'localhost'  
    PORT = 4670        

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT))
        print(f"Conectado al servidor en {HOST}:{PORT}")
       
        client_socket.sendall("Iniciame".encode('utf-8'))
        print("Mensaje enviado: Iniciame")

        data = client_socket.recv(1024)
        
        data_js = json.loads(data.decode('utf-8'))
        config = data_js['configuration']
        mess   = data_js['message']
        
        print("\n📡 Configuración inicial recibida del servidor:")
        print(json.dumps(mess, indent=4))
        
        client_socket.sendall("Estoy listo".encode('utf-8'))
        print("\nMensaje enviado: Estoy listo")
        
        model = config['model']
        topic = config['topic']
        personality = config['personality']
        name = config['name']

        data = client_socket.recv(1024).decode('utf-8')
        serer_msg = json.loads(data)
        print(f"Server ({serer_msg['name']}) said: {serer_msg['message']}")
        print('-' * 50)

        messages = [{"role": "system", "content":personality},
                    {"role": "user", "content": topic + "\n\n------------------------------\n"+ serer_msg['message']}]
        
        response = generate_response(client, model, messages )
        print(f"Client ({name}):", response)
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
            print(f"Server ({client_msg['name']}) said: {client_msg['message']}")
            print('-' * 50)
            messages = [{"role": "user", "content": client_msg['message']+topic}]
            response = generate_response(client, model, messages)
            print(f"Client ({name}):", response)
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
        print("\n Hubo un error:", e)
    finally:
        client_socket.close()
        print("Conexión cerrada.")

if __name__ == "__main__":
    main()
