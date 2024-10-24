from utilities.print_formatters import print_formatted
from utilities.voice_utils import VoiceRecorder
import keyboard


recorder = VoiceRecorder()


def user_input(prompt=""):
    print_formatted(prompt + " Or use (m)icrophone to record it:", color="yellow", bold=True)
    user_sentence = input()
    if user_sentence == 'm':
        if recorder.microphone_available:
            user_sentence = record_voice_message()
        else:
            print_formatted("Install 'sudo apt-get install libportaudio2' (Linux) or 'brew install portaudio' (Mac) to use microphone feature.", color="red")
            user_sentence = input()

    return user_sentence


def record_voice_message():
    recorder.start_recording()
    keyboard.wait('enter')
    recorder.stop_recording()
    print("Recording finished.\n")
    return recorder.transcribe_audio()
