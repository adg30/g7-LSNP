import time
import utils

class PeerManager:
    def __init__(self):
        self.peers = {}
        self.groups = {}
        self.followers = {}

    def add_peer(self, user_id, display_name=None, status=None, ip_address=None, avatar_url=None, avatar_hash=None):
        current_time = time.time()
        
        if user_id not in self.peers:
            # for new peers
            self.peers[user_id] = {
                'display_name': display_name or user_id, # if display_name is None
                'status': status, 
                'ip_address': ip_address,
                'avatar_url': avatar_url,
                'avatar_hash': avatar_hash,
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
            if avatar_url:
                peer['avatar_url'] = avatar_url
            if avatar_hash:
                peer['avatar_hash'] = avatar_hash
            peer['last_seen'] = current_time
            utils.log(f"Updated peer: {user_id}", level="INFO")

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
            if peer.get('avatar_url'):
                print(f"-->Avatar URL: {peer['avatar_url']}")
            if peer.get('avatar_hash'):
                print(f"-->Avatar Hash: {peer['avatar_hash']}")
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