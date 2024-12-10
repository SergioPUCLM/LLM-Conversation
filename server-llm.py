import groq
import random
import time
import socket
import json
import sys

CONVERSATION_LENGTH = 15
CONVERSATION_TEMPERATURE = 0.5
SLEEP_TIME = 1
CONVINCE_TIME = 4
CONVINCE_TIME_DEFINITIVE = 2
FREQUENCY_PENALTY = 0.5
PRESENCE_PENALTY = 0.8

API_KEY_1 = open('api-key1.txt', 'r').read().strip()
API_KEY_2 = open('api-key1.txt', 'r').read().strip()

client = groq.Groq(api_key=API_KEY_1)

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

def init_server():
    HOST = '0.0.0.0'
    PORT = 4670
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)
    print(f"Servidor escuchando en {HOST}:{PORT}...")
    return server_socket


def main():
    remaining_messages = CONVERSATION_LENGTH
    model1 = 'llama3-70b-8192'
    model2 = 'llama3-70b-8192'
    user_topic = '¿Is time travel real?'

    model1_opinion = 'You belive time travel is real and in fact are convinced you are a\
        time traveler yourself.'
    model2_opinion = 'You do not believe in time travel and in fact think people who \
        do are suffering from some kind of condition.'
    model1_personality = f'{model1_opinion} Make up examples and arguments to defend \
        your position.'
    model2_personality = f'{model2_opinion} Show factual evidence to support \
        your position.'


    topic = f'Using arguments and examples, convince me of your opinion on: {user_topic}. \
        Keep responses to a single phrase. Do not repeat arguments.\
        NOT SAY THE NUMBER OF THE ARGUMENT\
        Do not engage in roleplay. If you are told to be convinced, act accordingly.'
 
    model1_name = generate_name(client, model1)
    model2_name = generate_name(client, model2, model1_name)

    server_socket = init_server()
    conn, addr = server_socket.accept()


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
        start_message = 'State your belief about the topic in one clear sentence. This is the \
                        start of the conversation, so do not refer to any past interactions\
                        or arguments. Do not include examples or further elaboration.'

        print('Tema: ', topic)
        print('-' * 50)
        
        prompt = f"Context: 'This is the first message of the conversation' \
                \nTopic: {topic}\
                \nInstruction: {start_message}\nYour opinion:"


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
        print("\n Hubo un error en la comunicación con el cliente")
    except Exception as e:
        print("\n Hubo un error:", e)
    finally:
        conn.close()
        server_socket.close()


if __name__ == '__main__':
    main()
