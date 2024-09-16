from termcolor import colored


def print_ascii_logo():
    with open("assets/ascii-art.txt", "r") as f:
        logo = f.read()
    with open("assets/Clean_Coder_writing.txt", "r") as f:
        writing = f.read()
    print(colored(logo, color="yellow"))
    print(writing)
