from pynput.keyboard import Key, Listener
from voice_utils import VoiceRecorder
from util_functions import print_wrapped
import sys

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
                    # cancel recording
                    if key.char == 'c':
                        recorder.stop_recording()
                        print("Recording canceled")

            elif key == Key.tab:
                recorder.start_recording()

            elif key == Key.enter:
                if recorder.is_recording:
                    recorder.stop_recording()
                    print("Recording finished")
                    self.output_string = recorder.transcribe_audio()
                return False  # Stop listener

        # Collect all event until released
        with Listener(on_press=press_interrupt) as listener:
            listener.join()

        self.output_string = input()

        return self.output_string


def user_input():
    input_class = InputHandler()
    return input_class.user_input()


if __name__ == "__main__":
    print(user_input())