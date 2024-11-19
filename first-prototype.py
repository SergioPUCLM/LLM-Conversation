import groq
import random
import time


CONVERSATION_LENGTH = 15 # Number of exchanges in the conversation
CONVERSATION_TEMPERATURE = 0.5  # Temperature for chat completions

# Read the API keys for the clients
API_KEY_1 = open('api-key1.txt', 'r').read().strip()  # Groq API key for client 1
API_KEY_2 = open('api-key1.txt', 'r').read().strip()  # Groq API key for client 2

def generate_response(client, prompt, model):
    # Create a message structure for the chat completion
    message = [{"role": "user", "content": prompt}]

    # Generate the response using the chat completion method
    chat_completion = client.chat.completions.create(
        messages=message,
        model=model,
        temperature=CONVERSATION_TEMPERATURE,  # Range from 0 to 1, higher values result in more creative responses but may be less coherent
    )

    # Extract and return the response content
    return chat_completion.choices[0].message.content


def main():
    remaining_messages = CONVERSATION_LENGTH

    # Model names for the two speakers
    model1 = 'llama-3.1-8b-instant'  # The model the first speaker will use
    model2 = 'llama-3.1-8b-instant'  # The model the second speaker will use

    # AVAILABLE MODELS
    # LLAMA (META)
    # llama-3.1-70b-versatile  <- Insists on roleplaying
    # llama-3.1-8b-instant  <- Fine
    # llama-3.2-11b-text-preview  <- Fine
    # llama-3.2-11b-vision-preview  <- Fine
    # llama-3.2-1b-preview  <- Insists on roleplaying
    # llama-3.2-3b-preview  <- Fine
    # llama-3.2-90b-text-preview  <- Fine but needs longer waits
    # llama-3.2-90b-vision-preview  <- It insists on roleplaying (longer messages as conversation progresses)
    # llama-guard-3-8b  <- Checks if messages are "safe" but doesn't generate text by itself
    # llama3-70b-8192  <- Fine
    # llama3-8b-8192  <- Fine

    # GOOGLE
    # gemma-7b-it  <- Ignores message length and tries to make lists
    # gemma2-9b-it  <- Fine (very short messages and predictable conversations)

    # MIXTRAL
    # mixtral-8x7b-32768  <- Problems with messages longer than requested

    # OTHER
    # llava-v1.5-7b-4096-preview  <- Very variable message length but works better than most (sometimes they repeat themselves)

    # Topic of conversation and context
    user_topic = '¿Is time travel real?'  # Ask for the topic
    model1_personality = f'You belive time travel is real and in fact are convinced you are a time traveler yourself. Make up examples and arguments to defend your position. Get progressively more angry.'
    model2_personality = f'You do not believe in time travel and in fact think people who do are suffering from some kind of condition. Show factual evidence to support your position.'

    # Pre-Cooked parameters
    topic = f'Using arguments and examples, convince me of your opinion on: {user_topic}. Keep responses to a single phrase. Do not repeat arguments. Do not engage in roleplay.'

    context = []  # Stores the conversation history

    # Create Groq clients
    client1 = groq.Groq(api_key=API_KEY_1)
    client2 = groq.Groq(api_key=API_KEY_2)

    # Ask each client to name themselves (No real practical use but it's funny)
    prompt_name_1 = f'Give yoursef a SINGLE WORD spanish name. Do not simulate a response, I just need a name.'
    model1_name = generate_response(client1, prompt_name_1, model1)
    model1_name = model1_name.replace('\n', '')
    model1_name = ''.join(e for e in model1_name if e.isalnum())

    prompt_name_2 = f'Give yoursef a SINGLE WORD spanish name that is not {model1_name}. Do not simulate a response, I just need a name.'
    model2_name = generate_response(client2, prompt_name_2, model2) 
    model2_name = model2_name.replace('\n', '')
    model2_name = ''.join(e for e in model2_name if e.isalnum())

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
        print(f"Model 1 ({model1_name}):", response)
        print('-' * 50)
    else:
        prompt = f"{model2_personality}\nContext: 'This is the first message of the conversation'\nInstruction: {start_message}\nYour response:"
        response = generate_response(client2, prompt, model2)
        print(f"Model 2 ({model2_name}):", response)
        print('-' * 50)

    remaining_messages -= 1
    time.sleep(5)  # Pause briefly to simulate real conversation pacing

    # Switch the speaker
    current_speaker = 2 if current_speaker == 1 else 1

    # Loop for the conversation
    for _ in range(remaining_messages):  # Limit the conversation to 15 exchanges for manageability
        if current_speaker == 1:
            # Prepare the input for model 1
            prompt = f"{model1_personality}\nTopic: {topic}\nContext: {' '.join(context)}\nYour response:"
            response = generate_response(client1, prompt, model1)
            print(f"Model 1 ({model1_name}):", response)
            print('-' * 50)  # Separator for better readability
        else:
            # Prepare the input for model 2
            prompt = f"{model2_personality}\nTopic: {topic}\nContext: {' '.join(context)}\nYour response:"
            response = generate_response(client2, prompt, model2)
            print(f"Model 2 ({model2_name}):", response)
            print('-' * 50)  # Separator for better readability
        
        # Add the response to the conversation context
        context.append(f"{response}")

        # Ensure the context doesn't exceed 15 messages
        if len(context) > CONVERSATION_LENGTH:
            context.pop(0)

        # Switch the speaker
        current_speaker = 2 if current_speaker == 1 else 1
        
        # Pause briefly to simulate real conversation pacing
        time.sleep(5)

if __name__ == '__main__':
    main()