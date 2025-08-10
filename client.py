import time
import socket
import threading
from peers import PeerManager
from network import Network
import parser
import utils
import secrets

# Import handlers
from handlers.profile_handler import ProfileHandler
from handlers.social_handler import SocialHandler
from handlers.file_handler import FileHandler
from handlers.group_handler import GroupHandler
from handlers.game_handler import GameHandler

class LSNPClient:
    def __init__(self):
        # Initialize components
        self.peer_manager = PeerManager()
        self.network = Network()
        
        # Get user info
        self.user_id = f"user@{self.get_lan_ip()}"
        self.display_name = input("Enter your display name: ").strip() or "LSNP User"
        
        # Initialize handlers
        self.profile_handler = ProfileHandler(self)
        self.social_handler = SocialHandler(self)
        self.file_handler = FileHandler(self)
        self.group_handler = GroupHandler(self)
        self.game_handler = GameHandler(self)
        
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

        # Send initial message immediately
        self.network.send_message(message_func())
        
        # Start periodic loop
        threading.Thread(target=task_loop, daemon=True).start()

    def start_periodic_ping(self):
        """Send a PING message every 60 seconds."""
        self.start_periodic_task(
            lambda: f"TYPE: PING\nUSER_ID: {self.user_id}\n\n",
            60
        )

    def start_periodic_profile(self):
        """Send a PROFILE message every 60 seconds, including AVATAR fields if present."""
        def profile_message():
            msg = {
                'TYPE': 'PROFILE',
                'USER_ID': self.user_id,
                'DISPLAY_NAME': self.display_name,
                'STATUS': 'Available',
            }
            if hasattr(self.profile_handler, 'avatar_type') and self.profile_handler.avatar_type:
                msg['AVATAR_TYPE'] = self.profile_handler.avatar_type
            if hasattr(self.profile_handler, 'avatar_encoding') and self.profile_handler.avatar_encoding:
                msg['AVATAR_ENCODING'] = self.profile_handler.avatar_encoding
            if hasattr(self.profile_handler, 'avatar_data') and self.profile_handler.avatar_data:
                msg['AVATAR_DATA'] = self.profile_handler.avatar_data
            return parser.format_message(msg)
        self.start_periodic_task(profile_message, 60)

    def announce_presence(self):
        """Immediately announce presence to all peers on startup"""
        utils.log("Announcing presence to network...", level="INFO")
        
        # Send immediate PING
        ping_msg = f"TYPE: PING\nUSER_ID: {self.user_id}\n\n"
        self.network.send_message(ping_msg)
        
        # Send immediate PROFILE
        profile_msg = {
            'TYPE': 'PROFILE',
            'USER_ID': self.user_id,
            'DISPLAY_NAME': self.display_name,
            'STATUS': 'Available',
        }
        if hasattr(self.profile_handler, 'avatar_type') and self.profile_handler.avatar_type:
            profile_msg['AVATAR_TYPE'] = self.profile_handler.avatar_type
        if hasattr(self.profile_handler, 'avatar_encoding') and self.profile_handler.avatar_encoding:
            profile_msg['AVATAR_ENCODING'] = self.profile_handler.avatar_encoding
        if hasattr(self.profile_handler, 'avatar_data') and self.profile_handler.avatar_data:
            profile_msg['AVATAR_DATA'] = self.profile_handler.avatar_data
        
        formatted_profile = parser.format_message(profile_msg)
        self.network.send_message(formatted_profile)
        
        utils.log("Presence announcement sent", level="INFO")

    def handle_message(self, message_text, sender_ip):
        """Process incoming LSNP messages"""
        # Parse the message
        parsed = parser.parse_message(message_text)
        
        if not parsed:
            utils.log("Failed to parse message", level="ERROR")
            return
            
        msg_type = parsed.get('TYPE')
        
        if not msg_type:
            utils.log("Message missing TYPE", level="WARNING")
            return
        
        # Route messages to appropriate handlers
        if msg_type == 'PROFILE':
            self.profile_handler.handle_profile_message(parsed, sender_ip)
        elif msg_type == 'POST':
            self.social_handler.handle_post(parsed, sender_ip)
        elif msg_type == 'DM':
            self.social_handler.handle_dm(parsed, sender_ip)
        elif msg_type == 'FOLLOW':
            self.social_handler.handle_follow(parsed, sender_ip)
        elif msg_type == 'UNFOLLOW':
            self.social_handler.handle_unfollow(parsed, sender_ip)
        elif msg_type == "ACK":
            self.social_handler.handle_ack(parsed, sender_ip)
        elif msg_type == "LIKE":
            self.social_handler.handle_like(parsed, sender_ip)
        elif msg_type == "REVOKE":
            self.social_handler.handle_revoke(parsed, sender_ip)
        elif msg_type == 'FILE_OFFER':
            self.file_handler.handle_file_offer(parsed, sender_ip)
        elif msg_type == 'FILE_CHUNK':
            self.file_handler.handle_file_chunk(parsed, sender_ip)
        elif msg_type == 'FILE_RECEIVED':
            self.file_handler.handle_file_received(parsed, sender_ip)
        elif msg_type == 'FILE_REJECT':
            self.file_handler.handle_file_reject(parsed, sender_ip)
        elif msg_type == 'FILE_REQUEST':
            self.file_handler.handle_file_request(parsed, sender_ip)
        elif msg_type == 'GROUP_CREATE':
            self.group_handler.handle_group_create(parsed, sender_ip)
        elif msg_type == 'GROUP_UPDATE':
            self.group_handler.handle_group_update(parsed, sender_ip)
        elif msg_type == 'GROUP_MESSAGE':
            self.group_handler.handle_group_message(parsed, sender_ip)
        elif msg_type == 'TICTACTOE_INVITE':
            self.game_handler.handle_tictactoe_invite(parsed, sender_ip)
        elif msg_type == 'TICTACTOE_MOVE':
            self.game_handler.handle_tictactoe_move(parsed, sender_ip)
        elif msg_type == 'TICTACTOE_RESULT':
            self.game_handler.handle_tictactoe_result(parsed, sender_ip)
        elif msg_type == 'TICTACTOE_ACCEPT':
            self.game_handler.handle_tictactoe_accept(parsed, sender_ip)
        elif msg_type == 'TICTACTOE_REJECT':
            self.game_handler.handle_tictactoe_reject(parsed, sender_ip)
        else:
            utils.log(f"Unknown message type: {msg_type}", level="WARNING")

    def _validate_token_or_log(self, token, expected_scope, expected_user_id, sender_ip=None, message_type=None):
        valid = utils.validate_token(token, expected_scope=expected_scope, expected_user_id=expected_user_id)
        utils.log_token_check(token, expected_scope, expected_user_id, valid, sender_ip)
        if not valid:
            utils.log_message_drop("invalid_token", message_type, sender_ip)
        return valid

    def get_user_id_by_display_name(self, display_name):
        """Find user ID by display name"""
        for user_id, peer_info in self.peer_manager.peers.items():
            if peer_info.get('display_name') == display_name:
                return user_id
        return None

    def run(self):
        """Start the client"""
        # Start periodic tasks
        self.start_periodic_ping()
        self.start_periodic_profile()
        
        # Announce presence
        self.announce_presence()
        
        # Start CLI
        from cli import CLI
        cli = CLI(self)
        cli.run()

    def cleanup(self):
        """Cleanup resources"""
        self.network.stop_listening()
