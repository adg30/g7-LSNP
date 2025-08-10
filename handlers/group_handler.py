import time
import secrets
import utils
import parser

class GroupHandler:
    def __init__(self, client):
        self.client = client
        self.groups = {}  # group_id -> {'name': ..., 'members': set(), 'meta': {...}}

    def send_group_create(self, group_id, group_name, members):
        now = int(time.time())
        ttl_seconds = 3600
        token = f"{self.client.user_id}|{now + ttl_seconds}|group"
        msg = parser.format_message({
            'TYPE': 'GROUP_CREATE',
            'GROUP_ID': group_id,
            'GROUP_NAME': group_name,
            'MEMBERS': ','.join(members),
            'FROM': self.client.user_id,
            'TIMESTAMP': now,
            'TOKEN': token,
        })
        for member in members:
            peer_info = self.client.peer_manager.peers.get(member)
            if peer_info and peer_info.get('ip_address'):
                dest_ip = peer_info['ip_address']
                self.client.network.send_message(msg, dest_ip=dest_ip)
                utils.log(f"Sent GROUP_CREATE for {group_id} to {member} via {dest_ip}", level="INFO")

    def handle_group_create(self, parsed, sender_ip):
        group_id = parsed.get('GROUP_ID')
        group_name = parsed.get('GROUP_NAME')
        members = set(parsed.get('MEMBERS', '').split(','))
        token = parsed.get('TOKEN')
        from_user = parsed.get('FROM')
        if not self.client._validate_token_or_log(token, expected_scope='group', expected_user_id=from_user, sender_ip=sender_ip, message_type='GROUP_CREATE'):
            return
        self.groups[group_id] = {'name': group_name, 'members': members, 'meta': {}}
        utils.log_protocol_event("GROUP_CREATED", f"group={group_name} members={len(members)}", sender_ip, "GROUP_CREATE")
        utils.log(f"Joined group {group_name} ({group_id}) with members: {members}", level="INFO")
        print(f"\n[GROUP] Joined group '{group_name}' ({group_id})")

    def send_group_update(self, group_id, members):
        now = int(time.time())
        ttl_seconds = 3600
        token = f"{self.client.user_id}|{now + ttl_seconds}|group"
        msg = parser.format_message({
            'TYPE': 'GROUP_UPDATE',
            'GROUP_ID': group_id,
            'MEMBERS': ','.join(members),
            'FROM': self.client.user_id,
            'TIMESTAMP': now,
            'TOKEN': token,
        })
        for member in members:
            peer_info = self.client.peer_manager.peers.get(member)
            if peer_info and peer_info.get('ip_address'):
                dest_ip = peer_info['ip_address']
                self.client.network.send_message(msg, dest_ip=dest_ip)
                utils.log(f"Sent GROUP_UPDATE for {group_id} to {member} via {dest_ip}", level="INFO")

    def handle_group_update(self, parsed, sender_ip):
        group_id = parsed.get('GROUP_ID')
        members = set(parsed.get('MEMBERS', '').split(','))
        token = parsed.get('TOKEN')
        from_user = parsed.get('FROM')
        if not self.client._validate_token_or_log(token, expected_scope='group', expected_user_id=from_user, sender_ip=sender_ip, message_type='GROUP_UPDATE'):
            return
        if group_id in self.groups:
            self.groups[group_id]['members'] = members
            utils.log(f"Updated group {group_id} members: {members}", level="INFO")
            print(f"\n[GROUP] Updated group '{group_id}' members: {members}")

    def send_group_message(self, group_id, content):
        now = int(time.time())
        ttl_seconds = 3600
        token = f"{self.client.user_id}|{now + ttl_seconds}|group"
        msg = parser.format_message({
            'TYPE': 'GROUP_MESSAGE',
            'GROUP_ID': group_id,
            'FROM': self.client.user_id,
            'CONTENT': content,
            'TIMESTAMP': now,
            'TOKEN': token,
        })
        
        # Send to all group members
        if group_id in self.groups:
            for member in self.groups[group_id]['members']:
                if member == self.client.user_id:
                    continue
                peer_info = self.client.peer_manager.peers.get(member)
                if peer_info and peer_info.get('ip_address'):
                    dest_ip = peer_info['ip_address']
                    self.client.network.send_message(msg, dest_ip=dest_ip)
                    utils.log(f"Sent GROUP_MESSAGE to {member} via {dest_ip}", level="INFO")
            print(f"Group message sent to {group_id}: {content}")
        else:
            print(f"Group {group_id} not found")

    def handle_group_message(self, parsed, sender_ip):
        group_id = parsed.get('GROUP_ID')
        from_user = parsed.get('FROM')
        content = parsed.get('CONTENT')
        token = parsed.get('TOKEN')
        
        if not self.client._validate_token_or_log(token, expected_scope='group', expected_user_id=from_user, sender_ip=sender_ip, message_type='GROUP_MESSAGE'):
            return
            
        if group_id in self.groups:
            display_name = self.client.peer_manager.get_display_name(from_user)
            group_name = self.groups[group_id]['name']
            utils.log_protocol_event("GROUP_MESSAGE_RECEIVED", f"group={group_name} from={display_name} content={content[:30]}...", sender_ip, "GROUP_MESSAGE")
            print(f"\n[GROUP:{group_name}] {display_name}: {content}")
        else:
            utils.log(f"Received group message for unknown group {group_id}", level="WARN")
