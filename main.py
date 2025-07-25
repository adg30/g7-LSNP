import time
import socket
import threading
from peers import PeerManager
from network import Network
import parser
import utils
import secrets

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
        
    def start_periodic_task(self, message_func, interval_seconds):
        def task_loop():
            while True:
                self.network.send_message(message_func())
                time.sleep(interval_seconds)

        self.network.send_message(message_func())

        threading.Thread(target=task_loop, daemon=True).start()

    def start_periodic_ping(self):
        """Send a PING message every 300 seconds."""
        self.start_periodic_task(
            lambda: f"TYPE: PING\nUSER_ID: {self.user_id}\n\n",
            300
        )

    def start_periodic_profile(self):
        """Send a PROFILE message every 300 seconds."""
        self.start_periodic_task(
            lambda: parser.format_message({
                'TYPE': 'PROFILE',
                'USER_ID': self.user_id,
                'DISPLAY_NAME': self.display_name,
                'STATUS': 'Available'
            }),
            300
        )

    def handle_message(self, message_text, sender_ip):
        """Process incoming LSNP messages"""
        # Parse the message
        parsed = parser.parse_message(message_text)
        
        if not parsed:
            utils.log("Failed to parse message", level="ERROR")
            return
            
        msg_type = parsed.get('TYPE')
        #user_id = parsed.get('USER_ID')
        
        if not msg_type:
            utils.log("Message missing TYPE or USER_ID", level="WARNING")
            return
        
        # Handle different message types
        if msg_type == 'PROFILE':
            self.handle_profile_message(parsed, sender_ip)
        elif msg_type == 'POST':
            self.handle_post_message(parsed, sender_ip)
        elif msg_type == 'DM':
            self.handle_dm_message(parsed, sender_ip)
        elif msg_type == 'FOLLOW':
            self.handle_follow(parsed, sender_ip)
        elif msg_type == 'UNFOLLOW':
            self.handle_unfollow(parsed, sender_ip)
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

    def handle_follow(self, parsed, sender_ip):
        follower_id = parsed.get('FROM')
        followed_id = parsed.get('TO')
        token = parsed.get('TOKEN', '')

        if not follower_id or not followed_id:
            utils.log("FOLLOW message missing FROM or TO field", level="WARN")
            return

        # Prevent self-follow
        if follower_id == followed_id:
            utils.log("User attempted to follow themselves", level="WARN")
            return

        if followed_id != self.user_id:
            return  # Not for this user so do not

        if not utils.validate_token(token, expected_scope='follow', expected_user_id=follower_id):
            utils.log(f"Rejected FOLLOW from {follower_id}: invalid or expired token", level="WARN")
            return

        self.peer_manager.add_follower(followed_id, follower_id)

        follower_info = self.peer_manager.peers.get(follower_id, {})
        follower_name = follower_info.get('display_name', follower_id)

        print(f"\nUser {follower_name} has followed you.")


    def handle_unfollow(self, parsed, sender_ip):
        unfollower_id = parsed.get('FROM')
        unfollowed_id = parsed.get('TO')
        token = parsed.get('TOKEN', '')

        if not unfollower_id or not unfollowed_id:
            utils.log("UNFOLLOW message missing FROM or TO field", level="WARN")
            return

        # Prevent self-unfollow
        if unfollower_id == unfollowed_id:
            utils.log("User attempted to unfollow themselves", level="WARN")
            return

        if unfollowed_id != self.user_id:
            return  # Not for this user so do not

        if not utils.validate_token(token, expected_scope='follow', expected_user_id=unfollower_id):
            utils.log(f"Rejected UNFOLLOW from {unfollower_id}: invalid or expired token", level="WARN")
            return

        self.peer_manager.remove_follower(unfollowed_id, unfollower_id)

        unfollower_info = self.peer_manager.peers.get(unfollower_id, {})
        unfollower_name = unfollower_info.get('display_name', unfollower_id)

        print(f"\nUser {unfollower_name} has unfollowed you.")



    def _send_follow_action(self, target_user_id: str, action: str):
        """
        Build and send a FOLLOW or UNFOLLOW message to the target user.
        `action` must be either 'FOLLOW' or 'UNFOLLOW'.
        """
        if action not in ("FOLLOW", "UNFOLLOW"):
            raise ValueError("action must be FOLLOW or UNFOLLOW")

        ttl_seconds   = 3600
        now           = int(time.time())
        token         = f"{self.user_id}|{now + ttl_seconds}|follow"
        message_id    = secrets.token_hex(8)

        msg = parser.format_message({
            'TYPE'      : action,
            'MESSAGE_ID': message_id,
            'FROM'      : self.user_id,
            'TO'        : target_user_id,
            'TIMESTAMP' : now,
            'TOKEN'     : token,
        })

        peer_info = self.peer_manager.peers.get(target_user_id)
        if peer_info and peer_info.get('ip_address'):
            dest_ip = peer_info['ip_address']
            self.network.send_message(msg, dest_ip=dest_ip)
            utils.log(f"Sent {action} to {target_user_id} via {dest_ip}", level="INFO")
        else:
            utils.log(f"Cannot send {action} — no known IP for {target_user_id}", level="WARN")

    
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

                elif command == "follow":
                    if len(cmd) > 1:
                        self._send_follow_action(cmd[1], "FOLLOW")
                    else:
                        print("Usage: follow <user_id>")

                elif command == "unfollow":
                    if len(cmd) > 1:
                        self._send_follow_action(cmd[1], "UNFOLLOW")
                    else:
                        print("Usage: unfollow <user_id>")

                elif command == "followers":
                    self.peer_manager.display_followers(self.user_id)


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
    client.start_periodic_ping()
    client.start_periodic_profile()
    client.run_cli()