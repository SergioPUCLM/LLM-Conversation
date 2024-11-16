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
    model1 = 'llama3-8b-8192'  # The model the first speaker will use
    model2 = 'llama3-8b-8192'  # The model the second speaker will use

    # Topic of conversation and context
    topic = 'Using arguments and examples, convince me of your opinion on: ¿Is time travel real?. Keep responses to 1 phrase. Do not repeat arguments. Address me in second person.'
    context = []  # Stores the conversation history

    # Personalities for each model
    model1_personality = 'You belive time travel is real and in fact are convinced you are a time traveler yourself. Make up examples and arguments to defend your position. Get progressively more angry.'
    model2_personality = 'You do not believe in time travel and in fact think people who do are suffering from some kind of condition. Show factual evidence to support your position.'

    # Create Groq clients
    client1 = groq.Groq(api_key=API_KEY_1)
    client2 = groq.Groq(api_key=API_KEY_2)

    # Randomly choose the starting speaker
    current_speaker = random.choice([1, 2])

    print('Tema: ', topic)
    print('-' * 50)  # Separator for better readability

    # Initial opinion message emphasizing that this is the start of the conversation
    start_message = 'State your belief about the topic in one clear sentence. This is the start of the conversation, so do not refer to any past interactions or arguments. Do not include examples or further elaboration.'

    # Prepare the input prompt for the first speaker
    if current_speaker == 1:
        prompt = f"{model1_personality}\nContext: 'This is the first message of the conversation'\nInstruction: {start_message}\nYour response:"
        response = generate_response(client1, prompt, model1)
        print("Model 1 (Time traveler):", response)
        print('-' * 50)
    else:
        prompt = f"{model2_personality}\nContext: 'This is the first message of the conversation'\nInstruction: {start_message}\nYour response:"
        response = generate_response(client2, prompt, model2)
        print("Model 2 (Non - Traveler):", response)
        print('-' * 50)

    time.sleep(5)  # Pause briefly to simulate real conversation pacing
    context.append(f"Model {current_speaker}: {response}")

    # Switch the speaker
    current_speaker = 2 if current_speaker == 1 else 1

    # Loop for the conversation
    for _ in range(15):  # Limit the conversation to 15 exchanges for manageability
        if current_speaker == 1:
            # Prepare the input for model 1
            prompt = f"{model1_personality}\nTopic: {topic}\nContext: {' '.join(context)}\nYour response:"
            response = generate_response(client1, prompt, model1)
            print("Model 1 (Time traveler):", response)
            print('-' * 50)  # Separator for better readability
        else:
            # Prepare the input for model 2
            prompt = f"{model2_personality}\nTopic: {topic}\nContext: {' '.join(context)}\nYour response:"
            response = generate_response(client2, prompt, model2)
            print("Model 2 (Non - Traveler):", response)
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