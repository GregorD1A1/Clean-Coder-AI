import sys

from pynput.keyboard import Key, Listener
from utilities.voice_utils import VoiceRecorder
from utilities.util_functions import print_wrapped
import time

recorder = VoiceRecorder()

class InputHandler():
    def __init__(self):
        self.output_string = ""
        self.been_recorded = False

    def user_input(self, prompt=""):
        print_wrapped("Just start writing or record voice message by pressing Tab:", color="yellow", bold=True)

        def press_interrupt(key):
            if hasattr(key, 'char'):
                if not recorder.is_recording:
                    return False
                else:
                    if key.char == 'c':
                        recorder.stop_recording()
                        print("Recording canceled")

            elif key == Key.tab:
                recorder.start_recording()
                self.been_recorded = True

            elif key == Key.enter:
                if recorder.is_recording:
                    recorder.stop_recording()
                    print("Recording finished")
                    self.output_string = recorder.transcribe_audio()
                return False  # Stop listener

        # Collect all event until released
        with Listener(on_press=press_interrupt) as listener:
            listener.join()

        if not self.been_recorded:
            self.output_string = input()

        return self.output_string



def user_input_old(prompt=""):
    input_class = InputHandler()
    return input_class.user_input(prompt)


def user_input(prompt=""):
    print_wrapped(prompt + " Or use (m)icrophone to record it:", color="yellow", bold=True)
    user_sentence = input()
    if user_sentence == 'm':
        recorder.start_recording()
        def press_interrupt(key):
            if key == Key.enter:
                recorder.stop_recording()
                print("Recording finished.\n")
                return False  # Stop listener
        with Listener(on_press=press_interrupt, suppress=True) as listener:
            listener.join()

        user_sentence = recorder.transcribe_audio()

    return user_sentence

if __name__ == "__main__":
    print(user_input("Provide your feedback."))
