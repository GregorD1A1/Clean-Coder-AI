from termcolor import colored
import itertools
import sys
import time
from utilities.util_functions import print_formatted


def print_ascii_logo():
    with open("assets/ascii-art.txt", "r") as f:
        logo = f.read()
    with open("assets/Clean_Coder_writing.txt", "r") as f:
        writing = f.read()
    print(colored(logo, color="yellow"))
    print(colored(writing, color="white"))



def loading_animation(message="Waiting for response", color="cyan"):
    frames = [
        "[        ]",
        "[=       ]",
        "[==      ]",
        "[===     ]",
        "[====    ]",
        "[=====   ]",
        "[======  ]",
        "[======= ]",
        "[========]",
        "[ =======]",
        "[  ======]",
        "[   =====]",
        "[    ====]",
        "[     ===]",
        "[      ==]",
        "[       =]",
        "[        ]",
        "[       =]",
        "[      ==]",
        "[     ===]",
        "[    ====]",
        "[   =====]",
        "[  ======]",
        "[ =======]",
        "[========]",
        "[======= ]",
        "[======  ]",
        "[=====   ]",
        "[====    ]",
        "[===     ]",
        "[==      ]",
        "[=       ]",
    ]
    sys.stdout.write(message + " ")
    sys.stdout.flush()
    for frame in itertools.cycle(frames):
        print_formatted(frame, color=color, end='\r')
        time.sleep(0.1)
        sys.stdout.write('\b' * len(frame))
    print(writing)
