import datetime
import time

revoked_tokens = set()

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

def revoke_token(token: str):
    revoked_tokens.add(token)

def validate_token(token: str, expected_scope: str, expected_user_id: str) -> bool:
    try:
        user_id, expiry_str, scope = token.strip().split("|")
        expiry = int(expiry_str)

        # Revocation check
        if token in revoked_tokens:
            log("Token has been revoked", level="WARN", message_type="TOKEN")
            return False

        # Validate token components
        if user_id != expected_user_id:
            log(f"Token user mismatch: expected {expected_user_id}, got {user_id}", level="WARN", message_type="TOKEN")
            return False

        if scope != expected_scope:
            log(f"Token scope mismatch: expected '{expected_scope}', got '{scope}'", level="WARN", message_type="TOKEN")
            return False

        if expiry < int(time.time()):
            log("Token has expired", level="WARN", message_type="TOKEN")
            return False

        return True
    except Exception as e:
        log(f"Invalid token format: {e}", level="ERROR", message_type="TOKEN")
        return False
