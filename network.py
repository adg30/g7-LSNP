import socket
import threading
import utils
import config

class Network:
    def __init__(self, port=50999):
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        try:
            self.sock.bind(('', self.port))
        except OSError as e:
            if e.errno == 10048:  # Port in use
                print(f"Port {self.port} in use. Close other instances first.")
                raise
            else:
                raise
        self.message_handlers = []
        self.running = False
        self.broadcast_address = self._get_broadcast_address()
        utils.log(f"Network initialized on port {self.port}", level="INFO")

    def _get_broadcast_address(self):
        """Determine the correct broadcast address for the local network"""
        try:
            # Get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            # Extract network prefix (assuming /24 subnet)
            network_prefix = '.'.join(local_ip.split('.')[:-1])
            broadcast_address = f"{network_prefix}.255"
            
            utils.log(f"Using broadcast address: {broadcast_address}", level="INFO")
            return broadcast_address
        except Exception as e:
            utils.log(f"Could not determine broadcast address, using default: {e}", level="WARN")
            return "192.168.1.255"  # fallback

    def start_listening(self):
        self.running = True
        self.listen_thread = threading.Thread(target=self._listen_loop)
        self.listen_thread.daemon = True
        self.listen_thread.start()
        utils.log("Started listening for incoming messages.", level="INFO")

    def _listen_loop(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(config.BUFFER_SIZE)
                message = data.decode('utf-8')
                sender_ip = addr[0]
                utils.log(f"Received: {message}", level="RECV", sender_ip=sender_ip)
                for handler in self.message_handlers:
                    handler(message, sender_ip)
            except socket.timeout:
                continue
            except Exception as e:
                utils.log(f"Error receiving message: {e}", level="ERROR")

    def stop_listening(self):
        self.running = False
        if self.listen_thread.is_alive():
            self.listen_thread.join(timeout=1)
        utils.log("Stopped listening for incoming messages.", level="INFO")

    def send_message(self, message, dest_ip='<broadcast>'):
        encoded_message = message.encode('utf-8')
        try:
            if dest_ip == '<broadcast>':
                self.sock.sendto(encoded_message, (self.broadcast_address, self.port))
                utils.log(f"Sent broadcast: {message}", level="SEND", message_type="BROADCAST")
            else:
                self.sock.sendto(encoded_message, (dest_ip, self.port))
                utils.log(f"Sent unicast to {dest_ip}: {message}", level="SEND", message_type="UNICAST")
        except Exception as e:
            utils.log(f"Error sending message: {e}", level="ERROR")

    def register_message_handler(self, handler):
        self.message_handlers.append(handler)
        utils.log("Message handler registered.", level="INFO")

    def unregister_message_handler(self, handler):
        if handler in self.message_handlers:
            self.message_handlers.remove(handler)
            utils.log("Message handler unregistered.", level="INFO")

# Example Usage (for testing purposes, can be removed later)
if __name__ == "__main__":
    net = Network()
    net.start_listening()

    def my_handler(msg, ip):
        print(f"Handler received: {msg} from {ip}")

    net.register_message_handler(my_handler)

    import time
    try:
        while True:
            net.send_message("TYPE: PING\nUSER_ID: user@192.168.1.13\n\n")
            net.send_message("TYPE: PROFILE\nUSER_ID: user@192.168.1.13\nDISPLAY_NAME: dave\nSTATUS: Testing LSNP\n\n")
            time.sleep(5)
    except KeyboardInterrupt:
        net.stop_listening()
