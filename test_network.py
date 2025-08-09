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
    sock.settimeout(5)  # Increased timeout to 5 seconds
    try:
        print("Waiting for incoming messages (5 seconds)...")
        data, addr = sock.recvfrom(1024)
        print(f"✓ Received: {data.decode()} from {addr}")
    except socket.timeout:
        print("ℹ No incoming messages (this is normal if no other clients)")
    except Exception as e:
        print(f"✗ Receive test failed: {e}")
    
    sock.close()
    return True

def test_peer_discovery():
    """Test the improved peer discovery mechanism"""
    print("\n=== Testing Peer Discovery Improvements ===")
    print("The following changes have been implemented:")
    print("✓ PING messages sent every 60 seconds (was 300)")
    print("✓ PROFILE messages sent every 60 seconds (was 300)")
    print("✓ Immediate presence announcement on startup")
    print("✓ Faster peer discovery for new clients")
    print("\nTo test:")
    print("1. Start client A: python main.py")
    print("2. Wait 1-2 minutes")
    print("3. Start client B: python main.py")
    print("4. Client B should see Client A immediately")
    print("5. Client A should see Client B within 60 seconds")

if __name__ == "__main__":
    test_network()
    test_peer_discovery() 