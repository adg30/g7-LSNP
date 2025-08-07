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
        self.incoming_files = {}  # file_id -> {'filename': ..., 'chunks': {}, 'total': N, 'hash': ..., 'from': ...}
        self.groups = {}  # group_id -> {'name': ..., 'members': set(), 'meta': {...}}
        self.tictactoe_games = {}  # game_id -> {'players': [X, O], 'board': [...], 'turn': X, 'moves': [], 'status': ...}

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
        """Send a PROFILE message every 300 seconds, including AVATAR fields if present."""
        def profile_message():
            msg = {
                'TYPE': 'PROFILE',
                'USER_ID': self.user_id,
                'DISPLAY_NAME': self.display_name,
                'STATUS': 'Available',
            }
            if hasattr(self, 'avatar_url') and self.avatar_url:
                msg['AVATAR_URL'] = self.avatar_url
            if hasattr(self, 'avatar_hash') and self.avatar_hash:
                msg['AVATAR_HASH'] = self.avatar_hash
            return parser.format_message(msg)
        self.start_periodic_task(profile_message, 300)

    def send_initial_discovery(self):
        """Send immediate PING and PROFILE messages to discover existing peers"""
        utils.log("Sending initial discovery messages...", level="INFO")
        
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
        if hasattr(self, 'avatar_url') and self.avatar_url:
            profile_msg['AVATAR_URL'] = self.avatar_url
        if hasattr(self, 'avatar_hash') and self.avatar_hash:
            profile_msg['AVATAR_HASH'] = self.avatar_hash
        
        self.network.send_message(parser.format_message(profile_msg))
        
        # Send additional discovery messages after a short delay to catch peers that might have missed the first ones
        def delayed_discovery():
            time.sleep(2)  # Wait 2 seconds
            utils.log("Sending delayed discovery messages...", level="INFO")
            self.network.send_message(ping_msg)
            self.network.send_message(parser.format_message(profile_msg))
            
            # Send one more round after 5 seconds to ensure discovery
            time.sleep(3)  # Additional 3 seconds (total 5 seconds from start)
            utils.log("Sending final discovery messages...", level="INFO")
            self.network.send_message(ping_msg)
            self.network.send_message(parser.format_message(profile_msg))
        
        threading.Thread(target=delayed_discovery, daemon=True).start()

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
        if msg_type == 'PING':
            self.handle_ping(parsed, sender_ip)
        elif msg_type == 'PROFILE':
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
        elif msg_type == "REVOKE":
            self.handle_revoke(parsed, sender_ip)
        elif msg_type == 'FILE_OFFER':
            self.handle_file_offer(parsed, sender_ip)
        elif msg_type == 'FILE_CHUNK':
            self.handle_file_chunk(parsed, sender_ip)
        elif msg_type == 'FILE_RECEIVED':
            self.handle_file_received(parsed, sender_ip)
        elif msg_type == 'GROUP_CREATE':
            self.handle_group_create(parsed, sender_ip)
        elif msg_type == 'GROUP_UPDATE':
            self.handle_group_update(parsed, sender_ip)
        elif msg_type == 'GROUP_MESSAGE':
            self.handle_group_message(parsed, sender_ip)
        elif msg_type == 'TICTACTOE_INVITE':
            self.handle_tictactoe_invite(parsed, sender_ip)
        elif msg_type == 'TICTACTOE_MOVE':
            self.handle_tictactoe_move(parsed, sender_ip)
        elif msg_type == 'TICTACTOE_RESULT':
            self.handle_tictactoe_result(parsed, sender_ip)
        # Add more message types later
    
    def handle_ping(self, parsed, sender_ip):
        """Handle PING messages for peer discovery"""
        user_id = parsed.get('USER_ID')
        if user_id and user_id != self.user_id:
            # Add peer with basic info from PING
            self.peer_manager.add_peer(
                user_id=user_id,
                ip_address=sender_ip
            )
            utils.log(f"Received PING from {user_id} at {sender_ip}", level="INFO")
            
            # Respond with our own PING to help with discovery
            response_ping = f"TYPE: PING\nUSER_ID: {self.user_id}\n\n"
            self.network.send_message(response_ping, dest_ip=sender_ip)
            utils.log(f"Sent PING response to {sender_ip}", level="INFO")
    
    def handle_profile_message(self, parsed, sender_ip):
        """Handle PROFILE messages, including AVATAR fields if present"""
        self.peer_manager.add_peer(
            user_id=parsed['USER_ID'],
            display_name=parsed.get('DISPLAY_NAME'),
            status=parsed.get('STATUS'),
            ip_address=sender_ip,
            avatar_url=parsed.get('AVATAR_URL'),
            avatar_hash=parsed.get('AVATAR_HASH'),
        )
        
        # Respond with our own PROFILE to help with discovery
        profile_msg = {
            'TYPE': 'PROFILE',
            'USER_ID': self.user_id,
            'DISPLAY_NAME': self.display_name,
            'STATUS': 'Available',
        }
        if hasattr(self, 'avatar_url') and self.avatar_url:
            profile_msg['AVATAR_URL'] = self.avatar_url
        if hasattr(self, 'avatar_hash') and self.avatar_hash:
            profile_msg['AVATAR_HASH'] = self.avatar_hash
        
        response_profile = parser.format_message(profile_msg)
        self.network.send_message(response_profile, dest_ip=sender_ip)
        utils.log(f"Sent PROFILE response to {sender_ip}", level="INFO")


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

        if not self._validate_token_or_log(token, expected_scope='follow', expected_user_id=follower_id, sender_ip=sender_ip, message_type='FOLLOW'):
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

        if not self._validate_token_or_log(token, expected_scope='follow', expected_user_id=unfollower_id, sender_ip=sender_ip, message_type='UNFOLLOW'):
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

        # Send only to followers (as per RFC/rubric)
        for follower_id in self.peer_manager.get_followers(self.user_id):
            peer_info = self.peer_manager.peers.get(follower_id)
            if peer_info and peer_info.get('ip_address'):
                self.network.send_message(msg, dest_ip=peer_info['ip_address'])
        
        print(f"\n[POST] You posted: {content}")

    def handle_post(self, parsed, sender_ip):
        from_user = parsed.get('USER_ID')
        content = parsed.get('CONTENT')
        token = parsed.get('TOKEN')
        if not self._validate_token_or_log(token, expected_scope='broadcast', expected_user_id=from_user, sender_ip=sender_ip, message_type='POST'):
            return
        display_name = self.peer_manager.get_display_name(from_user)
        print(f"\n[POST] {display_name}: {content}")
        
        # Store received post
        if not hasattr(self, 'posts'):
            self.posts = {}
        if timestamp:
            self.posts[int(timestamp)] = {
                'content': content,
                'user_id': from_user,
                'timestamp': int(timestamp)
            }


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
        if to_user != self.user_id:
            return
        if not self._validate_token_or_log(token, expected_scope='chat', expected_user_id=from_user, sender_ip=sender_ip, message_type='DM'):
            return
        display_name = self.peer_manager.get_display_name(from_user)
        print(f"\n[DM] {display_name}: {content}")
        self.send_ack(message_id, sender_ip)

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
            return
        if not self._validate_token_or_log(token, expected_scope='broadcast', expected_user_id=from_user, sender_ip=sender_ip, message_type='LIKE'):
            return
        display_name = self.peer_manager.get_display_name(from_user)
        verb = "likes" if action == "LIKE" else "unlikes"
        print(f"\n{display_name} {verb} your post [post @ {post_timestamp}]")

#-------------------------- revoke

    def send_revoke(self, token: str):
        """Broadcasts a REVOKE message for the given token."""
        msg = parser.format_message({
            'TYPE' : 'REVOKE',
            'TOKEN': token
        })

        self.network.send_message(msg)

    def handle_revoke(self, parsed: dict, sender_ip: str):
        """Handles an incoming REVOKE message."""
        token = parsed.get("TOKEN")  # <- this line MUST exist

        if not token:
            utils.log("REVOKE message missing token", level="WARN", sender_ip=sender_ip)
            return

        utils.revoke_token(token)
        utils.log(f"Token revoked from {sender_ip}", level="INFO", message_type="REVOKE")


#--------------------------

    # --- FILE TRANSFER (Milestone 3) ---
    def send_file_offer(self, target_user_id, filename, filesize, filehash):
        now = int(time.time())
        ttl_seconds = 3600
        token = f"{self.user_id}|{now + ttl_seconds}|file"
        message_id = secrets.token_hex(8)
        msg = parser.format_message({
            'TYPE': 'FILE_OFFER',
            'FROM': self.user_id,
            'TO': target_user_id,
            'FILENAME': filename,
            'FILESIZE': filesize,
            'FILEHASH': filehash,
            'MESSAGE_ID': message_id,
            'TIMESTAMP': now,
            'TOKEN': token,
        })
        peer_info = self.peer_manager.peers.get(target_user_id)
        if peer_info and peer_info.get('ip_address'):
            dest_ip = peer_info['ip_address']
            self.network.send_message(msg, dest_ip=dest_ip)
            utils.log(f"Sent FILE_OFFER for {filename} to {target_user_id} via {dest_ip}", level="INFO")
        else:
            utils.log(f"Cannot send FILE_OFFER — no known IP for {target_user_id}", level="WARN")

    def handle_file_offer(self, parsed, sender_ip):
        from_user = parsed.get('FROM')
        to_user = parsed.get('TO')
        filename = parsed.get('FILENAME')
        filesize = parsed.get('FILESIZE')
        filehash = parsed.get('FILEHASH')
        token = parsed.get('TOKEN')
        if to_user != self.user_id:
            return
        if not self._validate_token_or_log(token, expected_scope='file', expected_user_id=from_user, sender_ip=sender_ip, message_type='FILE_OFFER'):
            return
        display_name = self.peer_manager.get_display_name(from_user)
        utils.log_protocol_event("FILE_OFFER_RECEIVED", f"file={filename} size={filesize} from={display_name}", sender_ip, "FILE_OFFER")
        print(f"\n[FILE_OFFER] {display_name} wants to send you '{filename}' ({filesize} bytes, hash: {filehash})")
        # TODO: Prompt user to accept/reject, then send ACK or start receiving chunks

    def send_file_chunk(self, target_user_id, file_id, chunk_index, chunk_data):
        now = int(time.time())
        ttl_seconds = 3600
        token = f"{self.user_id}|{now + ttl_seconds}|file"
        msg = parser.format_message({
            'TYPE': 'FILE_CHUNK',
            'FROM': self.user_id,
            'TO': target_user_id,
            'FILE_ID': file_id,
            'CHUNK_INDEX': chunk_index,
            'TIMESTAMP': now,
            'TOKEN': token,
            'RAW_CONTENT': utils.base64_encode(chunk_data),
        })
        peer_info = self.peer_manager.peers.get(target_user_id)
        if peer_info and peer_info.get('ip_address'):
            dest_ip = peer_info['ip_address']
            self.network.send_message(msg, dest_ip=dest_ip)
            utils.log(f"Sent FILE_CHUNK {chunk_index} for {file_id} to {target_user_id} via {dest_ip}", level="INFO")
        else:
            utils.log(f"Cannot send FILE_CHUNK — no known IP for {target_user_id}", level="WARN")

    def handle_file_chunk(self, parsed, sender_ip):
        from_user = parsed.get('FROM')
        to_user = parsed.get('TO')
        file_id = parsed.get('FILE_ID')
        chunk_index = int(parsed.get('CHUNK_INDEX', -1))
        token = parsed.get('TOKEN')
        raw_content = parsed.get('RAW_CONTENT')
        if to_user != self.user_id or file_id is None or chunk_index < 0 or raw_content is None:
            return
        if not self._validate_token_or_log(token, expected_scope='file', expected_user_id=from_user, sender_ip=sender_ip, message_type='FILE_CHUNK'):
            return
        chunk_data = utils.base64_decode(raw_content)
        if file_id not in self.incoming_files:
            self.incoming_files[file_id] = {'chunks': {}, 'from': from_user}
        self.incoming_files[file_id]['chunks'][chunk_index] = chunk_data
        utils.log(f"Received FILE_CHUNK {chunk_index} for {file_id} from {from_user}", level="INFO")
        # TODO: Check if all chunks received, reassemble, verify hash, send FILE_RECEIVED

    def send_file_received(self, target_user_id, file_id):
        now = int(time.time())
        ttl_seconds = 3600
        token = f"{self.user_id}|{now + ttl_seconds}|file"
        msg = parser.format_message({
            'TYPE': 'FILE_RECEIVED',
            'FROM': self.user_id,
            'TO': target_user_id,
            'FILE_ID': file_id,
            'TIMESTAMP': now,
            'TOKEN': token,
        })
        peer_info = self.peer_manager.peers.get(target_user_id)
        if peer_info and peer_info.get('ip_address'):
            dest_ip = peer_info['ip_address']
            self.network.send_message(msg, dest_ip=dest_ip)
            utils.log(f"Sent FILE_RECEIVED for {file_id} to {target_user_id} via {dest_ip}", level="INFO")
        else:
            utils.log(f"Cannot send FILE_RECEIVED — no known IP for {target_user_id}", level="WARN")

    def handle_file_received(self, parsed, sender_ip):
        from_user = parsed.get('FROM')
        to_user = parsed.get('TO')
        file_id = parsed.get('FILE_ID')
        token = parsed.get('TOKEN')
        if to_user != self.user_id or file_id is None:
            return
        if not self._validate_token_or_log(token, expected_scope='file', expected_user_id=from_user, sender_ip=sender_ip, message_type='FILE_RECEIVED'):
            return
        utils.log(f"File transfer complete: {file_id} acknowledged by {from_user}", level="INFO")
        print(f"\n[FILE_TRANSFER] File {file_id} successfully received by {from_user}.")

    # --- GROUP MANAGEMENT (Milestone 3) ---
    def send_group_create(self, group_id, group_name, members):
        now = int(time.time())
        ttl_seconds = 3600
        token = f"{self.user_id}|{now + ttl_seconds}|group"
        msg = parser.format_message({
            'TYPE': 'GROUP_CREATE',
            'GROUP_ID': group_id,
            'GROUP_NAME': group_name,
            'MEMBERS': ','.join(members),
            'FROM': self.user_id,
            'TIMESTAMP': now,
            'TOKEN': token,
        })
        for member in members:
            peer_info = self.peer_manager.peers.get(member)
            if peer_info and peer_info.get('ip_address'):
                dest_ip = peer_info['ip_address']
                self.network.send_message(msg, dest_ip=dest_ip)
                utils.log(f"Sent GROUP_CREATE for {group_id} to {member} via {dest_ip}", level="INFO")

    def handle_group_create(self, parsed, sender_ip):
        group_id = parsed.get('GROUP_ID')
        group_name = parsed.get('GROUP_NAME')
        members = set(parsed.get('MEMBERS', '').split(','))
        token = parsed.get('TOKEN')
        from_user = parsed.get('FROM')
        if not self._validate_token_or_log(token, expected_scope='group', expected_user_id=from_user, sender_ip=sender_ip, message_type='GROUP_CREATE'):
            return
        self.groups[group_id] = {'name': group_name, 'members': members, 'meta': {}}
        utils.log_protocol_event("GROUP_CREATED", f"group={group_name} members={len(members)}", sender_ip, "GROUP_CREATE")
        utils.log(f"Joined group {group_name} ({group_id}) with members: {members}", level="INFO")
        print(f"\n[GROUP] Joined group '{group_name}' ({group_id})")

    def send_group_update(self, group_id, members):
        now = int(time.time())
        ttl_seconds = 3600
        token = f"{self.user_id}|{now + ttl_seconds}|group"
        msg = parser.format_message({
            'TYPE': 'GROUP_UPDATE',
            'GROUP_ID': group_id,
            'MEMBERS': ','.join(members),
            'FROM': self.user_id,
            'TIMESTAMP': now,
            'TOKEN': token,
        })
        for member in members:
            peer_info = self.peer_manager.peers.get(member)
            if peer_info and peer_info.get('ip_address'):
                dest_ip = peer_info['ip_address']
                self.network.send_message(msg, dest_ip=dest_ip)
                utils.log(f"Sent GROUP_UPDATE for {group_id} to {member} via {dest_ip}", level="INFO")

    def handle_group_update(self, parsed, sender_ip):
        group_id = parsed.get('GROUP_ID')
        members = set(parsed.get('MEMBERS', '').split(','))
        token = parsed.get('TOKEN')
        from_user = parsed.get('FROM')
        if not self._validate_token_or_log(token, expected_scope='group', expected_user_id=from_user, sender_ip=sender_ip, message_type='GROUP_UPDATE'):
            return
        if group_id in self.groups:
            self.groups[group_id]['members'] = members
            utils.log(f"Updated group {group_id} members: {members}", level="INFO")
            print(f"\n[GROUP] Updated group '{group_id}' members: {members}")

    def send_group_message(self, group_id, content):
        now = int(time.time())
        ttl_seconds = 3600
        token = f"{self.user_id}|{now + ttl_seconds}|group"
        msg = parser.format_message({
            'TYPE': 'GROUP_MESSAGE',
            'GROUP_ID': group_id,
            'FROM': self.user_id,
            'CONTENT': content,
            'TIMESTAMP': now,
            'TOKEN': token,
        })
        members = self.groups.get(group_id, {}).get('members', set())
        for member in members:
            if member == self.user_id:
                continue
            peer_info = self.peer_manager.peers.get(member)
            if peer_info and peer_info.get('ip_address'):
                dest_ip = peer_info['ip_address']
                self.network.send_message(msg, dest_ip=dest_ip)
                utils.log(f"Sent GROUP_MESSAGE for {group_id} to {member} via {dest_ip}", level="INFO")

    def handle_group_message(self, parsed, sender_ip):
        group_id = parsed.get('GROUP_ID')
        from_user = parsed.get('FROM')
        content = parsed.get('CONTENT')
        token = parsed.get('TOKEN')
        if not self._validate_token_or_log(token, expected_scope='group', expected_user_id=from_user, sender_ip=sender_ip, message_type='GROUP_MESSAGE'):
            return
        if group_id not in self.groups:
            return
        display_name = self.peer_manager.get_display_name(from_user)
        print(f"\n[GROUP:{group_id}] {display_name}: {content}")
        utils.log(f"Received GROUP_MESSAGE in {group_id} from {from_user}", level="INFO")

    # --- TIC TAC TOE GAME (Milestone 3) ---
    def send_tictactoe_invite(self, target_user_id, game_id):
        now = int(time.time())
        ttl_seconds = 3600
        token = f"{self.user_id}|{now + ttl_seconds}|game"
        msg = parser.format_message({
            'TYPE': 'TICTACTOE_INVITE',
            'GAME_ID': game_id,
            'FROM': self.user_id,
            'TO': target_user_id,
            'TIMESTAMP': now,
            'TOKEN': token,
        })
        peer_info = self.peer_manager.peers.get(target_user_id)
        if peer_info and peer_info.get('ip_address'):
            dest_ip = peer_info['ip_address']
            self.network.send_message(msg, dest_ip=dest_ip)
            utils.log(f"Sent TICTACTOE_INVITE for {game_id} to {target_user_id} via {dest_ip}", level="INFO")

    def handle_tictactoe_invite(self, parsed, sender_ip):
        game_id = parsed.get('GAME_ID')
        from_user = parsed.get('FROM')
        to_user = parsed.get('TO')
        token = parsed.get('TOKEN')
        if to_user != self.user_id:
            return
        if not self._validate_token_or_log(token, expected_scope='game', expected_user_id=from_user, sender_ip=sender_ip, message_type='TICTACTOE_INVITE'):
            return
        self.tictactoe_games[game_id] = {
            'players': [from_user, self.user_id],
            'board': [' '] * 9,
            'turn': from_user,
            'moves': [],
            'status': 'active',
        }
        display_name = self.peer_manager.get_display_name(from_user)
        utils.log_protocol_event("GAME_INVITE_RECEIVED", f"game={game_id} from={display_name}", sender_ip, "TICTACTOE_INVITE")
        print(f"\n[TICTACTOE] Game invite from {display_name} (game_id: {game_id})")
        print(f"Type 'ttt accept {game_id}' to accept the game")

    def check_win_condition(self, board):
        """Check if there's a winner or draw"""
        # Winning combinations
        win_combinations = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
            [0, 4, 8], [2, 4, 6]  # Diagonals
        ]
        
        for combo in win_combinations:
            if board[combo[0]] == board[combo[1]] == board[combo[2]] != ' ':
                return board[combo[0]]  # Return winner (X or O)
        
        # Check for draw
        if ' ' not in board:
            return 'DRAW'
        
        return None  # Game continues

    def handle_tictactoe_move(self, parsed, sender_ip):
        game_id = parsed.get('GAME_ID')
        from_user = parsed.get('FROM')
        position = int(parsed.get('POSITION', -1))
        token = parsed.get('TOKEN')
        if game_id not in self.tictactoe_games or position < 0 or position > 8:
            return
        if not self._validate_token_or_log(token, expected_scope='game', expected_user_id=from_user, sender_ip=sender_ip, message_type='TICTACTOE_MOVE'):
            return
        game = self.tictactoe_games[game_id]
        if position in game['moves']:
            utils.log(f"Duplicate move detected for {game_id} at {position}", level="WARN")
            return
        if game['turn'] != from_user:
            utils.log(f"Not {from_user}'s turn in game {game_id}", level="WARN")
            return
        game['moves'].append(position)
        mark = 'X' if from_user == game['players'][0] else 'O'
        game['board'][position] = mark
        game['turn'] = [p for p in game['players'] if p != from_user][0]
        utils.log(f"Received TICTACTOE_MOVE in {game_id} from {from_user} at {position}", level="INFO")
        print(f"\n[TICTACTOE:{game_id}] {from_user} played {mark} at {position}")
        
        # Check for win/draw
        result = self.check_win_condition(game['board'])
        if result:
            if result == 'DRAW':
                game['status'] = 'draw'
                print(f"\n[TICTACTOE:{game_id}] Game ended in a DRAW!")
                self.send_tictactoe_result(game_id, 'DRAW')
            else:
                game['status'] = 'won'
                winner = from_user
                print(f"\n[TICTACTOE:{game_id}] {winner} ({result}) WINS!")
                self.send_tictactoe_result(game_id, f'WIN_{result}_{winner}')
        else:
            print(f"\n[TICTACTOE:{game_id}] Your turn! Use 'ttt move {game_id} <position>'")

    def send_tictactoe_move(self, game_id, position):
        now = int(time.time())
        ttl_seconds = 3600
        token = f"{self.user_id}|{now + ttl_seconds}|game"
        msg = parser.format_message({
            'TYPE': 'TICTACTOE_MOVE',
            'GAME_ID': game_id,
            'FROM': self.user_id,
            'POSITION': position,
            'TIMESTAMP': now,
            'TOKEN': token,
        })
        players = self.tictactoe_games.get(game_id, {}).get('players', [])
        for player in players:
            if player == self.user_id:
                continue
            peer_info = self.peer_manager.peers.get(player)
            if peer_info and peer_info.get('ip_address'):
                dest_ip = peer_info['ip_address']
                self.network.send_message(msg, dest_ip=dest_ip)
                utils.log(f"Sent TICTACTOE_MOVE for {game_id} to {player} via {dest_ip}", level="INFO")

    def send_tictactoe_result(self, game_id, result):
        now = int(time.time())
        ttl_seconds = 3600
        token = f"{self.user_id}|{now + ttl_seconds}|game"
        msg = parser.format_message({
            'TYPE': 'TICTACTOE_RESULT',
            'GAME_ID': game_id,
            'FROM': self.user_id,
            'RESULT': result,
            'TIMESTAMP': now,
            'TOKEN': token,
        })
        players = self.tictactoe_games.get(game_id, {}).get('players', [])
        for player in players:
            if player == self.user_id:
                continue
            peer_info = self.peer_manager.peers.get(player)
            if peer_info and peer_info.get('ip_address'):
                dest_ip = peer_info['ip_address']
                self.network.send_message(msg, dest_ip=dest_ip)
                utils.log(f"Sent TICTACTOE_RESULT for {game_id} to {player} via {dest_ip}", level="INFO")

    def handle_tictactoe_result(self, parsed, sender_ip):
        game_id = parsed.get('GAME_ID')
        from_user = parsed.get('FROM')
        result = parsed.get('RESULT')
        token = parsed.get('TOKEN')
        if game_id not in self.tictactoe_games:
            return
        if not self._validate_token_or_log(token, expected_scope='game', expected_user_id=from_user, sender_ip=sender_ip, message_type='TICTACTOE_RESULT'):
            return
        self.tictactoe_games[game_id]['status'] = 'finished'
        utils.log(f"Game {game_id} finished: {result}", level="INFO")
        print(f"\n[TICTACTOE:{game_id}] Game finished: {result}")

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

    def run_cli(self):
        """Main CLI loop"""
        print(f"\n=== LSNP Client for {self.user_id} ===")
        print("=== BASIC COMMANDS (Milestone 2) ===")
        print("  peers                    - Show all discovered peers")
        print("  follow <user_id>         - Follow a user (use full user@IP format)")
        print("  unfollow <user_id>       - Unfollow a user")
        print("  followers                - Show your followers")
        print("  post                     - Create a new post")
        print("  message <user_id> <text> - Send private message")
        print("  like <user_id> <timestamp> - Like a post")
        print("  unlike <user_id> <timestamp> - Unlike a post")
        print("  revoke <token>           - Revoke a token")
        print("  verbose                  - Toggle verbose logging")
        print("\n=== ADVANCED COMMANDS (Milestone 3) ===")
        print("  sendfile <user_id> <file> - Send file to user")
        print("  acceptfile <file_id>     - Accept a file transfer")
        print("  rejectfile <file_id>     - Reject a file transfer")
        print("  group create <id> <name> <members> - Create group (members: user1,user2)")
        print("  group message <id> <text> - Send message to group")
        print("  group list               - List your groups")
        print("  group members <id>       - Show group members")
        print("  ttt invite <user_id>     - Invite to Tic Tac Toe")
        print("  ttt accept <game_id>     - Accept Tic Tac Toe game")
        print("  ttt move <game_id> <pos> - Make move (0-8)")
        print("  ttt board <game_id>      - Show game board")
        print("  ttt list                 - List active games")
        print("\n  exit                     - Exit program")
        print("\n=== EXAMPLES ===")
        print("  follow user@192.168.1.4")
        print("  message user@192.168.1.4 Hello there!")
        print("  group create mygroup 'My Group' user@192.168.1.4,user@192.168.1.5")
        print("  sendfile user@192.168.1.4 test.txt")
        print("  ttt invite user@192.168.1.4")
        print("  ttt accept game_1234567890")
        print("\n=== TIPS ===")
        print("  - You can use display names (like 'pc') instead of full user IDs")
        print("  - Use 'peers' to see all available users and their IDs")
        print("  - Use 'verbose' to see detailed protocol logs")
        print("  - Posts are sent only to your followers (follow each other first)")
        print("  - Use 'follow <user_id>' to follow someone before posting")
        
        while True:
            try:
                cmd = input("\nLSNP> ").strip().split()
                
                if not cmd:
                    continue
                    
                command = cmd[0].lower()
                
                if command == "exit":
                    break
                elif command == "help":
                    print(f"\n=== LSNP Client for {self.user_id} ===")
                    print("=== BASIC COMMANDS (Milestone 2) ===")
                    print("  peers                    - Show all discovered peers")
                    print("  follow <user_id>         - Follow a user (use full user@IP format)")
                    print("  unfollow <user_id>       - Unfollow a user")
                    print("  followers                - Show your followers")
                    print("  post                     - Create a new post")
                    print("  message <user_id> <text> - Send private message")
                    print("  like <user_id> <timestamp> - Like a post")
                    print("  unlike <user_id> <timestamp> - Unlike a post")
                    print("  revoke <token>           - Revoke a token")
                    print("  verbose                  - Toggle verbose logging")
                    print("\n=== ADVANCED COMMANDS (Milestone 3) ===")
                    print("  sendfile <user_id> <file> - Send file to user")
                    print("  acceptfile <file_id>     - Accept a file transfer")
                    print("  rejectfile <file_id>     - Reject a file transfer")
                    print("  group create <id> <name> <members> - Create group (members: user1,user2)")
                    print("  group message <id> <text> - Send message to group")
                    print("  group list               - List your groups")
                    print("  group members <id>       - Show group members")
                    print("  ttt invite <user_id>     - Invite to Tic Tac Toe")
                    print("  ttt accept <game_id>     - Accept Tic Tac Toe game")
                    print("  ttt move <game_id> <pos> - Make move (0-8)")
                    print("  ttt board <game_id>      - Show game board")
                    print("  ttt list                 - List active games")
                    print("\n  exit                     - Exit program")
                    print("\n=== EXAMPLES ===")
                    print("  follow user@192.168.1.4")
                    print("  message user@192.168.1.4 Hello there!")
                    print("  group create mygroup 'My Group' user@192.168.1.4,user@192.168.1.5")
                    print("  sendfile user@192.168.1.4 test.txt")
                    print("  ttt invite user@192.168.1.4")
                    print("  ttt accept game_1234567890")
                    print("\n=== TIPS ===")
                    print("  - You can use display names (like 'pc') instead of full user IDs")
                    print("  - Use 'peers' to see all available users and their IDs")
                    print("  - Use 'verbose' to see detailed protocol logs")
                    print("  - Posts are sent only to your followers (follow each other first)")
                    print("  - Use 'follow <user_id>' to follow someone before posting")
                elif command == "peers":
                    self.peer_manager.display_all_peers()
                elif command == "follow":
                    if len(cmd) > 1:
                        target = cmd[1]
                        # Try to find user ID by display name if not full user ID
                        if not target.startswith("user@"):
                            user_id = self.get_user_id_by_display_name(target)
                            if user_id:
                                target = user_id
                            else:
                                print(f"User '{target}' not found. Use full user ID (e.g., user@192.168.1.4)")
                                continue
                        self.send_follow_action(target, "FOLLOW")
                    else:
                        print("Usage: follow <user_id>")
                        print("Example: follow user@192.168.1.4")

                elif command == "unfollow":
                    if len(cmd) > 1:
                        target = cmd[1]
                        # Try to find user ID by display name if not full user ID
                        if not target.startswith("user@"):
                            user_id = self.get_user_id_by_display_name(target)
                            if user_id:
                                target = user_id
                            else:
                                print(f"User '{target}' not found. Use full user ID (e.g., user@192.168.1.4)")
                                continue
                        self.send_follow_action(target, "UNFOLLOW")
                    else:
                        print("Usage: unfollow <user_id>")
                        print("Example: unfollow user@192.168.1.4")

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
                        target = cmd[1]
                        # Try to find user ID by display name if not full user ID
                        if not target.startswith("user@"):
                            user_id = self.get_user_id_by_display_name(target)
                            if user_id:
                                target = user_id
                            else:
                                print(f"User '{target}' not found. Use full user ID (e.g., user@192.168.1.4)")
                                continue
                        content = " ".join(cmd[2:])
                        self.send_dm(target, content)
                    else:
                        print("Usage: message <user_id> <content>")
                        print("Example: message user@192.168.1.4 Hello there!")

                elif command == "like":
                    if len(cmd) > 2:
                        target = cmd[1]
                        # Try to find user ID by display name if not full user ID
                        if not target.startswith("user@"):
                            user_id = self.get_user_id_by_display_name(target)
                            if user_id:
                                target = user_id
                            else:
                                print(f"User '{target}' not found. Use full user ID (e.g., user@192.168.1.4)")
                                continue
                        post_timestamp = cmd[2]
                        self.send_like(target, post_timestamp, action="LIKE")
                    else:
                        print("Usage: like <user_id> <post_timestamp>")
                        print("Example: like user@192.168.1.4 1234567890")

                elif command == "unlike":
                    if len(cmd) > 2:
                        target = cmd[1]
                        # Try to find user ID by display name if not full user ID
                        if not target.startswith("user@"):
                            user_id = self.get_user_id_by_display_name(target)
                            if user_id:
                                target = user_id
                            else:
                                print(f"User '{target}' not found. Use full user ID (e.g., user@192.168.1.4)")
                                continue
                        post_timestamp = cmd[2]
                        self.send_like(target, post_timestamp, action="UNLIKE")
                    else:
                        print("Usage: unlike <user_id> <post_timestamp>")
                        print("Example: unlike user@192.168.1.4 1234567890")

                elif command == "revoke":
                    if len(cmd) == 2:
                        token = cmd[1]
                        self.send_revoke(token)
                    else:
                        print("Usage: revoke <token>")
                        print("Example: revoke user@192.168.1.4|1234567890|follow")
                        print("Note: Revoke invalidates a token, preventing its future use")

                elif command == "verbose":
                    import config
                    config.VERBOSE_MODE = not config.VERBOSE_MODE
                    print(f"Verbose mode: {'ON' if config.VERBOSE_MODE else 'OFF'}")

                # --- NEW MILESTONE 3 COMMANDS ---
                elif command == "sendfile":
                    if len(cmd) > 2:
                        target = cmd[1]
                        # Try to find user ID by display name if not full user ID
                        if not target.startswith("user@"):
                            user_id = self.get_user_id_by_display_name(target)
                            if user_id:
                                target = user_id
                            else:
                                print(f"User '{target}' not found. Use full user ID (e.g., user@192.168.1.4)")
                                continue
                        filename = cmd[2]
                        try:
                            import os
                            filesize = os.path.getsize(filename)
                            filehash = str(hash(filename))  # Simple hash for demo
                            self.send_file_offer(target, filename, filesize, filehash)
                            print(f"File offer sent for {filename}")
                        except FileNotFoundError:
                            print(f"File {filename} not found")
                        except Exception as e:
                            print(f"Error: {e}")
                    else:
                        print("Usage: sendfile <user_id> <filename>")
                        print("Example: sendfile user@192.168.1.4 test.txt")

                elif command == "acceptfile":
                    if len(cmd) > 1:
                        file_id = cmd[1]
                        if file_id in self.incoming_files:
                            print(f"Accepting file transfer for {file_id}")
                            # TODO: Implement actual file acceptance logic
                            print("File acceptance not fully implemented yet")
                        else:
                            print(f"File {file_id} not found in pending transfers")
                    else:
                        print("Usage: acceptfile <file_id>")

                elif command == "rejectfile":
                    if len(cmd) > 1:
                        file_id = cmd[1]
                        if file_id in self.incoming_files:
                            print(f"Rejecting file transfer for {file_id}")
                            del self.incoming_files[file_id]
                        else:
                            print(f"File {file_id} not found in pending transfers")
                    else:
                        print("Usage: rejectfile <file_id>")

                elif command == "group":
                    if len(cmd) < 2:
                        print("Usage: group <create|message|list|members> [args...]")
                        print("Examples:")
                        print("  group create mygroup 'My Group' user@192.168.1.4,user@192.168.1.5")
                        print("  group message mygroup Hello group!")
                        print("  group list")
                        print("  group members mygroup")
                        continue
                    
                    subcmd = cmd[1].lower()
                    if subcmd == "create" and len(cmd) > 4:
                        group_id = cmd[2]
                        group_name = cmd[3]
                        # Join all remaining arguments as members (comma-separated)
                        members_str = " ".join(cmd[4:])
                        members = [m.strip() for m in members_str.split(',') if m.strip()]
                        # Convert display names to user IDs
                        resolved_members = []
                        for member in members:
                            if member.startswith("user@"):
                                resolved_members.append(member)
                            else:
                                user_id = self.get_user_id_by_display_name(member)
                                if user_id:
                                    resolved_members.append(user_id)
                                else:
                                    print(f"Warning: User '{member}' not found, skipping")
                        if resolved_members:
                            self.send_group_create(group_id, group_name, resolved_members)
                            print(f"Group {group_name} created with members: {resolved_members}")
                        else:
                            print("No valid members found for group creation")
                    elif subcmd == "message" and len(cmd) > 3:
                        group_id = cmd[2]
                        content = " ".join(cmd[3:])
                        self.send_group_message(group_id, content)
                        print(f"Group message sent to {group_id}")
                    elif subcmd == "list":
                        if self.groups:
                            print("\n=== Your Groups ===")
                            for group_id, group_info in self.groups.items():
                                print(f"{group_id}: {group_info['name']} ({len(group_info['members'])} members)")
                        else:
                            print("No groups joined")
                    elif subcmd == "members" and len(cmd) > 2:
                        group_id = cmd[2]
                        if group_id in self.groups:
                            members = self.groups[group_id]['members']
                            print(f"\n=== Members of {group_id} ===")
                            for member in members:
                                if member:  # Skip empty strings
                                    display_name = self.peer_manager.get_display_name(member)
                                    print(f"- {display_name} ({member})")
                        else:
                            print(f"Group {group_id} not found")
                    else:
                        print("Usage: group <create|message|list|members> [args...]")
                        print("Examples:")
                        print("  group create mygroup 'My Group' user@192.168.1.4,user@192.168.1.5")
                        print("  group message mygroup Hello group!")
                        print("  group list")
                        print("  group members mygroup")

                elif command == "ttt":
                    if len(cmd) < 2:
                        print("Usage: ttt <invite|move|board|list> [args...]")
                        print("Examples:")
                        print("  ttt invite user@192.168.1.4")
                        print("  ttt move game_1234567890 4")
                        print("  ttt board game_1234567890")
                        print("  ttt list")
                        continue
                    
                    subcmd = cmd[1].lower()
                    if subcmd == "invite" and len(cmd) > 2:
                        target = cmd[2]
                        # Try to find user ID by display name if not full user ID
                        if not target.startswith("user@"):
                            user_id = self.get_user_id_by_display_name(target)
                            if user_id:
                                target = user_id
                            else:
                                print(f"User '{target}' not found. Use full user ID (e.g., user@192.168.1.4)")
                                continue
                        game_id = f"game_{int(time.time())}"
                        self.send_tictactoe_invite(target, game_id)
                        print(f"Tic Tac Toe invite sent to {target} (game_id: {game_id})")
                    elif subcmd == "accept" and len(cmd) > 2:
                        game_id = cmd[2]
                        if game_id in self.tictactoe_games:
                            game = self.tictactoe_games[game_id]
                            if game['status'] == 'active':
                                print(f"Game {game_id} accepted! You can now make moves.")
                                print(f"Use 'ttt board {game_id}' to see the board.")
                                print(f"Use 'ttt move {game_id} <position>' to make a move (0-8).")
                            else:
                                print(f"Game {game_id} is not active (status: {game['status']})")
                        else:
                            print(f"Game {game_id} not found")
                    elif subcmd == "move" and len(cmd) > 3:
                        game_id = cmd[2]
                        try:
                            position = int(cmd[3])
                            if 0 <= position <= 8:
                                self.send_tictactoe_move(game_id, position)
                                print(f"Move sent: position {position}")
                            else:
                                print("Position must be 0-8")
                        except ValueError:
                            print("Position must be a number 0-8")
                    elif subcmd == "board" and len(cmd) > 2:
                        game_id = cmd[2]
                        if game_id in self.tictactoe_games:
                            game = self.tictactoe_games[game_id]
                            board = game['board']
                            print(f"\n=== Tic Tac Toe Board ({game_id}) ===")
                            for i in range(0, 9, 3):
                                print(f" {board[i]} | {board[i+1]} | {board[i+2]} ")
                                if i < 6:
                                    print("---+---+---")
                            print(f"Turn: {game['turn']}")
                            print(f"Status: {game['status']}")
                        else:
                            print(f"Game {game_id} not found")
                    elif subcmd == "list":
                        if self.tictactoe_games:
                            print("\n=== Your Tic Tac Toe Games ===")
                            for game_id, game_info in self.tictactoe_games.items():
                                print(f"{game_id}: {game_info['status']} (turn: {game_info['turn']})")
                        else:
                            print("No active games")
                    else:
                        print("Usage: ttt <invite|move|board|list> [args...]")
                        print("Examples:")
                        print("  ttt invite user@192.168.1.4")
                        print("  ttt move game_1234567890 4")
                        print("  ttt board game_1234567890")
                        print("  ttt list")

                else:
                    print("Unknown command. Type 'help' for usage information or try:")
                    print("  peers, follow, unfollow, post, message, like, unlike, revoke, verbose")
                    print("  sendfile, group, ttt, exit")
            
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
    client.send_initial_discovery()
    client.run_cli()