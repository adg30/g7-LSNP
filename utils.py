import datetime

def log(message, level="INFO", sender_ip=None, message_type=None, verbose=True):
    import config
    if config.VERBOSE_MODE and verbose:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_parts = [f"[{timestamp}] [{level}]"]
        if sender_ip:
            log_parts.append(f"[IP: {sender_ip}]")
        if message_type:
            log_parts.append(f"[TYPE: {message_type}]")
        log_parts.append(message)
        print(" ".join(log_parts))

def set_verbose_mode(mode):
    import config
    config.VERBOSE_MODE = mode
