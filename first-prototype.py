import groq
import random
import time


CONVERSATION_LENGTH = 15 # Number of exchanges in the conversation
CONVERSATION_TEMPERATURE = 0.5  # Temperature for chat completions
SLEEP_TIME = 1  # Time to wait between messages to simulate a real conversation
CONVINCE_TIME = 4  # Amount of messages there has to be left for one of the models to beging questioning their beliefs
CONVINCE_TIME_DEFINITIVE = 2  # Amount of messages left for one of the models to be definitively convinced
FREQUENCY_PENALTY = 0.5  # Penalty for the frequency of words (eg. not "the the the")
PRESENCE_PENALTY = 0.8  # Penalty for the presence of words of topic (eg. if topic the moon speak about the moon and later of other satellites)


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
        temperature=CONVERSATION_TEMPERATURE,  # Range from 0 to 2, higher values result in more creative responses but may be less coherent
        frequency_penalty=FREQUENCY_PENALTY,   # Range from -2 to 2 lower values result in more repetitive responses
        presence_penalty=PRESENCE_PENALTY,     # Range from -2 to 2 lower values result in more repetitive responses

    )

    # Extract and return the response content
    return chat_completion.choices[0].message.content


def generate_name(client, model, blacklisted=None):
    if blacklisted is None:
        prompt = 'Give yoursef a SINGLE WORD spanish name. Do not simulate a response, I just need a name.'
    else:  # If a blacklisted name is provided, ensure the generated name is different
        prompt = f'Give yoursef a SINGLE WORD spanish name that is not {blacklisted}. Do not simulate a response, I just need a name.'
    name = generate_response(client, prompt, model)  # Ask model
    name = name.replace('\n', '')  # Remove line breaks
    name = ''.join(e for e in name if e.isalnum())  # Remove special characters
    return name


def main():
    remaining_messages = CONVERSATION_LENGTH

    # Model names for the two speakers
    model1 = 'llama-3.3-70b-Specdec'  # The model the first speaker will use
    model2 = 'llama-3.3-70b-Specdec'  # The model the second speaker will use

    # AVAILABLE MODELS
    # LLAMA (META)
    # llama-3.3-70b-Specdec <- Fine
    # llama-3.3-70b-versatile <- Fine
    # llama-3.1-70b-versatile  <- Insists on roleplaying
    # llama-3.1-8b-instant  <- Fine
    # llama-3.2-11b-text-preview  // DECOMISIONED
    # llama-3.2-11b-vision-preview  <- Fine
    # llama-3.2-1b-preview  <- Insists on roleplaying
    # llama-3.2-3b-preview  <- Fine
    # llama-3.2-90b-text-preview  // DECOMISIONED
    # llama-3.2-90b-vision-preview  <- It insists on roleplaying (longer messages as conversation progresses)
    # llama-guard-3-8b  <- Checks if messages are "safe" but doesn't generate text by itself
    # llama3-70b-8192  <- Fine
    # llama3-8b-8192  <- Fine

    # GOOGLE
    # gemma-7b-it  <- Ignores message length and tries to make lists
    # gemma2-9b-it  <- Fine (very short messages and predictable conversations, struggles with formulating arguments)

    # MIXTRAL
    # mixtral-8x7b-32768  <- Problems with messages longer than requested

    # OTHER
    # llava-v1.5-7b-4096-preview  <- Very variable message length but works better than most (sometimes they repeat themselves)

    # Topic of conversation and context
    user_topic = '¿Is time travel real?'  # Ask for the topic
    model1_opinion = 'You belive time travel is real and in fact are convinced you are a time traveler yourself.'
    model2_opinion = 'You do not believe in time travel and in fact think people who do are suffering from some kind of condition.'
    model1_personality = f'{model1_opinion} Make up examples and arguments to defend your position.'
    model2_personality = f'{model2_opinion} Show factual evidence to support your position.'

    # Pre-Cooked parameters
    topic = f'Using arguments and examples, convince me of your opinion on: {user_topic}. Keep responses to a single phrase. Do not repeat arguments. Do not engage in roleplay. If you are told to be convinced, act accordingly.'

    context = []  # Stores the conversation history

    # Create Groq clients
    client1 = groq.Groq(api_key=API_KEY_1)
    client2 = groq.Groq(api_key=API_KEY_2)

    # Ask each client to name themselves (No real practical use but it's funny)
    model1_name = generate_name(client1, model1)
    model2_name = generate_name(client2, model2, model1_name)

    # Randomly choose the starting speaker
    current_speaker = random.choice([1, 2])

    print('Tema: ', topic)
    print('-' * 50)  # Separator for better readability

    ### START OF THE CONVERSATION ###
    # Initial opinion message emphasizing that this is the start of the conversation
    start_message = 'State your belief about the topic in one clear sentence. This is the start of the conversation, so do not refer to any past interactions or arguments. Do not include examples or further elaboration.'

    # Prepare the input prompt for the first speaker
    if current_speaker == 1:
        prompt = f"{model1_personality}\nContext: 'This is the first message of the conversation'\nInstruction: {start_message}\nYour opinion:"
        response = generate_response(client1, prompt, model1)
        print(f"Model 1 ({model1_name}):", response)
        print('-' * 50)
    else:
        prompt = f"{model2_personality}\nContext: 'This is the first message of the conversation'\nInstruction: {start_message}\nYour opinion:"
        response = generate_response(client2, prompt, model2)
        print(f"Model 2 ({model2_name}):", response)
        print('-' * 50)

    remaining_messages -= 1
    time.sleep(SLEEP_TIME)  # Pause briefly to simulate real conversation pacing

    # Switch the speaker
    current_speaker = 2 if current_speaker == 1 else 1

    ### MAIN CONVERSATION LOOP ###
    # Loop for the conversation
    winner_picked = False
    for _ in range(remaining_messages):
        if current_speaker == 1:
            # Prepare the input for model 1
            prompt = f'{model1_personality}\nTopic: {topic}\nContext: {' '.join(context)}\nYour response:'
            response = generate_response(client1, prompt, model1)
            print(f"Model 1 ({model1_name}):", response)
            print('-' * 50)  # Separator for better readability
        else:
            # Prepare the input for model 2
            prompt = f'{model2_personality}\nTopic: {topic}\nContext: {' '.join(context)}\nYour response:'
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

        remaining_messages -= 1
        ### END OF THE CONVERSATION ###
        if remaining_messages <= CONVINCE_TIME and not winner_picked:  # Adjust conversation to end gracefully
            winner_picked = True
            global CONVERSATION_TEMPERATURE
            # Randomly pick a model to "win"
            winner = random.choice([0, 1, 2])  # 0: No winner, 1: Model 1 wins, 2: Model 2 wins
            winner = 1 #TODO: Remove this line
            print('WINNER PICKED')
            if winner == 1:
                CONVERSATION_TEMPERATURE += 0.2  # Increase temperature for the last messages for more creative responses
                model2_personality = f'Your original point of view was: {model2_personality}. However, the arguments presented have started to persuade you, and you are beginning to shift your perspective toward this view: {model1_opinion}. Show subtle signs of being convinced and gradually adjust your stance. Acknowledge the strength of the other speaker\'s arguments, but maintain some reservations. Keep your explanations brief and directly to the point.'
            elif winner == 2:
                CONVERSATION_TEMPERATURE += 0.2  # Increase temperature for the last messages for more creative responses
                model1_personality = f'Your original point of view was: {model1_personality}. However, the arguments presented have started to persuade you, and you are beginning to shift your perspective toward this view: {model2_opinion}. Show subtle signs of being convinced and gradually adjust your stance. Acknowledge the strength of the other speaker\'s arguments, but maintain some reservations. Keep your explanations brief and directly to the point.'
            else:
                CONVERSATION_TEMPERATURE -= 0.2  # Lower temperature for the last messages for less creative responses
                model1_personality += ' Remain very firm in your position.'
                model2_personality += ' Remain very firm in your position.'
            if remaining_messages <= CONVINCE_TIME_DEFINITIVE and winner == 1:
                model2_personality = f'Your original belief was: {model2_personality}. However, after hearing the arguments presented, you are now completely convinced of this viewpoint: {model1_opinion}. Inform the other speaker that you have changed your mind, clearly express your agreement with their perspective, and briefly explain why their arguments persuaded you. Keep your explanation concise and directly to the point.'
            elif remaining_messages <= CONVINCE_TIME_DEFINITIVE and winner == 2:
                model1_personality = f'Your original belief was: {model1_personality}. However, after hearing the arguments presented, you are now completely convinced of this viewpoint: {model2_opinion}. Inform the other speaker that you have changed your mind, clearly express your agreement with their perspective, and briefly explain why their arguments persuaded you. Keep your explanation concise and directly to the point.'
            
        # Pause briefly to simulate real conversation pacing
        time.sleep(SLEEP_TIME)

if __name__ == '__main__':
    main()