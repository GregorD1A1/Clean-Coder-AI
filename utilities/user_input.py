from pynput.keyboard import Key, Listener
from utilities.voice_utils import VoiceRecorder
from utilities.util_functions import print_formatted

recorder = VoiceRecorder()

# Old try, to remove
class InputHandler():
    def __init__(self):
        self.output_string = ""
        self.been_recorded = False

    def user_input(self, prompt=""):
        print_formatted("Just start writing or record voice message by pressing Tab:", color="yellow", bold=True)

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



def user_input(prompt=""):
    print_formatted(prompt + " Or use (m)icrophone to record it:", color="yellow", bold=True)
    user_sentence = input()
    if user_sentence == 'm':
        if recorder.microphone_available:
            user_sentence = record_voice_message()
        else:
            print_formatted(
                "Install 'sudo apt-get install libportaudio2' (Linux) or 'brew install portaudio' (Mac) to use microphone feature.", color="light_red"
            )
            user_sentence = input()

    return user_sentence


def record_voice_message():
    recorder.start_recording()

    def press_interrupt(key):
        if key == Key.enter:
            recorder.stop_recording()
            print("Recording finished.\n")
            return False  # Stop listener

    with Listener(on_press=press_interrupt, suppress=True) as listener:
        listener.join()

    return recorder.transcribe_audio()

if __name__ == "__main__":
    print(user_input("Provide your feedback."))
