import time
import utils
import os
import base64

class PeerManager:
    def __init__(self):
        self.peers = {}
        self.groups = {}
        self.followers = {}

    def add_peer(self, user_id, display_name=None, status=None, ip_address=None, avatar_type=None, avatar_encoding=None, avatar_data=None):
        current_time = time.time()
        
        if user_id not in self.peers:
            # for new peers
            self.peers[user_id] = {
                'display_name': display_name or user_id, # if display_name is None
                'status': status, 
                'ip_address': ip_address,
                'avatar_type': avatar_type,
                'avatar_encoding': avatar_encoding,
                'avatar_data': avatar_data,
                'last_seen': current_time
            }
            utils.log(f"Added new peer: {user_id}", level="INFO")
        else:
            # update existing peer
            peer = self.peers[user_id]
            if display_name:
                peer['display_name'] = display_name
            if status:
                peer['status'] = status
            if ip_address:
                peer['ip_address'] = ip_address
            if avatar_type:
                peer['avatar_type'] = avatar_type
            if avatar_encoding:
                peer['avatar_encoding'] = avatar_encoding
            if avatar_data:
                peer['avatar_data'] = avatar_data
            peer['last_seen'] = current_time
            utils.log(f"Updated peer: {user_id}", level="INFO")

    def save_avatar_to_file(self, user_id, avatar_data, avatar_type):
        """Save avatar data to a file"""
        try:
            # Create avatars directory if it doesn't exist
            if not os.path.exists('avatars'):
                os.makedirs('avatars')
            
            # Determine file extension from MIME type
            if avatar_type == 'image/png':
                ext = '.png'
            elif avatar_type == 'image/jpeg' or avatar_type == 'image/jpg':
                ext = '.jpg'
            elif avatar_type == 'image/gif':
                ext = '.gif'
            else:
                ext = '.img'  # fallback
            
            # Create filename from user_id
            safe_user_id = user_id.replace('@', '_').replace('.', '_')
            filename = f"avatars/{safe_user_id}{ext}"
            
            # Decode and save the image
            image_data = base64.b64decode(avatar_data)
            with open(filename, 'wb') as f:
                f.write(image_data)
            
            return filename
        except Exception as e:
            utils.log(f"Error saving avatar for {user_id}: {e}", level="ERROR")
            return None

    def display_all_peers(self):
        if not self.peers:
            print("No known peers.")
            return
        
        print("\n=== Known Peers ===")
        for user_id, peer in self.peers.items():
            print(f"User ID: {user_id}")
            print(f"-->Display Name: {peer['display_name']}")
            print(f"-->Status: {peer['status']}")
            print(f"-->IP Address: {peer['ip_address']}")
            if peer.get('avatar_type') and peer.get('avatar_data'):
                print(f"-->Avatar Type: {peer['avatar_type']}")
                # Save avatar to file and show the filename
                avatar_file = self.save_avatar_to_file(user_id, peer['avatar_data'], peer['avatar_type'])
                if avatar_file:
                    print(f"-->Avatar: Saved as {avatar_file}")
                else:
                    print(f"-->Avatar: Error saving image")
            if peer['last_seen']:
                time_diff = time.time() - peer['last_seen']
                print(f"-->Last Seen: {int(time_diff)} seconds ago")
            print("-" * 40)

    def add_follower(self, target_user, follower_user):
        if target_user not in self.followers:
            self.followers[target_user] = set()
        self.followers[target_user].add(follower_user)
        utils.log(f"{follower_user} is now following {target_user}", level="INFO")

    def remove_follower(self, target_user, follower_user):
        if target_user in self.followers:
            self.followers[target_user].discard(follower_user)
            utils.log(f"{follower_user} unfollowed {target_user}", level="INFO")

    def get_followers(self, user_id):
        return list(self.followers.get(user_id, set()))

    def display_followers(self, user_id):
        followers = self.get_followers(user_id)
        if not followers:
            print(f"{user_id} has no followers.")
            return

        print(f"\n=== Followers of {user_id} ===")
        for follower_id in followers:
            display_name = self.peers.get(follower_id, {}).get("display_name", follower_id)
            print(f"- {display_name} (@{follower_id})")

    def get_display_name(self, user_id):
        peer = self.peers.get(user_id)
        if peer and peer.get("display_name"):
            return peer["display_name"]
        return user_id