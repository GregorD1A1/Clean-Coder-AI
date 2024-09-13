import sys

from pynput.keyboard import Key, Listener
from voice_utils import VoiceRecorder
from util_functions import print_wrapped
import time

output_string = ""
been_recorded = False
recorder = VoiceRecorder()


def user_input(prompt=""):

    print_wrapped("Just start writing or record voice message by pressing Tab:", color="yellow", bold=True)

    def press_interrupt(key):
        global output_string
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
                output_string = recorder.transcribe_audio()
            return False  # Stop listener

        return True

    # Collect all event until released
    with Listener(on_press=press_interrupt) as listener:
        listener.join()

    sys.stdout.flush()
    return output_string


if __name__ == "__main__":
    print(user_input("Provide your feedback."))