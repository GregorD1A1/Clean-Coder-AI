import textwrap


def print_wrapped(content, width=160):
    lines = content.split('\n')
    wrapped_lines = [textwrap.fill(line, width=width) for line in lines]
    wrapped_content = '\n'.join(wrapped_lines)
    print(wrapped_content)

