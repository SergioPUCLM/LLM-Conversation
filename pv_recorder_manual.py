import wave
import struct
from pvrecorder import PvRecorder

# Prototipo para captar el audio desde python a tiempo real

# Configuración del grabador
DEVICE_INDEX = -1  # Índice del dispositivo (-1 para usar el predeterminado)
FRAME_LENGTH = 512  # Longitud de cada fotograma
OUTPUT_FILE = "prueba.wav"  # Archivo donde se guardará el audio grabado

# Crear instancia del grabador
recorder = PvRecorder(device_index=DEVICE_INDEX, frame_length=FRAME_LENGTH)
audio = []

try:
    print("Comenzando la grabación. Presiona Ctrl+C para detener.")
    recorder.start()

    while True:
        frame = recorder.read()
        audio.extend(frame)  # Agregar los datos capturados al buffer
except KeyboardInterrupt:
    print("\nGrabación detenida.")
    recorder.stop()

    # Guardar el audio en un archivo WAV
    print(f"Guardando el audio en {OUTPUT_FILE}...")
    with wave.open(OUTPUT_FILE, 'w') as f:
        f.setnchannels(1)  # Canal mono
        f.setsampwidth(2)  # 2 bytes por muestra (16 bits)
        f.setframerate(16000)  # Frecuencia 
        f.writeframes(struct.pack("h" * len(audio), *audio))
    print("Archivo guardado .")
finally:
    recorder.delete()


