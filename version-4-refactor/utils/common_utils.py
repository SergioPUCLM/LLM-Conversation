import os
import signal
import wave
import pyaudio
import numpy as np

from google.cloud import texttospeech, speech

from interface import SpeakingWindow


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./google-credentials.json" # Set the Google credentials

# global variables to control the audio
frames = []
audio_stream = None
p_audio = None

# global variable interface
speaking_window = None
program_pid = os.getpid()


def _audio_callback(in_data, frame_count, time_info, status):
    """
    Callback for non-blocking audio recording
    """
    frames.append(in_data)
    return (in_data, pyaudio.paContinue)

def hear():
    """
    Non-blocking audio recording function
    """
    global frames, audio_stream, p_audio
    
    # Reset frames array
    frames = []
    
    # Initialize PyAudio
    p_audio = pyaudio.PyAudio()
    
    # Open audio stream (non-blocking)
    audio_stream = p_audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=44100,
        input=True,
        frames_per_buffer=1024,
        stream_callback=_audio_callback
    )
    
    # Start the stream
    audio_stream.start_stream()

def stop_hearing():
    """
    Stop recording and process the audio
    """
    global audio_stream, p_audio, frames
    
    if audio_stream:
        # Stop and close the stream
        audio_stream.stop_stream()
        audio_stream.close()
        p_audio.terminate()
        
        # Process the recorded audio
        audio_data = b''.join(frames)
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        
        # Amplify the audio
        gain_factor = 5.0
        amplified_audio_array = np.clip(audio_array * gain_factor, -32768, 32767)
        amplified_audio_data = amplified_audio_array.astype(np.int16).tobytes()
        
        # Save to WAV file
        filename = "recorded_speech.wav"
        if os.path.exists(filename):
            os.remove(filename)
            
        wf = wave.open(filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(p_audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(44100)
        wf.writeframes(amplified_audio_data)
        wf.close()
        
        # Convert to text
        try:
            text = speech_to_text(filename)
            speaking_window.update_listening(text)
            return text
        except Exception as e:
            print(f"Error converting speech to text: {e}")
            return ""

def speak(text):
    """
    Blocking function to convert text to speech and play it
    """
    speaking_window.update_speaking(text)
    try:
        # Convert text to speech
        output_file = 'temp_speech.wav'
        text_to_speech(text, output_file)
        
        speaking_window.update_avatar(is_open=False)
        # Play the audio (blocking)
        play_audio(output_file)
        speaking_window.update_avatar(is_open=True)
        # Clean up
        if os.path.exists(output_file):
            os.remove(output_file)
            
    except Exception as e:
        print(f"Error in speak function: {e}")

def speech_to_text(audio_file):
    """
    Convert audio file to text using Google Cloud Speech-to-Text API.  
    """
    client = speech.SpeechClient()
    with open(audio_file, 'rb') as audio_file:
        content = audio_file.read()
    
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=44100,
        language_code="es-ES",
    )
    
    response = client.recognize(config=config, audio=audio)
    
    return response.results[0].alternatives[0].transcript

def text_to_speech(text, output_file):
    """
    Convert text to speech using Google Cloud Text-to-Speech API.
    """
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code="es-ES",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    with open(output_file, "wb") as out:
        out.write(response.audio_content)
        print(f'Audio content written to file {output_file}')

def play_audio(file_path):
    """
    Play the audio file using PyAudio.
    """
    # Open the WAV file
    wf = wave.open(file_path, 'rb')
    
    # Initialize PyAudio
    p = pyaudio.PyAudio()
    
    # Open stream
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)
    
    # Read data in chunks and play
    data = wf.readframes(1024)
    while data:
        stream.write(data)
        data = wf.readframes(1024)
    
    # Clean up
    stream.stop_stream()
    stream.close()
    p.terminate()
    wf.close()

def show_speaking_window(model):
    """
    Creates and displays a speaking window interface for the specified model.
    """
    global speaking_window
    speaking_window = SpeakingWindow(model)
    speaking_window.window.mainloop()
    close_by_user_action()

def close_by_user_action():
    """
    Close the speaking window and kill the program if the user closes the window.
    """
    global speaking_window
    if speaking_window:
        if speaking_window.closed_by_user_action: 
            speaking_window = None
            os.kill(program_pid, signal.SIGINT)

