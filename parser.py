import utils

def parse_message(text):
    message_data = {}
    try:
        # Split by the LSNP terminator (double newline)
        parts = text.strip().split('\n\n', 1)
        if not parts:
            utils.log("Received empty message.", level="WARNING")
            return {}

        # Split lines and parse key-value pairs
        lines = parts[0].split('\n')
        for line in lines:
            if ": " in line:
                key, value = line.split(": ", 1)
                message_data[key.strip()] = value.strip()
            elif line.strip(): # Handle lines that might not be key-value but are not empty
                utils.log(f"Malformed line in message: {line}", level="WARNING")

        # For FILE_CHUNK, treat content after \n\n as RAW_CONTENT (Base64 chunk)
        if len(parts) > 1 and parts[1].strip():
            message_data['RAW_CONTENT'] = parts[1].strip()

    except Exception as e:
        utils.log(f"Error parsing message: {e} - Original text: {text}", level="ERROR")
        return {}
    return message_data

def format_message(message_data):
    lines = []
    raw_content = message_data.pop('RAW_CONTENT', None)
    # AVATAR fields: allow AVATAR_URL, AVATAR_HASH, AVATAR_TYPE, etc.
    avatar_keys = [k for k in list(message_data.keys()) if k.startswith('AVATAR_')]
    for key in avatar_keys:
        value = message_data[key]
        lines.append(f"{key}: {value}")
        message_data.pop(key)
    # Standard fields
    for key, value in message_data.items():
        lines.append(f"{key}: {value}")
    # Add the LSNP terminator
    formatted_message = '\n'.join(lines) + '\n\n'
    if raw_content:
        formatted_message += raw_content
    return formatted_message