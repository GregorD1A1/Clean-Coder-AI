import itertools
import sys
import time
import random
from termcolor import colored
from time import sleep
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.columns import Columns
import os
current = os.path.dirname(os.path.realpath(__file__))
grandparent = os.path.dirname(os.path.dirname(current))
sys.path.append(grandparent)
from src.utilities.print_formatters import print_formatted

def print_ascii_logo():
    with open("assets/ascii-art.txt", "r") as f:
        logo = f.read()
    with open("assets/Clean_Coder_writing.txt", "r") as f:
        writing = f.read()
    print(colored(logo, color="yellow"))
    print(colored(writing, color="white"))


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

def task_completed_animation():
    console = Console()
    width = console.width  # Get console width

    # Adjusted ASCII celebration art to fit console width
    celebration_art = """
   🌟 🌟 🌟 🌟 🌟 🌟 🌟 🌟 🌟 🌟 🌟 🌟
   
       🎊 TASK COMPLETED! 🎊
       
   🌟 🌟 🌟 🌟 🌟 🌟 🌟 🌟 🌟 🌟 🌟 🌟
   """

    # Symbols for animation
    symbols = ["✨", "🎊", "🌟"]

    # Initial celebration panel
    console.clear()
    panel = Panel(
        Text(celebration_art, justify="center"),
        border_style="bright_yellow",
        padding=(1, 2)
    )
    console.print(panel)

    # Calculate how many symbols fit in the width (considering each symbol + more spaces takes about 6 characters)
    symbols_per_line = width // 6  # Increased space between symbols

    # Animated confetti - full width but spaced out
    with Live(console=console, refresh_per_second=15) as live:
        for frame in range(20):
            lines = []
            for _ in range(5):  # 5 lines of confetti
                line = "".join(
                    f"{random.choice(symbols)}    "  # Added more spaces between symbols
                    for _ in range(symbols_per_line)
                )
                lines.append(line)
            
            live.update(Text("\n".join(lines), justify="center"))
            sleep(0.05)  # Fast animation

    # Final message
    final_panel = Panel(
        Text("✨ Great job! Moving on to the next task... ✨",
             justify="center"),
        border_style="green"
    )
    console.print(final_panel)
