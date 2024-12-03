import groq
import random
import time
import socket


CONVERSATION_LENGTH = 15 # Number of exchanges in the conversation
CONVERSATION_TEMPERATURE = 0.5  # Temperature for chat completions
SLEEP_TIME = 1  # Time to wait between messages to simulate a real conversation
CONVINCE_TIME = 4  # Amount of messages there has to be left for one of the models to beging questioning their beliefs
CONVINCE_TIME_DEFINITIVE = 2  # Amount of messages left for one of the models to be definitively convinced
API_KEY_1 = open('api-key1.txt', 'r').read().strip()  # Groq API key for client 1 (Server)

START_PROMPT = 'State your belief about the topic in one clear sentence. This is the start of the conversation, so do not refer to any past interactions or arguments. Do not include examples or further elaboration.'

HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 4670  # Port to listen on


def generate_name(client, model, blacklisted=None):
    if blacklisted is None:
        prompt = 'Give yoursef a SINGLE WORD spanish name. Do not simulate a response, I just need a name.'
    else:  # If a blacklisted name is provided, ensure the generated name is different
        prompt = f'Give yoursef a SINGLE WORD spanish name that is not {blacklisted}. Do not simulate a response, I just need a name.'
    name = generate_response(client, prompt, model)  # Ask model
    name = name.replace('\n', '')  # Remove line breaks
    name = ''.join(e for e in name if e.isalnum())  # Remove special characters
    return name


def recv_all(conn):  # Receive all data from a socket
    data = b''
    while True:
        part = conn.recv(1024)
        data += part
        if len(part) < 1024:
            break
    return data.decode()


def main():
    # ======= CONFIGURATION PHASE =======
    global CONVERSATION_TEMPERATURE
    model1 = 'llama3-70b-8192'  # The model the server will use
    model2 = 'llama3-70b-8192'  # The model the client will use

    # Topics and personalities
    user_topic = 'Is time travel real?'  #TODO: Ask for the topic and personalities using voice
    model1_opinion = 'You belive time travel is real and in fact are convinced you are a time traveler yourself.'
    model2_opinion = 'You do not believe in time travel and in fact think people who do are suffering from some kind of condition.'
    model1_personality = f'{model1_opinion} Make up examples and arguments to defend your position.'
    model2_personality = f'{model2_opinion} Show factual evidence to support your position.'
    topic = f'Using arguments and examples, convince me of your opinion on: {user_topic}. Keep responses to a single phrase. Do not repeat arguments. Do not engage in roleplay. If you are told to be convinced, act accordingly.'
    context = []  # Stores the conversation history (Client and server both store this array)

    # Personality changes at the end of the conversation
    half_concinved_m1 = f'Your original point of view was: {model1_personality}. However, the arguments presented have started to persuade you, and you are beginning to shift your perspective toward this view: {model2_opinion}. Show subtle signs of being convinced and gradually adjust your stance. Acknowledge the strength of the other speaker\'s arguments, but maintain some reservations. Keep your explanations brief and directly to the point.'
    half_concinved_m2 = f'Your original point of view was: {model2_personality}. However, the arguments presented have started to persuade you, and you are beginning to shift your perspective toward this view: {model1_opinion}. Show subtle signs of being convinced and gradually adjust your stance. Acknowledge the strength of the other speaker\'s arguments, but maintain some reservations. Keep your explanations brief and directly to the point.'
    concinved_m1 = f'Your original belief was: {model1_personality}. However, after hearing the arguments presented, you are now completely convinced of this viewpoint: {model2_opinion}. Inform the other speaker that you have changed your mind, clearly express your agreement with their perspective, and briefly explain why their arguments persuaded you. Keep your explanation concise and directly to the point.'
    concinved_m2 = f'Your original belief was: {model2_personality}. However, after hearing the arguments presented, you are now completely convinced of this viewpoint: {model1_opinion}. Inform the other speaker that you have changed your mind, clearly express your agreement with their perspective, and briefly explain why their arguments persuaded you. Keep your explanation concise and directly to the point.'

    # CLIENT COMMUNICATION OF PARAMETERS
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)  # Only accept one connection
    print(f"Server listening on {HOST}:{PORT}...")

    model1_name = generate_name(model1, model1)  # Generate name for model 1
    model2_name = generate_name(model2, model2, model1_name)  # Generate name for model 2

    winner = None  # Stores the winner of the conversation

    try:
        conn, addr = server_socket.accept()  # Accept connection
        print(f"Connection established with {addr}")
        conn.sendall(f"TOPIC:{topic}".encode())  # Send topic to client
        conn.sendall(f"PERSONALITY:{model2_personality}".encode())  # Send personality to client (model 2)
        conn.sendall(f"MODEL:{model2}.".encode())  # Send model to client
        conn.sendall(f"NAME:{model2_name}".encode())  # Send name to client
    
        # ======= CONVERSATION PHASE =======
        # Start message

        # Pick a random model to start the conversation
        current_speaker = random.choice([1, 2])  # 1 = Server, 2 = Client
        if current_speaker == 2:
            conn.sendall(f"YOU START".encode())  # Tell the client to start
        
        # Conversation start message
        match current_speaker:
            case 1:
                prompt = f"{model1_personality}\nContext: 'This is the first message of the conversation'\nInstruction: {start_message}\nYour opinion:"
                response = generate_response(model1, prompt, model1)
                conn.sendall(response.encode())  # Send our message to the client
                print(f"Model 1 ({model1_name}):", response)
                context.append(response)
            case 2:
                data = recv_all(conn)  # Receive the client's message
                print(f"\nMessage recieved from {addr}\n")
                context.append(data)

        time.sleep(SLEEP_TIME)  # Wait before sending the next message

        current_speaker = 1 if current_speaker == 2 else 2  # Switch speakers
        remaining_messages -= 1
            
        # Regular conversation loop
        for i in range(CONVERSATION_LENGTH):
            match current_speaker:
                case 1:
                    prompt = f'{model1_personality}\nTopic: {topic}\nContext: {' '.join(context)}\nYour response:'
                    response = generate_response(client1, prompt, model1)
                    conn.sendall(response.encode())  # Send our message to the client
                    print(f"Model 1 ({model1_name}):", response)
                    context.append(response)
                case 2:
                    data = recv_all(conn)  # Receive the client's message
                    print(f"\nMessage recieved from {addr}\n")
                    context.append(data)
            
            if len(context) > CONVERSATION_LENGTH:  # Cut context to the last 15 messages
                context.pop(0)

            current_speaker = 1 if current_speaker == 2 else 2  # Switch speakers

            # ======= CONVINCE PHASE =======
            if remaining_messages <= CONVINCE_TIME and not winner_picked:  # Half convinced
                winner_picked = True
                winner = random.choice([1, 3])  # Pick a random winner (1 = Server, 2 = Client, 3 = None)
                winner = 1 #FIXME: For testing purposes, the server will always win

                match winner:
                    case 1:  # Server wins
                        CONVERSATION_TEMPERATURE += 0.2  # Increase temperature
                        conn.sendall(f"PERSONALITY:{half_convinced_m2}".encode())
                    case 2:
                        CONVERSATION_TEMPERATURE += 0.2  # Increase temperature
                        model1_personality = half_convinced_m1
                    case default:
                        CONVERSATION_TEMPERATURE -= 0.2  # Decrease temperature
            
            if remaining_messages <= CONVINCE_TIME_DEFINITIVE and winner == 1:  # Fully convinced
                match winner:
                    case 1:  # Server wins
                        conn.sendall(f"PERSONALITY:{convinced_m2}".encode())
                    case 2:
                        model1_personality = convinced_m1

            time.sleep(SLEEP_TIME)  # Wait before sending the next message
    
    except KeyboardInterrupt:
        print("\nServer closed manually.")
    finally:
        conn.close()
        server_socket.close()



    

if __name__ == '__main__':
    main()