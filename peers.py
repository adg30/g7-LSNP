import time
import utils

class PeerManager:
    def __init__(self):
        self.peers = {}
        self.groups = {}
        self.followers = {}
        self.disconnect_threshold = 600  # 10 minutes - consider peer offline if not seen for this long

    def add_peer(self, user_id, display_name=None, status=None, ip_address=None, avatar_url=None, avatar_hash=None):
        current_time = time.time()
        
        # Check if this is a reconnection of a previously offline peer
        was_offline = False
        if user_id in self.peers:
            old_peer = self.peers[user_id]
            if current_time - old_peer.get('last_seen', 0) > self.disconnect_threshold:
                was_offline = True
                utils.log(f"Peer {user_id} reconnected after being offline", level="INFO")
        
        if user_id not in self.peers:
            # for new peers
            self.peers[user_id] = {
                'display_name': display_name or user_id, # if display_name is None
                'status': status, 
                'ip_address': ip_address,
                'avatar_url': avatar_url,
                'avatar_hash': avatar_hash,
                'last_seen': current_time,
                'online': True
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
            peer['online'] = True
            utils.log(f"Updated peer: {user_id}", level="INFO")
        
        # Notify user of reconnection
        if was_offline:
            display_name = self.peers[user_id].get('display_name', user_id)
            print(f"\n🟢 {display_name} is back online!")

    def check_disconnected_peers(self):
        """Check for peers that have gone offline and notify user"""
        current_time = time.time()
        for user_id, peer in list(self.peers.items()):
            if peer.get('online', True) and (current_time - peer.get('last_seen', 0)) > self.disconnect_threshold:
                peer['online'] = False
                display_name = peer.get('display_name', user_id)
                print(f"\n🔴 {display_name} went offline")
                utils.log(f"Peer {user_id} marked as offline", level="INFO")

    def get_online_peers(self):
        """Get list of currently online peers"""
        current_time = time.time()
        online_peers = {}
        for user_id, peer in self.peers.items():
            if (current_time - peer.get('last_seen', 0)) <= self.disconnect_threshold:
                online_peers[user_id] = peer
        return online_peers

    def display_all_peers(self):
        if not self.peers:
            print("No known peers.")
            return
        
        print("\n=== Known Peers ===")
        for user_id, peer in self.peers.items():
            status_icon = "🟢" if peer.get('online', True) else "🔴"
            print(f"{status_icon} User ID: {user_id}")
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