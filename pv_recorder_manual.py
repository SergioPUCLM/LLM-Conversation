import wave
import struct
import keyboard
from pvrecorder import PvRecorder 
import time


recorder = PvRecorder(device_index=-1, frame_length=512)
audio = []
print("Empieza a grabar cuando se inicializa el script.")
# keyboard.wait('space') 
# print("Grabando... Pulsa la barra espaciadora para parar")
# time.sleep(0.2)
try:
    recorder.start()
    while True:
        frame = recorder.read()
        audio.extend(frame)
except KeyboardInterrupt:
    # if keyboard.is_pressed('space'): 
    print("Se para la grabación del tema del debate") 
    # time.sleep(0.2)
    recorder.stop()
    with wave.open("output.wav", "w") as file: 
        file.setparams((1, 2, 16000, 512, "NONE", "NONE"))
        file.writeframes(struct.pack("h" * len(audio), *audio))
finally:
    recorder.delete()



 
