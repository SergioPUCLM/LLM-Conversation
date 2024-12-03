import os
from google.cloud import speech

# Configurar credenciales de Google Cloud
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"

def transcribe_audio(audio_file_path):
    client = speech.SpeechClient()

    # Leer el archivo de audio
    with open(audio_file_path, "rb") as audio_file:
        audio_content = audio_file.read()

    # Configurar el reconocimiento
    audio = speech.RecognitionAudio(content=audio_content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,  # Frecuencia de muestreo
        language_code="es-ES"  # Español
    )

    # Enviar el audio a Google Speech-to-Text
    response = client.recognize(config=config, audio=audio)

    # Procesar y devolver el texto transcrito
    transcript = ""
    for result in response.results:
        transcript += result.alternatives[0].transcript
    return transcript

if __name__ == "__main__":
    # Archivo de audio que deseas transcribir
    audio_file = "recorded_audio.wav"

    # Transcribir el audio
    print("Transcribiendo el audio...")
    text = transcribe_audio(audio_file)

    if text:
        print(f"Texto transcrito: {text}")
    else:
        print("No se pudo transcribir el audio.")
