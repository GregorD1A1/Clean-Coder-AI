from pynput.keyboard import Key, Listener
from voice_utils import VoiceRecorder
from util_functions import print_wrapped
import sys

recorder = VoiceRecorder()


class UserInput:
    def __init__(self):
        self.been_recorded = False
        self.output_string = ""

    def user_input(self, prompt=""):
        print_wrapped("Just start writing or record voice message by pressing Tab:", color="yellow", bold=True)



        # Collect all events until released
        with Listener(on_press=self.press_interrupt) as listener:
            listener.join()

        if not self.been_recorded:
            self.output_string = input(prompt)

        return self.output_string

    def press_interrupt(self, key):
        if hasattr(key, 'char'):
            if not recorder.is_recording:
                return False
            else:
                # cancel recording
                if key.char == 'c':
                    recorder.stop_recording()
                    print("Recording canceled")
                    self.been_recorded = False

        elif key == Key.tab:
            recorder.start_recording()
            self.been_recorded = True

        elif key == Key.enter:
            if recorder.is_recording:
                recorder.stop_recording()
                print("Recording finished")
                output_string = recorder.transcribe_audio()
                self.been_recorded = True
            return False  # Stop listener


def user_input(prompt=""):
    """
    Wrapper function for UserInput.user_input

    This function creates a UserInput instance and calls its user_input method.
    It's useful for one-off calls without needing to explicitly create a UserInput object.
    """
    ui = UserInput()
    return ui.user_input(prompt)


if __name__ == "__main__":
    print(user_input())