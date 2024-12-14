import os
from google.cloud import speech

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"

def speech_to_text(audio_file):
    client = speech.SpeechClient()

    with open(audio_file, "rb") as audio:
        audio_content = audio.read()

    audio_config = speech.RecognitionAudio(content=audio_content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="es-ES"  
    )

    response = client.recognize(config=config, audio=audio_config)

    for result in response.results:
        print(f"Transcripción: {result.alternatives[0].transcript}")

if __name__ == '__main__':
    audio_file = "output.wav"
    speech_to_text(audio_file)
