import datetime
import time

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

def validate_token(token: str, expected_scope: str, expected_user_id: str) -> bool:
    try:
        user_id, expiry_str, scope = token.strip().split("|")
        expiry = int(expiry_str)

        # validate token components
        if user_id != expected_user_id:
            return False # wrong user
        if scope != expected_scope:
            return False # diff scope
        if expiry < int(time.time()):
            return False  # token expired

        return True
    except Exception as e:
        print(f"[ERROR] Invalid token format: {e}")
        return False