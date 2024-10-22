import itertools
import sys
import time

from utilities.print_formatters import print_formatted


def print_ascii_logo():
    with open("assets/ascii-art.txt", "r") as f:
        logo = f.read()
    with open("assets/Clean_Coder_writing.txt", "r") as f:
        writing = f.read()
    print_formatted(logo, color="yellow")
    print_formatted(writing, color="white")


def loading_animation(message="I'm thinking...", color="cyan"):
    frames = [
        "🌘🌑🌑🌑🌑🌑🌑🌑",
        "🌗🌘🌑🌑🌑🌑🌑🌑",
        "🌖🌗🌘🌑🌑🌑🌑🌑",
        "🌕🌖🌗🌘🌑🌑🌑🌑",
        "🌕🌕🌖🌗🌘🌑🌑🌑",
        "🌕🌕🌕🌖🌗🌘🌑🌑",
        "🌕🌕🌕🌕🌖🌗🌘🌑",
        "🌕🌕🌕🌕🌕🌖🌗🌘",
        "🌕🌕🌕🌕🌕🌕🌖🌗",
        "🌕🌕🌕🌕🌕🌕🌕🌖",
        "🌕🌕🌕🌕🌕🌕🌕🌕",
        "🌔🌕🌕🌕🌕🌕🌕🌕",
        "🌓🌔🌕🌕🌕🌕🌕🌕",
        "🌒🌓🌔🌕🌕🌕🌕🌕",
        "🌑🌒🌓🌔🌕🌕🌕🌕",
        "🌑🌑🌒🌓🌔🌕🌕🌕",
        "🌑🌑🌑🌒🌓🌔🌕🌕",
        "🌑🌑🌑🌑🌒🌓🌔🌕",
        "🌑🌑🌑🌑🌑🌒🌓🌔",
        "🌑🌑🌑🌑🌑🌑🌒🌓",
        "🌑🌑🌑🌑🌑🌑🌑🌒",
    ]
    print_formatted(message, color=color, end=' ')  # Print the message with color and stay on the same line
    sys.stdout.flush()
    print('\033[?25l', end='')  # Hide cursor
    try:
        for frame in itertools.cycle(frames):
            print_formatted(frame, color=color,
                            end='\r' + message + ' ')  # Print the frame on the same line after the message
            time.sleep(0.07)  # Adjust the sleep time for better animation speed
            if not loading_animation.is_running:
                break
    finally:
        print('\033[?25h', end='')  # Show cursor
        sys.stdout.write('\r' + ' ' * (len(message) + len(frames[0]) + 2) + '\r')  # Clear the entire line
        sys.stdout.flush()


loading_animation.is_running = True
