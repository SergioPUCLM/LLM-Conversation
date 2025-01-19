import groq
import os
import sys
import json
from dotenv import load_dotenv

from utils.communication_utils import send_listen, send_speak, send_stop, recv_all
from utils.common_utils import hear, stop_hearing, speak


class ConversationManager:
    def __init__(self, conversation_temperature, frequency_penalty, presence_penalty, api_key=None, change_voice=False):
        load_dotenv()
        if api_key is None:
            self.api_key = os.getenv('API_KEY_1')
        
        self.client = groq.Groq(api_key=self.api_key)

        self.conversation_temperature = conversation_temperature
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.change_voice = change_voice

    def generate_response(self, model,messages):
        """
        Generate a response from the model given the messages.
        Attributes:
        - client: Groq client
        - model: model name
        - messages: list of messages
        Outputs:
        - response: generated response
        """
        chat_completion = self.client.chat.completions.create(
            messages=messages,  # List of messages
            model=model,  # Model name
            temperature=self. conversation_temperature,  # Temperature (0 - 2)
            frequency_penalty=self.frequency_penalty,  # Avoid repeating the same words (0 - 2)
            presence_penalty=self.presence_penalty,  # Avoid repeating the same arguments (0 - 2)
        )
        return chat_completion.choices[0].message.content

    def start_conversation(self, model_personality, model, topic, start_message, conn):
        """
        Start the conversation with the client.
        """
        prompt = f"Context: 'Este es el primer mensaje de la conversación' \
                    \nTema: {topic}\
                    \nInstructiones: {start_message}\nTu opinión:"
        messages = [{"role": "system", "content":model_personality},
                {"role": "user", "content": prompt}]
        response = self.generate_response(model, messages)

        send_listen(conn)  # Signal the client to start listening

        # Receive signal to start speaking
        data = recv_all(conn).decode('utf-8')  
        client_msg = json.loads(data)
        if not client_msg['message'] == "SPEAK":
            print(f"Error: No se reconoce el comando. Se esperaba 'SPEAK' y se recibió {client_msg['message']}")
            sys.exit()


        speak(response, self.change_voice)  # Speak the response

        messages.append({"role": "assistant", "content": response})  # Append our response to the message history

        send_stop(conn)  # Signal the client to stop listening


        return messages

    def conversation_listen(self, conn):
        """
        Listen to the conversation with the client.
        """
        # Receive signal to start listening
        data = recv_all(conn).decode('utf-8')
        client_msg = json.loads(data)
        if not client_msg['message'] == "LISTEN":
            print(f"Error: No se reconoce el comando. Datos recibidos: {data}")
            sys.exit()

        hear()  # Start listening

        send_speak(conn)  # Signal the client to start speaking because we are listening

        # Receive signal to stop listening
        data = recv_all(conn).decode('utf-8')
        client_msg = json.loads(data)
        if not client_msg['message'] == "STOP":
            print(f"Error: No se reconoce el comando. Datos recibidos: {data}")
            sys.exit()

        message = stop_hearing()  # Stop listening and process the audio


        return ({"role": "user", "content": message}) 

    def conversation_speak(self, conn, model, messages):
        response = self.generate_response(model, messages)  # Generate a response
        messages.append({"role": "assistant", "content": response})  # Append our response to the message history

        send_listen(conn)  # Signal the client to start listening

        # Receive signal to start speaking
        data = recv_all(conn).decode('utf-8')
        client_msg = json.loads(data)
        if not client_msg['message'] == "SPEAK":
            print(f"Error: No se reconoce el comando. Datos recibidos: {data}")
            sys.exit()

        speak(response, self.change_voice)  # Speak the response

        send_stop(conn)  # Signal the client to stop listening


class ConversationManagerClient(ConversationManager):
    def __init__(self, conversation_temperature, frequency_penalty, presence_penalty, api_key=None, change_voice=True):
        if api_key is None:
            api_key = os.getenv('API_KEY_2')
        super().__init__(conversation_temperature, frequency_penalty, presence_penalty, api_key, change_voice)

    def conversation_listen_data(self, conn, msg):
        """
        Listen to the conversation when are you given the data.
        """
        if not msg['message'] == "LISTEN":
            print(f"Error: No se reconoce el comando. Datos recibidos: {data}")
            sys.exit()

        hear()  # Start listening

        send_speak(conn)  # Signal the client to start speaking because we are listening

        # Receive signal to stop listening
        data = recv_all(conn).decode('utf-8')
        msg = json.loads(data)
        if not msg['message'] == "STOP":
            print(f"Error: No se reconoce el comando. Datos recibidos: {data}")
            sys.exit()

        message = stop_hearing()  # Stop listening and process the audio


        return ({"role": "user", "content": message}) 

    def conversation_generate_response(self, conn, model, messages):
        """
        Generate a response from the model given the messages.
        """
        response = self.generate_response(model, messages)  # Generate a response
        messages.append({"role": "assistant", "content": response})  # Append our response to the message history

        send_listen(conn)  # Signal the client to start listening

        return response

    def conversation_speak_text(self, conn, text, msg):
        """
        Speak the text to the server.
        """
        if not msg['message'] == "SPEAK":
            print(f"Error: No se reconoce el comando. Datos recibidos: {msg}")
            sys.exit()

        speak(text, self.change_voice)  # Speak the response

        send_stop(conn)  # Signal the client to stop listening
