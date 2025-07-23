import time
import socket
from peers import PeerManager
from network import Network
import parser
import utils

class LSNPClient:
    def __init__(self):
        # Initialize components
        self.peer_manager = PeerManager()
        self.network = Network()
        
        # Get user info
        self.user_id = f"user@{self.get_lan_ip()}"
        self.display_name = input("Enter your display name: ").strip() or "LSNP User"
        
        # Connect message handler
        self.network.register_message_handler(self.handle_message)
        
        # Start network
        self.network.start_listening()
        utils.log(f"LSNP Client started for {self.user_id}", level="INFO")

    def get_lan_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def handle_message(self, message_text, sender_ip):
        """Process incoming LSNP messages"""
        # Parse the message
        parsed = parser.parse_message(message_text)
        
        if not parsed:
            utils.log("Failed to parse message", level="ERROR")
            return
            
        msg_type = parsed.get('TYPE')
        user_id = parsed.get('USER_ID')
        
        if not msg_type or not user_id:
            utils.log("Message missing TYPE or USER_ID", level="WARNING")
            return
        
        # Handle different message types
        if msg_type == 'PROFILE':
            self.handle_profile_message(parsed, sender_ip)
        elif msg_type == 'POST':
            self.handle_post_message(parsed, sender_ip)
        elif msg_type == 'DM':
            self.handle_dm_message(parsed, sender_ip)
        # Add more message types later
    
    def handle_profile_message(self, parsed, sender_ip):
        """Handle PROFILE messages"""
        self.peer_manager.add_peer(
            user_id=parsed['USER_ID'],
            display_name=parsed.get('DISPLAY_NAME'),
            status=parsed.get('STATUS'),
            ip_address=sender_ip
        )
    
    def handle_post_message(self, parsed, sender_ip):
        """Handle POST messages"""
        # First add/update the peer
        self.peer_manager.add_peer(
            user_id=parsed['USER_ID'],
            ip_address=sender_ip
        )
        
        # Then add the post
        self.peer_manager.add_post(
            user_id=parsed['USER_ID'],
            content=parsed.get('CONTENT', ''),
            timestamp=int(parsed.get('TIMESTAMP', time.time()))
        )
    
    def handle_dm_message(self, parsed, sender_ip):
        """Handle DM messages"""
        # Only process if it's for us
        if parsed.get('TO') == self.user_id:
            self.peer_manager.add_direct_message(
                from_user=parsed['FROM'],
                to_user=parsed['TO'],
                content=parsed.get('CONTENT', ''),
                timestamp=int(parsed.get('TIMESTAMP', time.time()))
            )
    
    def run_cli(self):
        """Main CLI loop"""
        print(f"\n=== LSNP Client for {self.user_id} ===")
        print("Commands: peers, posts [user_id], messages [user_id], verbose, exit")
        
        while True:
            try:
                cmd = input("\nLSNP> ").strip().split()
                
                if not cmd:
                    continue
                    
                command = cmd[0].lower()
                
                if command == "exit":
                    break
                elif command == "peers":
                    self.peer_manager.display_all_peers()
                elif command == "posts":
                    if len(cmd) > 1:
                        self.peer_manager.display_posts_by_user(cmd[1])
                    else:
                        print("Usage: posts <user_id>")
                elif command == "messages":
                    if len(cmd) > 1:
                        self.peer_manager.display_dms_for_user(cmd[1])
                    else:
                        print("Usage: messages <user_id>")
                elif command == "verbose":
                    import config
                    config.VERBOSE_MODE = not config.VERBOSE_MODE
                    print(f"Verbose mode: {'ON' if config.VERBOSE_MODE else 'OFF'}")
                else:
                    print("Unknown command. Try: peers, posts <user_id>, messages <user_id>, verbose, exit")
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
        
        # Cleanup
        self.network.stop_listening()
        print("Goodbye!")

# Main entry point
if __name__ == "__main__":
    client = LSNPClient()
    client.run_cli()