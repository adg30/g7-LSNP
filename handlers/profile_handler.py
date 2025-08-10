import time
import os
import base64
import mimetypes
import utils
import parser

class ProfileHandler:
    def __init__(self, client):
        self.client = client
        # Avatar attributes (initially None)
        self.avatar_type = None
        self.avatar_encoding = None
        self.avatar_data = None

    def handle_profile_message(self, parsed, sender_ip):
        """Handle PROFILE messages, including AVATAR fields if present"""
        self.client.peer_manager.add_peer(
            user_id=parsed['USER_ID'],
            display_name=parsed.get('DISPLAY_NAME'),
            status=parsed.get('STATUS'),
            ip_address=sender_ip,
            avatar_type=parsed.get('AVATAR_TYPE'),
            avatar_encoding=parsed.get('AVATAR_ENCODING'),
            avatar_data=parsed.get('AVATAR_DATA'),
        )

    def set_avatar_from_file(self, image_path):
        """Set avatar from an image file, converting to base64"""
        try:
            # Check if file exists
            if not os.path.exists(image_path):
                return False, f"File {image_path} not found"
            
            # Get file size (should be under 20KB per RFC)
            file_size = os.path.getsize(image_path)
            if file_size > 20 * 1024:  # 20KB limit
                return False, f"File too large ({file_size} bytes). Must be under 20KB"
            
            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(image_path)
            if not mime_type or not mime_type.startswith('image/'):
                return False, f"File {image_path} is not a recognized image format"
            
            # Read and encode file
            with open(image_path, 'rb') as f:
                image_data = f.read()
                base64_data = base64.b64encode(image_data).decode('utf-8')
            
            # Set avatar attributes
            self.avatar_type = mime_type
            self.avatar_encoding = 'base64'
            self.avatar_data = base64_data
            
            utils.log(f"Avatar set from {image_path} ({mime_type}, {file_size} bytes)", level="INFO")
            return True, f"Avatar set successfully from {image_path}"
            
        except Exception as e:
            return False, f"Error setting avatar: {e}"

    def clear_avatar(self):
        """Remove current avatar"""
        self.avatar_type = None
        self.avatar_encoding = None
        self.avatar_data = None
        utils.log("Avatar cleared", level="INFO")
        return True, "Avatar cleared successfully"
