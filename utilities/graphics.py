from termcolor import colored

def print_ascii_logo():
    with open("assets/ascii-art.txt", "r") as f:
        logo = f.read()
    print(colored(logo, color="yellow"))