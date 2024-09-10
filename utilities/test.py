#import keyboard
import sys
import time

output_string = ""

def dzik():
    sentence = []
    from pynput.keyboard import Key, Listener, KeyCode

    def show(key):

        global output_string
        if not isinstance(key, Key):
                output_string += key.char
                print(f'\r{output_string}', end='', flush=True)
        else:
            if key == Key.space:
                output_string += " "
                print(f'\r{output_string}', end='', flush=True)
            if key == Key.enter:
                print(f"\nOutput string: {output_string}")
                return False  # Stop listener
            elif key == Key.ctrl_l or key == Key.ctrl_r:
                output_string = "dzik"
                print(f"\nOutput string: {output_string}")
                return False  # Stop listener
            elif key == Key.backspace:
                if output_string:
                    output_string = output_string[:-1]
                    sys.stdout.write('\r' + output_string + ' ')
                    sys.stdout.write('\r' + output_string)
                    sys.stdout.flush()



    # Collect all event until released
    with Listener(on_press=show) as listener:
        listener.join()

    return ''.join(sentence)




if __name__ == "__main__":
    print(dzik())