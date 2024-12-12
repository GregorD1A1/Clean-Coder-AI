import os
from src.utilities.print_formatters import print_formatted
from src.utilities.voice_utils import VoiceRecorder
import keyboard


recorder = VoiceRecorder()


def user_input(prompt=""):
    print_formatted(prompt + " Or use (m)icrophone to tell:", color="yellow", bold=True)
    user_sentence = input()
    if user_sentence == 'm':
        if not os.getenv("OPENAI_API_KEY"):
            print_formatted("Set OPENAI_API_KEY to use microphone feature.", color="red")
            user_sentence = input()
        elif recorder.libportaudio_available:
            user_sentence = record_voice_message()
        else:
            print_formatted("Install 'sudo apt-get install libportaudio2' (Linux) or 'brew install portaudio' (Mac) to use microphone feature.", color="red")
            user_sentence = input()

    return user_sentence


def record_voice_message():
    recorder.start_recording()
    keyboard.wait('enter', suppress=True)
    recorder.stop_recording()
    print("Recording finished.\n")
    return recorder.transcribe_audio()
