import socket
import time
from config import PORT, BROADCAST

def test_network():
    print(f"Testing network connectivity...")
    print(f"Port: {PORT}")
    print(f"Broadcast: {BROADCAST}")
    
    # Test socket creation
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        print("✓ Socket created successfully")
    except Exception as e:
        print(f"✗ Socket creation failed: {e}")
        return False
    
    # Test binding
    try:
        sock.bind(('', PORT))
        print(f"✓ Bound to port {PORT}")
    except Exception as e:
        print(f"✗ Binding failed: {e}")
        return False
    
    # Test broadcast send
    try:
        test_msg = "LSNP_TEST:Hello World"
        sock.sendto(test_msg.encode(), (BROADCAST, PORT))
        print(f"✓ Sent test broadcast to {BROADCAST}")
    except Exception as e:
        print(f"✗ Broadcast failed: {e}")
        return False
    
    # Test receiving (with timeout)
    sock.settimeout(2)
    try:
        print("Waiting for incoming messages (2 seconds)...")
        data, addr = sock.recvfrom(1024)
        print(f"✓ Received: {data.decode()} from {addr}")
    except socket.timeout:
        print("ℹ No incoming messages (this is normal if no other clients)")
    except Exception as e:
        print(f"✗ Receive test failed: {e}")
    
    sock.close()
    return True

if __name__ == "__main__":
    test_network() 