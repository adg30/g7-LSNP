import time
import utils

class PeerManager:
    def __init__(self):
        self.peers = {}           
        self.posts = {}           
        self.direct_messages = [] 
        self.groups = {}     

    def add_peer(self, user_id, display_name=None, status=None, ip_address=None):
        current_time = time.time()
        
        if user_id not in self.peers:
            # for new peers
            self.peers[user_id] = {
                'display_name': display_name or user_id, # if display_name is None
                'status': status, 
                'ip_address': ip_address,
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
            peer['last_seen'] = current_time
            utils.log(f"Updated peer: {user_id}", level="INFO")

    def add_post(self, user_id, content, timestamp, ttl=3600):
        self.posts[timestamp] = {
            'user_id': user_id,
            'content': content,
            'timestamp': timestamp,
            'ttl': ttl,
            'likes': []
        }
        utils.log(f"Added post from {user_id}: {content[:50]}...", level="INFO")

    def add_direct_message(self, from_user, to_user, content, timestamp):
        dm = {
            'from': from_user,
            'to': to_user, 
            'content': content,
            'timestamp': timestamp
        }
        self.direct_messages.append(dm)
        utils.log(f"Added DM from {from_user} to {to_user}", level="INFO")

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
            if peer['last_seen']:
                time_diff = time.time() - peer['last_seen']
                print(f"-->Last Seen: {int(time_diff)} seconds ago")
            print("-" * 40)
        
    def get_dms_for_user(self, user_id): # getter for direct messages
        user_messages = []

        for dm in self.direct_messages:
            if dm['from'] == user_id or dm['to'] == user_id:
                user_messages.append(dm)
        return user_messages
    
    def display_dms_for_user(self, user_id):
        messages = self.get_dms_for_user(user_id)
        
        if not messages:
            print(f"No direct messages found for user: {user_id}")
            return
        
        print(f"\n=== Direct Messages for {user_id} ===")
        for dm in messages:
            if dm['from'] == user_id:
                print(f"TO {dm['to']}: {dm['content']}")
            else:
                print(f"FROM {dm['from']}: {dm['content']}")
            print(f"Time: {dm['timestamp']}")
            print("-" * 40)


    def get_posts_by_user(self, user_id): # getter for posts
            user_posts = []

            for timestamp, post in self.posts.items():
                if post['user_id'] == user_id:
                    user_posts.append(post)
            return user_posts

    def display_posts_by_user(self, user_id):
        posts = self.get_posts_by_user(user_id)
        if not posts:
            print(f"No posts found for user: {user_id}")
            return
        
        print(f"\n=== Posts by {user_id} ===")
        for post in posts:
            print(f"Content: {post['content']}")
            print(f"Time: {post['timestamp']}")
            print(f"Likes: {len(post['likes'])}")
            print("-" * 40)
  