import wave
import struct
from pynput import keyboard
from pvrecorder import PvRecorder
import time
import os
from google.cloud import speech

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"

def transcribe_audio(audio_file_path):
    client = speech.SpeechClient()

    # Arvhico de entrada
    with open(audio_file_path, "rb") as audio_file:
        audio_content = audio_file.read()

    # Configurar el reconocimiento
    audio = speech.RecognitionAudio(content=audio_content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,  # Frecuencia de muestreo
        language_code="es-ES"  # Español
    )
    response = client.recognize(config=config, audio=audio)
    transcript = ""
    for result in response.results:
        transcript += result.alternatives[0].transcript
    return transcript

def record_audio():
    recorder = PvRecorder(device_index=-1, frame_length=512)
    audio = []
    is_recording = False

    print("Pulsa la barra espaciadora para empezar a grabar. Pulsa nuevamente para detener y guardar.")

    def on_press(key):
        nonlocal is_recording, audio
        try:
            if key == keyboard.Key.space and not is_recording:
                print("Grabando... Pulsa la barra espaciadora para detener.")
                time.sleep(0.1)  
                recorder.start()
                audio = []  
                is_recording = True

            elif key == keyboard.Key.space and is_recording:
                print("Grabación detenida. Guardando archivo...")
                time.sleep(0.1)
                recorder.stop()
                is_recording = False

                
                with wave.open("output.wav", "w") as file:
                    file.setparams((1, 2, 16000, 512, "NONE", "NONE"))
                    file.writeframes(struct.pack("h" * len(audio), *audio))

                print("Archivo guardado como 'output.wav'.")
                return False  
        except Exception as e:
            print(f"Error: {e}")

    def on_release(key):
        if key == keyboard.Key.esc:
            return False

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        while listener.running:
            if is_recording:
                frame = recorder.read()
                audio.extend(frame)

    recorder.delete()

if __name__ == "__main__":
    record_audio()
    # File which has been stored
    audio_file = "output.wav"

    # Transcribe the audio
    print("Transcribiendo el audio...")
    topic = transcribe_audio(audio_file)
    if topic:
        print(f"Le tema es el siguiente: {topic}")
    else:
        print("No se pudo transcribir el tema.")
