import time
import secrets
import utils
import parser

class SocialHandler:
    def __init__(self, client):
        self.client = client
        self.posts = {}  # timestamp -> {'content': ..., 'author': ..., 'timestamp': ...}

    def send_follow_action(self, target_user_id: str, action: str):
        """Send a FOLLOW or UNFOLLOW message to the target user."""
        now = int(time.time())
        ttl_seconds = 3600
        token = f"{self.client.user_id}|{now + ttl_seconds}|follow"
        message_id = secrets.token_hex(8)
        
        msg = parser.format_message({
            'TYPE': action,
            'FROM': self.client.user_id,
            'TO': target_user_id,
            'MESSAGE_ID': message_id,
            'TIMESTAMP': now,
            'TOKEN': token,
        })
        
        peer_info = self.client.peer_manager.peers.get(target_user_id)
        if peer_info and peer_info.get('ip_address'):
            dest_ip = peer_info['ip_address']
            self.client.network.send_message(msg, dest_ip=dest_ip)
            utils.log(f"Sent {action} to {target_user_id} via {dest_ip}", level="INFO")
            print(f"{action} sent to {target_user_id}")
        else:
            utils.log(f"Cannot send {action} — no known IP for {target_user_id}", level="WARN")
            print(f"Cannot send {action} — {target_user_id} not found")

    def handle_follow(self, parsed, sender_ip):
        """Handle FOLLOW messages"""
        from_user = parsed.get('FROM')
        to_user = parsed.get('TO')
        token = parsed.get('TOKEN')
        
        if to_user != self.client.user_id:
            return
            
        if not self.client._validate_token_or_log(token, expected_scope='follow', expected_user_id=from_user, sender_ip=sender_ip, message_type='FOLLOW'):
            return
            
        self.client.peer_manager.add_follower(self.client.user_id, from_user)
        display_name = self.client.peer_manager.get_display_name(from_user)
        utils.log_protocol_event("FOLLOW_RECEIVED", f"from={display_name}", sender_ip, "FOLLOW")
        print(f"\n[FOLLOW] {display_name} is now following you!")

    def handle_unfollow(self, parsed, sender_ip):
        """Handle UNFOLLOW messages"""
        from_user = parsed.get('FROM')
        to_user = parsed.get('TO')
        token = parsed.get('TOKEN')
        
        if to_user != self.client.user_id:
            return
            
        if not self.client._validate_token_or_log(token, expected_scope='follow', expected_user_id=from_user, sender_ip=sender_ip, message_type='UNFOLLOW'):
            return
            
        self.client.peer_manager.remove_follower(self.client.user_id, from_user)
        display_name = self.client.peer_manager.get_display_name(from_user)
        utils.log_protocol_event("UNFOLLOW_RECEIVED", f"from={display_name}", sender_ip, "UNFOLLOW")
        print(f"\n[UNFOLLOW] {display_name} unfollowed you.")

    def send_post(self, content: str, ttl: int = 3600):
        """Send a POST message to all followers"""
        now = int(time.time())
        token = f"{self.client.user_id}|{now + ttl}|broadcast"
        message_id = secrets.token_hex(8)
        
        msg = parser.format_message({
            'TYPE': 'POST',
            'USER_ID': self.client.user_id,
            'CONTENT': content,
            'TTL': ttl,
            'TIMESTAMP': now,
            'MESSAGE_ID': message_id,
            'TOKEN': token
        })
        
        # Store post locally
        self.posts[now] = {
            'content': content,
            'author': self.client.user_id,
            'timestamp': now
        }
        
        # Broadcast to all followers
        followers = self.client.peer_manager.get_followers(self.client.user_id)
        for follower_id in followers:
            peer_info = self.client.peer_manager.peers.get(follower_id)
            if peer_info and peer_info.get('ip_address'):
                dest_ip = peer_info['ip_address']
                self.client.network.send_message(msg, dest_ip=dest_ip)
                utils.log(f"Sent POST to {follower_id} via {dest_ip}", level="INFO")
        
        # Also broadcast to network for discovery
        self.client.network.send_message(msg)
        utils.log(f"Posted: {content[:50]}...", level="INFO")
        print(f"Post sent: {content}")

    def handle_post(self, parsed, sender_ip):
        """Handle POST messages"""
        from_user = parsed.get('USER_ID') or parsed.get('FROM')  # Support both RFC and legacy format
        content = parsed.get('CONTENT')
        timestamp = parsed.get('TIMESTAMP')
        token = parsed.get('TOKEN')
        
        if not self.client._validate_token_or_log(token, expected_scope='broadcast', expected_user_id=from_user, sender_ip=sender_ip, message_type='POST'):
            return
            
        # Store post locally
        if timestamp:
            self.posts[int(timestamp)] = {
                'content': content,
                'author': from_user,
                'timestamp': int(timestamp)
            }
        
        display_name = self.client.peer_manager.get_display_name(from_user)
        utils.log_protocol_event("POST_RECEIVED", f"from={display_name} content={content[:30]}...", sender_ip, "POST")
        print(f"\n[POST] {display_name}: {content}")

    def send_dm(self, target_user_id: str, content: str):
        """Send a private DM to the target user with chat-scoped token."""
        now = int(time.time())
        ttl_seconds = 3600
        token = f"{self.client.user_id}|{now + ttl_seconds}|chat"
        message_id = secrets.token_hex(8)
        
        msg = parser.format_message({
            'TYPE': 'DM',
            'FROM': self.client.user_id,
            'TO': target_user_id,
            'CONTENT': content,
            'MESSAGE_ID': message_id,
            'TIMESTAMP': now,
            'TOKEN': token,
        })
        
        peer_info = self.client.peer_manager.peers.get(target_user_id)
        if peer_info and peer_info.get('ip_address'):
            dest_ip = peer_info['ip_address']
            self.client.network.send_message(msg, dest_ip=dest_ip)
            utils.log(f"Sent DM to {target_user_id} via {dest_ip}", level="INFO")
            print(f"DM sent to {target_user_id}: {content}")
        else:
            utils.log(f"Cannot send DM — no known IP for {target_user_id}", level="WARN")
            print(f"Cannot send DM — {target_user_id} not found")

    def handle_dm(self, parsed: dict, sender_ip: str):
        """Handle DM messages"""
        from_user = parsed.get('FROM')
        to_user = parsed.get('TO')
        content = parsed.get('CONTENT')
        message_id = parsed.get('MESSAGE_ID')
        token = parsed.get('TOKEN')
        
        if to_user != self.client.user_id:
            return
            
        if not self.client._validate_token_or_log(token, expected_scope='chat', expected_user_id=from_user, sender_ip=sender_ip, message_type='DM'):
            return
            
        display_name = self.client.peer_manager.get_display_name(from_user)
        utils.log_protocol_event("DM_RECEIVED", f"from={display_name} content={content[:30]}...", sender_ip, "DM")
        print(f"\n[DM] {display_name}: {content}")

        # Send ACK to confirm receipt
        if message_id:
            self.send_ack(message_id, sender_ip)

    def send_ack(self, message_id: str, dest_ip: str):
        """Send an ACK message"""
        now = int(time.time())
        ttl_seconds = 3600
        token = f"{self.client.user_id}|{now + ttl_seconds}|chat"
        
        msg = parser.format_message({
            'TYPE': 'ACK',
            'FROM': self.client.user_id,
            'MESSAGE_ID': message_id,
            'TIMESTAMP': now,
            'TOKEN': token,
        })
        
        self.client.network.send_message(msg, dest_ip=dest_ip)
        utils.log(f"Sent ACK for {message_id} to {dest_ip}", level="INFO")

    def handle_ack(self, parsed, sender_ip):
        """Handle ACK messages"""
        from_user = parsed.get('FROM')
        message_id = parsed.get('MESSAGE_ID')
        token = parsed.get('TOKEN')
        
        if not self.client._validate_token_or_log(token, expected_scope='chat', expected_user_id=from_user, sender_ip=sender_ip, message_type='ACK'):
            return
            
        utils.log(f"Received ACK for {message_id} from {from_user}", level="INFO")

    def send_like(self, target_user_id: str, post_timestamp: int, action: str = "LIKE"):
        """Sends a LIKE or UNLIKE message to the author of a post"""
        now = int(time.time())
        ttl_seconds = 3600
        token = f"{self.client.user_id}|{now + ttl_seconds}|broadcast"
        message_id = secrets.token_hex(8)
        
        msg = parser.format_message({
            'TYPE': action,
            'FROM': self.client.user_id,
            'TO': target_user_id,
            'POST_TIMESTAMP': post_timestamp,
            'MESSAGE_ID': message_id,
            'TIMESTAMP': now,
            'TOKEN': token,
        })
        
        peer_info = self.client.peer_manager.peers.get(target_user_id)
        if peer_info and peer_info.get('ip_address'):
            dest_ip = peer_info['ip_address']
            self.client.network.send_message(msg, dest_ip=dest_ip)
            utils.log(f"Sent {action} to {target_user_id} via {dest_ip}", level="INFO")
            print(f"{action} sent to {target_user_id}")
        else:
            utils.log(f"Cannot send {action} — no known IP for {target_user_id}", level="WARN")
            print(f"Cannot send {action} — {target_user_id} not found")

    def handle_like(self, parsed, sender_ip):
        """Handle LIKE/UNLIKE messages"""
        from_user = parsed.get('FROM')
        to_user = parsed.get('TO')
        post_timestamp = parsed.get('POST_TIMESTAMP')
        token = parsed.get('TOKEN')
        
        if to_user != self.client.user_id:
            return
            
        if not self.client._validate_token_or_log(token, expected_scope='broadcast', expected_user_id=from_user, sender_ip=sender_ip, message_type='LIKE'):
            return
            
        display_name = self.client.peer_manager.get_display_name(from_user)
        utils.log_protocol_event("LIKE_RECEIVED", f"from={display_name} post={post_timestamp}", sender_ip, "LIKE")
        print(f"\n[LIKE] {display_name} liked your post from {post_timestamp}")

    def send_revoke(self, token: str):
        """Send a REVOKE message to invalidate a token"""
        now = int(time.time())
        ttl_seconds = 3600
        revoke_token = f"{self.client.user_id}|{now + ttl_seconds}|broadcast"
        
        msg = parser.format_message({
            'TYPE': 'REVOKE',
            'FROM': self.client.user_id,
            'TOKEN': token,
            'TIMESTAMP': now,
            'REVOKE_TOKEN': revoke_token,
        })
        
        self.client.network.send_message(msg)
        utils.log(f"Sent REVOKE for token: {token[:20]}...", level="INFO")
        print(f"Token revoked: {token[:20]}...")

    def handle_revoke(self, parsed: dict, sender_ip: str):
        """Handle REVOKE messages"""
        from_user = parsed.get('FROM')
        token = parsed.get('TOKEN')
        revoke_token = parsed.get('REVOKE_TOKEN')
        
        if not self.client._validate_token_or_log(revoke_token, expected_scope='broadcast', expected_user_id=from_user, sender_ip=sender_ip, message_type='REVOKE'):
            return
            
        utils.revoke_token(token)
        display_name = self.client.peer_manager.get_display_name(from_user)
        utils.log_protocol_event("REVOKE_RECEIVED", f"from={display_name} token={token[:20]}...", sender_ip, "REVOKE")
        print(f"\n[REVOKE] {display_name} revoked a token")
