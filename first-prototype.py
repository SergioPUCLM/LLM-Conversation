import groq
import random
import time

# Read the API keys for the clients
API_KEY_1 = open('api-key.txt', 'r').read().strip()  # Groq API key for client 1
API_KEY_2 = open('api-key.txt', 'r').read().strip()  # Groq API key for client 2

def generate_response(client, prompt, model):
    # Create a message structure for the chat completion
    message = [{"role": "user", "content": prompt}]

    # Generate the response using the chat completion method
    chat_completion = client.chat.completions.create(
        messages=message,
        model=model
    )

    # Extract and return the response content
    return chat_completion.choices[0].message.content


def main():
    # Model names for the two speakers
    model1 = 'llama3-70b-8192'  # The model the first speaker will use
    model2 = 'llama3-70b-8192'  # The model the second speaker will use

    # Topic of conversation
    #topic = 'Talk about whether Spanish potato omelette should be served with or without ketchup. Convince me of your opinion.'
    topic = 'Convenceme de de tu opinion sobre si la tortilla de patata debe servirse con o sin ketchup.'
    context = []  # Stores the conversation history

    # Personalities for each model
    #model1_personality = 'Act aggresive and assertive. You really like ketchup on Spanish potato omelette. Keep responses to 1 paragraph.'
    #model2_personality = 'Act calm and collected. You hate ketchup on Spanish potato omelette. Keep responses to 1 paragraph.'
    model1_personality = 'Actua de forma tranquila. Te gusta mucho el ketchup en la tortilla de patata. Mantén las respuestas a 1 frase. Dirigete a mi en segunda persona. No repitas argumentos.'
    model2_personality = 'Actua de forma agresiva. Odias el ketchup en la tortilla de patata. Mantén las respuestas a 1 frase. Dirigete a mi en segunda persona. No repitas argumentos.'

    # Create Groq clients
    client1 = groq.Groq(api_key=API_KEY_1)
    client2 = groq.Groq(api_key=API_KEY_2)

    # Randomly choose the starting speaker
    current_speaker = random.choice([1, 2])

    # Start the conversation loop
    print('Tema: ', topic)

    for _ in range(15):  # Limit the conversation to 15 exchanges for manageability
        if current_speaker == 1:
            # Prepare the input for model 1
            prompt = f"{model1_personality}\nTopic: {topic}\nContext: {' '.join(context)}\nYour response:"
            response = generate_response(client1, prompt, model1)
            print("Model 1 (IA Calmada):", response)
            print('-' * 50)  # Separator for better readability
        else:
            # Prepare the input for model 2
            prompt = f"{model2_personality}\nTopic: {topic}\nContext: {' '.join(context)}\nYour response:"
            response = generate_response(client2, prompt, model2)
            print("Model 2 (IA Agresiva):", response)
            print('-' * 50)  # Separator for better readability
        
        # Add the response to the conversation context
        context.append(f"Model {current_speaker}: {response}")

        # Ensure the context doesn't exceed 15 messages
        if len(context) > 15:
            context.pop(0)

        # Switch the speaker
        current_speaker = 2 if current_speaker == 1 else 1
        
        # Pause briefly to simulate real conversation pacing
        time.sleep(5)

if __name__ == '__main__':
    main()