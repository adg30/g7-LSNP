import datetime
import time
import base64
import random

revoked_tokens = set()

# Configuration for reliability testing
SIMULATE_PACKET_LOSS = False
PACKET_LOSS_RATE = 0.1  # 10% packet loss for testing

def should_drop_packet():
    """Simulate packet loss for testing reliability"""
    if SIMULATE_PACKET_LOSS:
        return random.random() < PACKET_LOSS_RATE
    return False

def enable_packet_loss_simulation(rate=0.1):
    """Enable packet loss simulation for testing"""
    global SIMULATE_PACKET_LOSS, PACKET_LOSS_RATE
    SIMULATE_PACKET_LOSS = True
    PACKET_LOSS_RATE = rate
    log(f"Packet loss simulation enabled with {rate*100}% loss rate", level="INFO")

def disable_packet_loss_simulation():
    """Disable packet loss simulation"""
    global SIMULATE_PACKET_LOSS
    SIMULATE_PACKET_LOSS = False
    log("Packet loss simulation disabled", level="INFO")

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

def log_protocol_event(event_type, details, sender_ip=None, message_type=None):
    """Enhanced logging for protocol-specific events"""
    import config
    if config.VERBOSE_MODE:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_parts = [f"[{timestamp}] [PROTOCOL]"]
        if sender_ip:
            log_parts.append(f"[IP: {sender_ip}]")
        if message_type:
            log_parts.append(f"[TYPE: {message_type}]")
        log_parts.append(f"[{event_type}] {details}")
        print(" ".join(log_parts))

def log_token_check(token, scope, user_id, valid, sender_ip=None):
    """Log token validation attempts"""
    import config
    if config.VERBOSE_MODE:
        status = "VALID" if valid else "INVALID"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_parts = [f"[{timestamp}] [TOKEN]"]
        if sender_ip:
            log_parts.append(f"[IP: {sender_ip}]")
        log_parts.append(f"[{status}] scope={scope} user={user_id}")
        print(" ".join(log_parts))

def log_retry_attempt(message_type, target, attempt_num, sender_ip=None):
    """Log retry attempts for unreliable operations"""
    import config
    if config.VERBOSE_MODE:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_parts = [f"[{timestamp}] [RETRY]"]
        if sender_ip:
            log_parts.append(f"[IP: {sender_ip}]")
        log_parts.append(f"[{message_type}] target={target} attempt={attempt_num}")
        print(" ".join(log_parts))

def log_message_drop(reason, message_type, sender_ip=None):
    """Log when messages are dropped"""
    import config
    if config.VERBOSE_MODE:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_parts = [f"[{timestamp}] [DROP]"]
        if sender_ip:
            log_parts.append(f"[IP: {sender_ip}]")
        log_parts.append(f"[{message_type}] reason={reason}")
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

def base64_encode(data: bytes) -> str:
    return base64.b64encode(data).decode('utf-8')

def base64_decode(data_str: str) -> bytes:
    return base64.b64decode(data_str.encode('utf-8'))

def chunk_file_data(data: bytes, chunk_size: int = 1024):
    """Yield file data in chunks of chunk_size bytes."""
    for i in range(0, len(data), chunk_size):
        yield data[i:i+chunk_size]
