import pyttsx3
import time

# IF THE TTS SHOWS AN ERROR SAYING THE VOICE ID DOES NOT EXIST, 
# RUN THIS TO FIND WHAT VOICE IDS ARE AVAILABLE IN THE SYSTEM

# Get the list of voices
engine = pyttsx3.init()
voices = engine.getProperty('voices')
for voice in voices:
    print(voice.id)


