def parse_message(text):
    parts = text.strip().split("\n")
    return {line.split(": ", 1)[0]: line.split(": ", 1)[1] for line in parts if ": " in line}
