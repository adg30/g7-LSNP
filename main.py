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
            self.handle_post(parsed, sender_ip)
        elif msg_type == 'DM':
            self.handle_dm(parsed, sender_ip)
        elif msg_type == 'FOLLOW':
            self.handle_follow(parsed, sender_ip)
        elif msg_type == 'UNFOLLOW':
            self.handle_unfollow(parsed, sender_ip)
        elif msg_type == "ACK":
            self.handle_ack(parsed, sender_ip)
        elif msg_type == "LIKE":
            self.handle_like(parsed, sender_ip)
        # Add more message types later
    
    def handle_profile_message(self, parsed, sender_ip):
        """Handle PROFILE messages"""
        self.peer_manager.add_peer(
            user_id=parsed['USER_ID'],
            display_name=parsed.get('DISPLAY_NAME'),
            status=parsed.get('STATUS'),
            ip_address=sender_ip
        )


#------- FOLLOW


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

    def send_follow_action(self, target_user_id: str, action: str):
        #Send a FOLLOW or UNFOLLOW message to the target user.
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


#------- POST

    def send_post(self, content: str, ttl: int = 60):
        now = int(time.time())
        token = f"{self.user_id}|{now + ttl}|broadcast"
        message_id = secrets.token_hex(8)

        msg = parser.format_message({
            'TYPE': 'POST',
            'USER_ID': self.user_id,
            'CONTENT': content,
            'TTL': ttl,
            'MESSAGE_ID': message_id,
            'TOKEN': token
        })

        for follower_id in self.peer_manager.get_followers(self.user_id):
            peer_info = self.peer_manager.peers.get(follower_id)
            if peer_info and peer_info.get('ip_address'):
                self.network.send_message(msg, dest_ip=peer_info['ip_address'])
        

    def handle_post(self, parsed, sender_ip):
        from_user = parsed.get('USER_ID')
        content = parsed.get('CONTENT')
        token = parsed.get('TOKEN')

        if not utils.validate_token(token, expected_scope='broadcast', expected_user_id=from_user):
            utils.log("Invalid POST token", level="WARN", sender_ip=sender_ip, message_type="POST")
            return

        display_name = self.peer_manager.get_display_name(from_user)
        print(f"\n POST from {display_name}: {content}")


#------- DM

    def send_dm(self, target_user_id: str, content: str):
        # Send a private DM to the target user with chat-scoped token.
        ttl_seconds = 3600
        now         = int(time.time())
        token       = f"{self.user_id}|{now + ttl_seconds}|chat"
        message_id  = secrets.token_hex(8)

        msg = parser.format_message({
            'TYPE'      : 'DM',
            'MESSAGE_ID': message_id,
            'FROM'      : self.user_id,
            'TO'        : target_user_id,
            'TIMESTAMP' : now,
            'CONTENT'   : content,
            'TOKEN'     : token,
        })

        peer_info = self.peer_manager.peers.get(target_user_id)
        if peer_info and peer_info.get('ip_address'):
            dest_ip = peer_info['ip_address']
            self.network.send_message(msg, dest_ip=dest_ip)
            utils.log(f"Sent DM to {target_user_id} via {dest_ip}", level="INFO")
        else:
            utils.log(f"Cannot send DM — no known IP for {target_user_id}", level="WARN")

    def handle_dm(self, parsed: dict, sender_ip: str):
        from_user   = parsed.get('FROM')
        to_user     = parsed.get('TO')
        content     = parsed.get('CONTENT')
        message_id  = parsed.get('MESSAGE_ID')
        token       = parsed.get('TOKEN')

        # Validate that the DM is addressed to this user
        if to_user != self.user_id:
            return

        if not utils.validate_token(token, expected_scope='chat', expected_user_id=from_user):
            utils.log("Invalid DM token", level="WARN", sender_ip=sender_ip, message_type="DM")
            return

        display_name = self.peer_manager.get_display_name(from_user)
        print(f"\n[DM] {display_name}: {content}")

        self.send_ack(message_id, sender_ip) #acknowledge

#------- ACK


    def send_ack(self, message_id: str, dest_ip: str):
        msg = parser.format_message({
            'TYPE': 'ACK',
            'MESSAGE_ID': message_id,
            'STATUS': 'RECEIVED'
        })

        self.network.send_message(msg, dest_ip=dest_ip)
        utils.log(f"Sent ACK for {message_id} to {dest_ip}", level="INFO")

    def handle_ack(self, parsed, sender_ip):
        message_id = parsed.get('MESSAGE_ID')
        status = parsed.get('STATUS')

        if not message_id or not status:
            utils.log("Malformed ACK received", level="WARN", sender_ip=sender_ip, message_type="ACK")
            return

        utils.log(f"Received ACK for {message_id} from {sender_ip} with status {status}", level="INFO")



    #------- Like

    def send_like(self, target_user_id: str, post_timestamp: int, action: str = "LIKE"):
        # Sends a LIKE or UNLIKE message to the author of a post
        if action not in ("LIKE", "UNLIKE"):
            raise ValueError("action must be LIKE or UNLIKE")

        ttl_seconds = 3600
        now = int(time.time())
        token = f"{self.user_id}|{now + ttl_seconds}|broadcast"

        msg = parser.format_message({
            'TYPE'           : 'LIKE',
            'FROM'           : self.user_id,
            'TO'             : target_user_id,
            'POST_TIMESTAMP' : post_timestamp,
            'ACTION'         : action,
            'TIMESTAMP'      : now,
            'TOKEN'          : token,
        })

        peer_info = self.peer_manager.peers.get(target_user_id)
        if peer_info and peer_info.get('ip_address'):
            dest_ip = peer_info['ip_address']
            self.network.send_message(msg, dest_ip=dest_ip)
            utils.log(f"Sent {action} for post {post_timestamp} to {target_user_id} via {dest_ip}", level="INFO")
        else:
            utils.log(f"Cannot send {action} — no known IP for {target_user_id}", level="WARN")

    def handle_like(self, parsed, sender_ip):
        from_user = parsed.get('FROM')
        to_user = parsed.get('TO')
        post_timestamp = parsed.get('POST_TIMESTAMP')
        action = parsed.get('ACTION')
        token = parsed.get('TOKEN')

        if to_user != self.user_id:
            return  # Not our post

        if not utils.validate_token(token, expected_scope='broadcast', expected_user_id=from_user):
            utils.log("Invalid LIKE token", level="WARN", sender_ip=sender_ip, message_type="LIKE")
            return

        # Display format: alice likes your post [post y message]
        display_name = self.peer_manager.get_display_name(from_user)
        verb = "likes" if action == "LIKE" else "unlikes"
        print(f"\n{display_name} {verb} your post [post @ {post_timestamp}]")

#--------------------------

    def run_cli(self):
        """Main CLI loop"""
        print(f"\n=== LSNP Client for {self.user_id} ===")
        print("Unknown command. Try: peers, follow <user_id>, unfollow <user_id>, post message <user_id> <content>, verbose, exit")
        
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
                elif command == "follow":
                    if len(cmd) > 1:
                        self.send_follow_action(cmd[1], "FOLLOW")
                    else:
                        print("Usage: follow <user_id>")

                elif command == "unfollow":
                    if len(cmd) > 1:
                        self.send_follow_action(cmd[1], "UNFOLLOW")
                    else:
                        print("Usage: unfollow <user_id>")

                elif command == "followers":
                    self.peer_manager.display_followers(self.user_id)

                elif command == "post":
                    content = input("Enter post content: ").strip()
                    if content:
                        self.send_post(content)
                    else:
                        print("Post content cannot be empty.")

                elif command == "message":
                    if len(cmd) > 2:
                        to_user = cmd[1]
                        content = " ".join(cmd[2:])
                        self.send_dm(to_user, content)
                    else:
                        print("Usage: message <user_id> <content>")

                elif command == "like":
                    if len(cmd) > 2:
                        to_user = cmd[1]
                        post_timestamp = cmd[2]
                        self.send_like(to_user, post_timestamp, action="LIKE")
                    else:
                        print("Usage: like <user_id> <post_timestamp>")

                elif command == "unlike":
                    if len(cmd) > 2:
                        to_user = cmd[1]
                        post_timestamp = cmd[2]
                        self.send_like(to_user, post_timestamp, action="UNLIKE")
                    else:
                        print("Usage: unlike <user_id> <post_timestamp>")

                elif command == "verbose":
                    import config
                    config.VERBOSE_MODE = not config.VERBOSE_MODE
                    print(f"Verbose mode: {'ON' if config.VERBOSE_MODE else 'OFF'}")
                else:
                    print("Unknown command. Try: peers, follow <user_id>, unfollow <user_id>, message <user_id> <content>, verbose, exit")
            
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