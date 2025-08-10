import time
import secrets
import utils
import parser

class GroupHandler:
    def __init__(self, client):
        self.client = client
        self.groups = {}  # group_id -> {'name': ..., 'members': set(), 'meta': {...}}

    def send_group_create(self, group_id, group_name, members):
        """Send a GROUP_CREATE message to all members."""
        now = int(time.time())
        ttl_seconds = 3600
        token = f"{self.client.user_id}|{now + ttl_seconds}|group"
        message_id = secrets.token_hex(8)
        
        msg = parser.format_message({
            'TYPE': 'GROUP_CREATE',
            'FROM': self.client.user_id,
            'GROUP_ID': group_id,
            'GROUP_NAME': group_name,
            'MEMBERS': ','.join(members),
            'MESSAGE_ID': message_id,
            'TIMESTAMP': now,
            'TOKEN': token,
        })
        
        self.groups[group_id] = {
            'name': group_name,
            'members': list(set(members)),  # Ensure unique members
            'creator': self.client.user_id,
            'created': now,
            'messages': []
        }
        
        for member_id in members:
            peer_info = self.client.peer_manager.peers.get(member_id)
            if peer_info and peer_info.get('ip_address'):
                dest_ip = peer_info['ip_address']
                self.client.network.send_message(msg, dest_ip=dest_ip)
                utils.log(f"Sent GROUP_CREATE to {member_id} via {dest_ip}", level="INFO")
        
        print(f"Group '{group_name}' created with ID: {group_id}")

    def handle_group_create(self, parsed, sender_ip):
        """Handle GROUP_CREATE messages."""
        group_id = parsed.get('GROUP_ID')
        group_name = parsed.get('GROUP_NAME')
        members_str = parsed.get('MEMBERS')
        from_user = parsed.get('FROM')
        token = parsed.get('TOKEN')
        
        if not self.client._validate_token_or_log(token, expected_scope='group', expected_user_id=from_user, sender_ip=sender_ip, message_type='GROUP_CREATE'):
            return
            
        members = members_str.split(',') if members_str else []
        
        self.groups[group_id] = {
            'name': group_name,
            'members': list(set(members)),
            'creator': from_user,
            'created': int(time.time()),
            'messages': []
        }
        
        display_name = self.client.peer_manager.get_display_name(from_user)
        utils.log_protocol_event("GROUP_CREATE_RECEIVED", f"group={group_name} from={display_name}", sender_ip, "GROUP_CREATE")
        print(f"\n👥 [GROUP] {display_name} created group '{group_name}' (ID: {group_id})")

    def send_group_update(self, group_id, add_members=None, remove_members=None):
        """Send a GROUP_UPDATE message to all group members."""
        if group_id not in self.groups:
            print(f"Group {group_id} not found.")
            return

        group_info = self.groups[group_id]
        # Check if the current user is the creator of the group
        if group_info.get('creator') != self.client.user_id:
            print("Only the group creator can update the group.")
            return

        now = int(time.time())
        ttl_seconds = 3600
        token = f"{self.client.user_id}|{now + ttl_seconds}|group"
        message_id = secrets.token_hex(8)

        msg_data = {
            'TYPE': 'GROUP_UPDATE',
            'FROM': self.client.user_id,
            'GROUP_ID': group_id,
            'MESSAGE_ID': message_id,
            'TIMESTAMP': now,
            'TOKEN': token,
        }
        if add_members:
            msg_data['ADD'] = ','.join(add_members)
        if remove_members:
            msg_data['REMOVE'] = ','.join(remove_members)

        msg = parser.format_message(msg_data)

        for member_id in group_info['members']:
            peer_info = self.client.peer_manager.peers.get(member_id)
            if peer_info and peer_info.get('ip_address'):
                dest_ip = peer_info['ip_address']
                self.client.network.send_message(msg, dest_ip=dest_ip)
                utils.log(f"Sent GROUP_UPDATE to {member_id} via {dest_ip}", level="INFO")

        print(f"Group {group_id} update sent.")

    def handle_group_update(self, parsed, sender_ip):
        """Handle GROUP_UPDATE messages."""
        group_id = parsed.get('GROUP_ID')
        from_user = parsed.get('FROM')
        token = parsed.get('TOKEN')
        add_members_str = parsed.get('ADD')
        remove_members_str = parsed.get('REMOVE')

        if group_id not in self.groups:
            return

        group_info = self.groups[group_id]
        # For now, we trust the creator of the group to send valid updates.
        # A more robust implementation would be to verify the sender is the creator.
        if from_user != group_info.get('creator'):
            utils.log(f"Received GROUP_UPDATE from non-creator {from_user}", level="WARNING")
            return

        if not self.client._validate_token_or_log(token, expected_scope='group', expected_user_id=from_user, sender_ip=sender_ip, message_type='GROUP_UPDATE'):
            return

        if add_members_str:
            add_members = add_members_str.split(',')
            group_info['members'].extend(add_members)
            # Remove duplicates
            group_info['members'] = list(set(group_info['members']))
            print(f"Users {add_members} added to group {group_id}")

        if remove_members_str:
            remove_members = remove_members_str.split(',')
            group_info['members'] = [m for m in group_info['members'] if m not in remove_members]
            print(f"Users {remove_members} removed from group {group_id}")

        utils.log(f"Group {group_id} updated.", level="INFO")

    def send_group_message(self, group_id, content):
        """Send a GROUP_MESSAGE to all members of a group."""
        if group_id not in self.groups:
            print(f"Group {group_id} not found.")
            return

        group_info = self.groups[group_id]
        now = int(time.time())
        ttl_seconds = 3600
        token = f"{self.client.user_id}|{now + ttl_seconds}|group"
        message_id = secrets.token_hex(8)

        msg = parser.format_message({
            'TYPE': 'GROUP_MESSAGE',
            'FROM': self.client.user_id,
            'GROUP_ID': group_id,
            'CONTENT': content,
            'MESSAGE_ID': message_id,
            'TIMESTAMP': now,
            'TOKEN': token,
        })

        # Store message locally
        group_info['messages'].append({
            'from': self.client.user_id,
            'content': content,
            'timestamp': now
        })

        for member_id in group_info['members']:
            peer_info = self.client.peer_manager.peers.get(member_id)
            if peer_info and peer_info.get('ip_address'):
                dest_ip = peer_info['ip_address']
                self.client.network.send_message(msg, dest_ip=dest_ip)
                utils.log(f"Sent GROUP_MESSAGE to {member_id} via {dest_ip}", level="INFO")

        print(f"Group message sent to {group_id}")

    def handle_group_message(self, parsed, sender_ip):
        """Handle GROUP_MESSAGE messages."""
        group_id = parsed.get('GROUP_ID')
        from_user = parsed.get('FROM')
        content = parsed.get('CONTENT')
        timestamp = parsed.get('TIMESTAMP')
        token = parsed.get('TOKEN')

        if group_id not in self.groups:
            utils.log(f"Received GROUP_MESSAGE for unknown group {group_id}", level="WARN")
            return

        group_info = self.groups[group_id]

        # Check if sender is a member of the group
        if from_user not in group_info['members']:
            utils.log(f"Received GROUP_MESSAGE from non-member {from_user} for group {group_id}", level="WARN")
            return

        if not self.client._validate_token_or_log(token, expected_scope='group', expected_user_id=from_user, sender_ip=sender_ip, message_type='GROUP_MESSAGE'):
            return

        group_info['messages'].append({
            'from': from_user,
            'content': content,
            'timestamp': int(timestamp)
        })

        display_name = self.client.peer_manager.get_display_name(from_user)
        utils.log_protocol_event("GROUP_MESSAGE_RECEIVED", f"group={group_id} from={display_name} content={content[:30]}...", sender_ip, "GROUP_MESSAGE")
        print(f"\n👥 [GROUP:{group_info['name']}] {display_name}: {content}")
