import keyboard
from pynput.keyboard import Key, Listener
from voice_utils import VoiceRecorder
from util_functions import print_wrapped
import time

recorder = VoiceRecorder()

class InputHandler():
    def __init__(self):
        self.output_string = ""
        self.been_recorded = False

    def user_input(self, prompt=""):
        print_wrapped("Just start writing or record voice message by pressing Tab:", color="yellow", bold=True)

        while True:
            if keyboard.is_pressed('ctrl'):
                recorder.start_recording()
                self.been_recorded = True

            elif keyboard.is_pressed('enter'):
                if recorder.is_recording:
                    recorder.stop_recording()
                    print("Recording finished")
                    self.output_string = recorder.transcribe_audio()
                break


        input("Be a dzik please")

        return self.output_string


def user_input(prompt=""):
    input_class = InputHandler()
    return input_class.user_input(prompt)

if __name__ == "__main__":
    print(user_input("Provide your feedback."))
