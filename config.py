import socket
import os

# Network Configuration
PORT = 50999
BUFFER_SIZE = 65535
ENCODING = 'utf-8'
VERBOSE_MODE = True

# Auto-detect broadcast address
def get_broadcast_address():
    try:
        # Get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        
        # Extract network prefix (assuming /24 subnet)
        network_prefix = '.'.join(local_ip.split('.')[:-1])
        broadcast_address = f"{network_prefix}.255"
        
        print(f"Auto-detected broadcast address: {broadcast_address}")
        return broadcast_address
    except Exception as e:
        print(f"Could not auto-detect broadcast address: {e}")
        print("Using fallback: 192.168.1.255")
        return "192.168.1.255"

BROADCAST = get_broadcast_address()

# Testing Configuration
TESTING_MODE = os.getenv('LSNP_TESTING', 'false').lower() == 'true'
LOCAL_TESTING = os.getenv('LSNP_LOCAL', 'false').lower() == 'true'

if LOCAL_TESTING:
    print("LOCAL TESTING MODE: Using localhost for testing")
    BROADCAST = '127.0.0.1'