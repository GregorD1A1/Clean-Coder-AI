from pynput.keyboard import Key, Listener
from utilities.voice_utils import VoiceRecorder
from utilities.util_functions import print_wrapped
import os, sys


output_string = ""
recorder = VoiceRecorder()


def user_input(prompt=""):
    print_wrapped(prompt + " You can record voice by pressing Ctrl.", color="yellow", bold=True)
    global output_string
    output_string = ""

    def press_interrupt(key):
        global output_string

        if hasattr(key, 'char'):
            if not recorder.is_recording:
                output_string += key.char
            else:
                # cancel recording
                if key.char == 'c':
                    recorder.stop_recording()
                    print("Recording canceled")

        elif key == Key.space:
            output_string += " "

        elif key == Key.ctrl_l or key == Key.ctrl_r:
            recorder.start_recording()

        elif key == Key.backspace:
            if output_string:
                output_string = output_string[:-1]
                # needed to remove letter from screen
                #sys.stdout.write('\r' + output_string + ' ')

        elif key == Key.enter:
            # go to newline when enter clicked
            #sys.stdout.write("")
            if recorder.is_recording:
                recorder.stop_recording()
                print("Recording finished")
                output_string = recorder.transcribe_audio()
            return False  # Stop listener

        print(f'\r{output_string}', end='', flush=True)
        #sys.stdout.write('\r' + output_string)
        #sys.stdout.flush()


    # Collect all event until released
    with Listener(on_press=press_interrupt) as listener:
        listener.join()

    return output_string


def user_input_simple(prompt=""):
    recorder = VoiceRecorder()
    print_wrapped(prompt + " You can record voice by writing 'v'.", color="yellow", bold=True)
    while True:
        user_response = input()
        if user_response == "v":

            recorder.record()
            if recorder.transcribe:
                recorder.transcribe = False
                return recorder.transcribe_audio()
            else:
                continue

    return user_response


if __name__ == "__main__":
    user_input("Provide your feedback.")
    #os.remove(recorder.soundfile_path)
    user_input("Provide your feedback.")
