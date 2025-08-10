import time
import secrets
import utils
import parser
import os
import hashlib
import threading
from threading import Lock, Event
from collections import defaultdict

import mimetypes

class FileHandler:
    def __init__(self, client):
        self.client = client
        self.incoming_files = {}  # file_id -> {'filename': ..., 'chunks': {}, 'total': N, 'hash': ..., 'from': ...}
        self.outgoing_files = {}  # file_id -> {'filename': ..., 'filesize': ..., 'filehash': ...}
        self.chunk_requests = {}  # file_id -> {'missing': set(), 'last_request': timestamp}
        self.transfer_locks = defaultdict(Lock)  # file_id -> Lock for thread safety
        self.downloads_dir = "downloads"
        self.chunk_size = 1024  # 1KB chunks
        self.max_retries = 3
        self.chunk_timeout = 30  # seconds
        self.flow_control_window = 10  # chunks to send before waiting for ack
        
        # Create downloads directory if it doesn't exist
        os.makedirs(self.downloads_dir, exist_ok=True)

    def _generate_file_id(self, filename):
        """Generate a unique file ID"""
        timestamp = int(time.time() * 1000)  # Use milliseconds for uniqueness
        random_part = secrets.token_hex(4)
        return f"{self.client.user_id}_{filename}_{timestamp}_{random_part}"

    def _calculate_file_hash(self, filepath):
        """Calculate SHA-256 hash of a file"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            utils.log(f"Error calculating hash for {filepath}: {e}", level="ERROR")
            return None

    def _verify_file_hash(self, filepath, expected_hash):
        """Verify file integrity using hash"""
        actual_hash = self._calculate_file_hash(filepath)
        return actual_hash == expected_hash

    def _get_safe_filename(self, filename):
        """Generate a safe filename in the downloads directory"""
        # Remove path components and dangerous characters
        safe_name = os.path.basename(filename).replace('..', '').replace('/', '_').replace('\\', '_')
        filepath = os.path.join(self.downloads_dir, safe_name)
        
        # Handle file name conflicts
        counter = 1
        base_path = filepath
        while os.path.exists(filepath):
            name, ext = os.path.splitext(base_path)
            filepath = f"{name}_{counter}{ext}"
            counter += 1
            
        return filepath

    def send_file_offer(self, target_user_id, filename, filesize=None, filehash=None):
        """Send file offer with proper file ID generation"""
        if not os.path.exists(filename):
            print(f"File not found: {filename}")
            return None
            
        # Calculate file info if not provided
        if filesize is None:
            filesize = os.path.getsize(filename)
        if filehash is None:
            filehash = self._calculate_file_hash(filename)
            if filehash is None:
                print(f"Failed to calculate hash for {filename}")
                return None

        # Generate consistent file ID
        file_id = self._generate_file_id(os.path.basename(filename))
        
        now = int(time.time())
        ttl_seconds = 3600
        token = f"{self.client.user_id}|{now + ttl_seconds}|file"
        message_id = secrets.token_hex(8)
        
        # Store file information for later chunk sending
        self.outgoing_files[file_id] = {
            'filename': filename,  # Store full path for reading
            'display_name': os.path.basename(filename),  # Store display name
            'filesize': int(filesize),
            'filehash': filehash,
            'target_user': target_user_id,
            'status': 'offered',
            'created': now
        }
        
        file_type, _ = mimetypes.guess_type(filename)
        if not file_type:
            file_type = "application/octet-stream"

        msg = parser.format_message({
            'TYPE': 'FILE_OFFER',
            'FROM': self.client.user_id,
            'TO': target_user_id,
            'FILEID': file_id,
            'FILENAME': os.path.basename(filename),
            'FILESIZE': filesize,
            'FILETYPE': file_type,
            'DESCRIPTION': f"File transfer for {os.path.basename(filename)}",
            'FILEHASH': filehash,
            'MESSAGE_ID': message_id,
            'TIMESTAMP': now,
            'TOKEN': token,
        })
        
        peer_info = self.client.peer_manager.peers.get(target_user_id)
        if peer_info and peer_info.get('ip_address'):
            dest_ip = peer_info['ip_address']
            self.client.network.send_message(msg, dest_ip=dest_ip)
            utils.log(f"Sent FILE_OFFER for {filename} (ID: {file_id}) to {target_user_id} via {dest_ip}", level="INFO")
            print(f"File offer sent: {os.path.basename(filename)} (ID: {file_id})")
            return file_id
        else:
            utils.log(f"Cannot send FILE_OFFER — no known IP for {target_user_id}", level="WARN")
            del self.outgoing_files[file_id]
            return None

    def handle_file_offer(self, parsed, sender_ip):
        """Handle incoming file offer"""
        from_user = parsed.get('FROM')
        to_user = parsed.get('TO')
        file_id = parsed.get('FILEID')
        filename = parsed.get('FILENAME')
        filesize = parsed.get('FILESIZE')
        filetype = parsed.get('FILETYPE')
        description = parsed.get('DESCRIPTION')
        filehash = parsed.get('FILEHASH', None) # Make filehash optional
        token = parsed.get('TOKEN')
        
        if to_user != self.client.user_id:
            return
        if not self.client._validate_token_or_log(token, expected_scope='file', expected_user_id=from_user, sender_ip=sender_ip, message_type='FILE_OFFER'):
            return
            
        display_name = self.client.peer_manager.get_display_name(from_user)
        utils.log_protocol_event("FILE_OFFER_RECEIVED", f"file={filename} size={filesize} from={display_name}", sender_ip, "FILE_OFFER")
        
        # Store file offer with consistent file_id
        self.incoming_files[file_id] = {
            'filename': filename,
            'filesize': int(filesize),
            'filetype': filetype,
            'description': description,
            'filehash': filehash,
            'from': from_user,
            'chunks': {},
            'total_chunks': (int(filesize) + self.chunk_size - 1) // self.chunk_size,
            'status': 'pending',
            'created': int(time.time())
        }
        
        print(f"\n📁 [FILE_OFFER] {display_name} wants to send you '{filename}'")
        print(f"   Size: {filesize} bytes ({int(filesize)//1024} KB)")
        print(f"   Type: {filetype}")
        print(f"   Description: {description}")
        print(f"   File ID: {file_id}")
        print(f"Commands:")
        print(f"  acceptfile {file_id} - Accept the file transfer")
        print(f"  rejectfile {file_id} - Decline the file transfer")

    def send_file_accept(self, file_id):
        """Accept a file transfer with proper flow"""
        if file_id not in self.incoming_files:
            print(f"❌ File {file_id} not found")
            return
            
        file_info = self.incoming_files[file_id]
        if file_info['status'] != 'pending':
            print(f"❌ File {file_id} is not in pending status")
            return
            
        from_user = file_info['from']
        file_info['status'] = 'accepted'
        
        print(f"✅ File transfer accepted: {file_info['filename']}")
        
        # Send file request to start transfer
        now = int(time.time())
        ttl_seconds = 3600
        token = f"{self.client.user_id}|{now + ttl_seconds}|file"
        msg = parser.format_message({
            'TYPE': 'FILE_REQUEST',
            'FROM': self.client.user_id,
            'TO': from_user,
            'FILE_ID': file_id,
            'TIMESTAMP': now,
            'TOKEN': token,
        })
        
        peer_info = self.client.peer_manager.peers.get(from_user)
        if peer_info and peer_info.get('ip_address'):
            dest_ip = peer_info['ip_address']
            self.client.network.send_message(msg, dest_ip=dest_ip)
            utils.log(f"Sent FILE_REQUEST for {file_id} to {from_user}", level="INFO")
            print(f"📥 Requesting file chunks...")
        else:
            print(f"❌ Cannot reach sender")
            file_info['status'] = 'failed'

    def send_file_reject(self, file_id):
        """Reject a file transfer"""
        if file_id not in self.incoming_files:
            print(f"❌ File {file_id} not found")
            return
            
        file_info = self.incoming_files[file_id]
        from_user = file_info['from']
        
        # Send rejection message
        now = int(time.time())
        ttl_seconds = 3600
        token = f"{self.client.user_id}|{now + ttl_seconds}|file"
        msg = parser.format_message({
            'TYPE': 'FILE_REJECT',
            'FROM': self.client.user_id,
            'TO': from_user,
            'FILE_ID': file_id,
            'TIMESTAMP': now,
            'TOKEN': token,
        })
        
        peer_info = self.client.peer_manager.peers.get(from_user)
        if peer_info and peer_info.get('ip_address'):
            dest_ip = peer_info['ip_address']
            self.client.network.send_message(msg, dest_ip=dest_ip)
            utils.log(f"Sent FILE_REJECT for {file_id} to {from_user}", level="INFO")
        
        del self.incoming_files[file_id]
        print(f"❌ File transfer rejected: {file_info['filename']}")

    def send_file_chunk(self, target_user_id, file_id, chunk_index, chunk_data, total_chunks):
        """Send a single file chunk"""
        now = int(time.time())
        ttl_seconds = 3600
        token = f"{self.client.user_id}|{now + ttl_seconds}|file"
        message_id = secrets.token_hex(8)
        msg = parser.format_message({
            'TYPE': 'FILE_CHUNK',
            'FROM': self.client.user_id,
            'TO': target_user_id,
            'FILEID': file_id,
            'CHUNK_INDEX': chunk_index,
            'TOTAL_CHUNKS': total_chunks,
            'CHUNK_SIZE': len(chunk_data),
            'MESSAGE_ID': message_id,
            'TIMESTAMP': now,
            'TOKEN': token,
            'DATA': utils.base64_encode(chunk_data),
        })
        
        peer_info = self.client.peer_manager.peers.get(target_user_id)
        if peer_info and peer_info.get('ip_address'):
            dest_ip = peer_info['ip_address']
            self.client.network.send_message(msg, dest_ip=dest_ip)
            utils.log(f"Sent FILE_CHUNK {chunk_index}/{total_chunks} for {file_id} to {target_user_id}", level="DEBUG")
        else:
            utils.log(f"Cannot send FILE_CHUNK — no known IP for {target_user_id}", level="WARN")
            raise Exception(f"No IP address for {target_user_id}")

    def handle_file_chunk(self, parsed, sender_ip):
        """Handle incoming file chunk with validation"""
        from_user = parsed.get('FROM')
        to_user = parsed.get('TO')
        file_id = parsed.get('FILE_ID') or parsed.get('FILEID')  # Support both
        chunk_index = parsed.get('CHUNK_INDEX')
        total_chunks = parsed.get('TOTAL_CHUNKS')
        chunk_size = parsed.get('CHUNK_SIZE')
        token = parsed.get('TOKEN')
        message_id = parsed.get('MESSAGE_ID')
        data = parsed.get('DATA')
        
        # Validation
        if to_user != self.client.user_id or file_id is None or data is None:
            return
        if not self.client._validate_token_or_log(token, expected_scope='file', expected_user_id=from_user, sender_ip=sender_ip, message_type='FILE_CHUNK'):
            return
            
        try:
            chunk_index = int(chunk_index)
            total_chunks = int(total_chunks)
            chunk_size = int(chunk_size)
        except (ValueError, TypeError):
            utils.log(f"Invalid chunk parameters from {from_user}", level="WARN")
            return
        
        # Decode chunk data
        try:
            chunk_data = utils.base64_decode(data)
            if len(chunk_data) != chunk_size:
                utils.log(f"Chunk size mismatch: expected {chunk_size}, got {len(chunk_data)}", level="WARN")
                return
        except Exception as e:
            utils.log(f"Failed to decode chunk data: {e}", level="WARN")
            return
        
        # Thread-safe chunk handling
        with self.transfer_locks[file_id]:
            if file_id not in self.incoming_files:
                utils.log(f"Received chunk for unknown file {file_id}", level="WARN")
                return
                
            file_info = self.incoming_files[file_id]
            if file_info['status'] != 'accepted':
                return
                
            # Update total chunks if not set
            if file_info.get('total_chunks', 0) == 0:
                file_info['total_chunks'] = total_chunks
            
            # Store chunk
            file_info['chunks'][chunk_index] = chunk_data
            utils.log(f"Received chunk {chunk_index}/{total_chunks} for {file_id}", level="DEBUG")

            # Send ACK for the received chunk
            if message_id:
                self.client.send_ack(message_id, sender_ip)
            
            # Update progress
            progress = len(file_info['chunks']) / total_chunks * 100
            if chunk_index % 10 == 0 or chunk_index == total_chunks - 1:  # Show progress every 10 chunks
                print(f"📥 Progress: {progress:.1f}% ({len(file_info['chunks'])}/{total_chunks} chunks)")
            
            # Check for completion
            self._check_file_completion_safe(file_id)

    def _check_file_completion_safe(self, file_id):
        file_info = self.incoming_files.get(file_id)
        if not file_info:
            print(f"[ERROR] No incoming file info for ID: {file_id}")
            return

        received_chunks = len(file_info['chunks'])
        expected_chunks = file_info['total_chunks']

        print(f"[DEBUG] Checking file completion for {file_id}: "
            f"{received_chunks}/{expected_chunks} chunks received.")

        if received_chunks == expected_chunks:
            print(f"[INFO] All chunks for {file_id} received. Starting reassembly...")
            self._reassemble_file(file_id)
        else:
            print(f"[WARN] File {file_id} not complete yet.")


    def _request_missing_chunks(self, file_id, missing_chunks):
        """Request specific missing chunks"""
        if file_id not in self.incoming_files:
            return
            
        file_info = self.incoming_files[file_id]
        from_user = file_info['from']
        
        # Throttle chunk requests
        now = time.time()
        if file_id in self.chunk_requests:
            if now - self.chunk_requests[file_id]['last_request'] < 5:  # Wait 5 seconds between requests
                return
        
        self.chunk_requests[file_id] = {
            'missing': set(missing_chunks),
            'last_request': now
        }
        
        utils.log(f"Requesting {len(missing_chunks)} missing chunks for {file_id}", level="INFO")
        print(f"📥 Requesting {len(missing_chunks)} missing chunks...")
        
        # Send chunk request (you'd need to implement CHUNK_REQUEST message type)
        now = int(time.time())
        ttl_seconds = 3600
        token = f"{self.client.user_id}|{now + ttl_seconds}|file"
        msg = parser.format_message({
            'TYPE': 'CHUNK_REQUEST',
            'FROM': self.client.user_id,
            'TO': from_user,
            'FILE_ID': file_id,
            'MISSING_CHUNKS': ','.join(map(str, missing_chunks)),
            'TIMESTAMP': now,
            'TOKEN': token,
        })
        
        peer_info = self.client.peer_manager.peers.get(from_user)
        if peer_info and peer_info.get('ip_address'):
            dest_ip = peer_info['ip_address']
            self.client.network.send_message(msg, dest_ip=dest_ip)


    def _reassemble_file(self, file_id):
        file_info = self.incoming_files[file_id]
        original_filename = file_info['filename']

        print(f"[INFO] Reassembling file: {original_filename} (ID: {file_id})")

        safe_path = self._get_safe_filename(original_filename)
        print(f"[DEBUG] Safe path resolved to: {safe_path}")

        try:
            os.makedirs(self.downloads_dir, exist_ok=True)
            with open(safe_path, 'wb') as f:
                for i in range(file_info['total_chunks']):
                    if i not in file_info['chunks']:
                        print(f"[ERROR] Missing chunk {i}. Aborting save.")
                        return
                    f.write(file_info['chunks'][i])

            print(f"[INFO] File written successfully to {safe_path}")

            # Verify hash if available
            if file_info.get('filehash'):
                with open(safe_path, 'rb') as f:
                    file_data = f.read()
                    calculated_hash = hashlib.sha256(file_data).hexdigest()

                print(f"[DEBUG] Calculated hash: {calculated_hash}")
                print(f"[DEBUG] Expected hash:   {file_info['filehash']}")

                if calculated_hash != file_info['filehash']:
                    print(f"[ERROR] Hash mismatch for file {original_filename}. Deleting corrupt file.")
                    os.remove(safe_path)
                    file_info['status'] = "failed"
                    file_info['saved_path'] = None
                else:
                    file_info['status'] = "completed"
                    file_info['saved_path'] = safe_path
                    print(f"[SUCCESS] File {original_filename} saved and verified.")
            else:
                file_info['status'] = "completed"
                file_info['saved_path'] = safe_path
                print(f"[WARNING] File {original_filename} saved without hash verification (hash not provided in offer).")

        except Exception as e:
            print(f"[EXCEPTION] Failed to save file {original_filename}: {e}")
            file_info['status'] = "failed"


        def send_file_received(self, target_user_id, file_id):
            """Send file received confirmation"""
            now = int(time.time())
            ttl_seconds = 3600
            token = f"{self.client.user_id}|{now + ttl_seconds}|file"
            msg = parser.format_message({
                'TYPE': 'FILE_RECEIVED',
                'FROM': self.client.user_id,
                'TO': target_user_id,
                'FILE_ID': file_id,
                'TIMESTAMP': now,
                'TOKEN': token,
            })
            
            peer_info = self.client.peer_manager.peers.get(target_user_id)
            if peer_info and peer_info.get('ip_address'):
                dest_ip = peer_info['ip_address']
                self.client.network.send_message(msg, dest_ip=dest_ip)
                utils.log(f"Sent FILE_RECEIVED for {file_id} to {target_user_id}", level="INFO")

    def handle_file_received(self, parsed, sender_ip):
        """Handle file received confirmation"""
        from_user = parsed.get('FROM')
        to_user = parsed.get('TO')
        file_id = parsed.get('FILE_ID')
        token = parsed.get('TOKEN')
        
        if to_user != self.client.user_id or file_id is None:
            return
        if not self.client._validate_token_or_log(token, expected_scope='file', expected_user_id=from_user, sender_ip=sender_ip, message_type='FILE_RECEIVED'):
            return
            
        if file_id in self.outgoing_files:
            self.outgoing_files[file_id]['status'] = 'completed'
            display_name = self.client.peer_manager.get_display_name(from_user)
            print(f"✅ File successfully received by {display_name}")
            utils.log(f"File transfer completed: {file_id} received by {from_user}", level="INFO")

    def handle_file_reject(self, parsed, sender_ip):
        """Handle file rejection"""
        from_user = parsed.get('FROM')
        file_id = parsed.get('FILE_ID')
        token = parsed.get('TOKEN')
        
        if not self.client._validate_token_or_log(token, expected_scope='file', expected_user_id=from_user, sender_ip=sender_ip, message_type='FILE_REJECT'):
            return
            
        display_name = self.client.peer_manager.get_display_name(from_user)
        print(f"❌ File rejected by {display_name}")
        
        if file_id in self.outgoing_files:
            self.outgoing_files[file_id]['status'] = 'rejected'
            del self.outgoing_files[file_id]

    def handle_file_request(self, parsed, sender_ip):
        """Handle file request and start sending chunks with flow control"""
        from_user = parsed.get('FROM')
        file_id = parsed.get('FILE_ID')
        token = parsed.get('TOKEN')
        
        if not self.client._validate_token_or_log(token, expected_scope='file', expected_user_id=from_user, sender_ip=sender_ip, message_type='FILE_REQUEST'):
            return
            
        if file_id not in self.outgoing_files:
            utils.log(f"File request for unknown file {file_id}", level="WARN")
            return
            
        file_info = self.outgoing_files[file_id]
        if file_info['target_user'] != from_user:
            utils.log(f"File request from unauthorized user {from_user} for {file_id}", level="WARN")
            return
            
        # Start sending file in a separate thread to avoid blocking
        threading.Thread(
            target=self._send_file_chunks_threaded,
            args=(file_id, from_user),
            daemon=True
        ).start()

    def _send_file_chunks_threaded(self, file_id, target_user_id):
        """Send file chunks with flow control in separate thread"""
        if file_id not in self.outgoing_files:
            return
            
        file_info = self.outgoing_files[file_id]
        filepath = file_info['filename']
        
        try:
            with open(filepath, 'rb') as f:
                file_size = file_info['filesize']
                total_chunks = (file_size + self.chunk_size - 1) // self.chunk_size
                
                print(f"📤 Starting transfer: {file_info['display_name']} ({total_chunks} chunks)")
                file_info['status'] = 'sending'
                
                chunk_index = 0
                sent_count = 0
                
                while chunk_index < total_chunks:
                    chunk_data = f.read(self.chunk_size)
                    if not chunk_data:
                        break
                    
                    try:
                        self.send_file_chunk(target_user_id, file_id, chunk_index, chunk_data, total_chunks)
                        chunk_index += 1
                        sent_count += 1
                        
                        # Show progress every 50 chunks
                        if chunk_index % 50 == 0 or chunk_index == total_chunks:
                            progress = chunk_index / total_chunks * 100
                            print(f"📤 Sent: {progress:.1f}% ({chunk_index}/{total_chunks} chunks)")
                        
                        # Flow control: small delay every few chunks
                        if sent_count % 5 == 0:
                            time.sleep(0.01)  # 10ms delay every 5 chunks
                            
                    except Exception as e:
                        utils.log(f"Error sending chunk {chunk_index}: {e}", level="ERROR")
                        file_info['status'] = 'failed'
                        return
                
                file_info['status'] = 'sent'
                print(f"📤 Transfer completed: {chunk_index} chunks sent")
                utils.log(f"File transfer completed: {file_id} ({chunk_index} chunks sent)", level="INFO")
                
        except Exception as e:
            print(f"❌ Error sending file: {e}")
            utils.log(f"Error sending file {file_id}: {e}", level="ERROR")
            file_info['status'] = 'failed'

    def handle_chunk_request(self, parsed, sender_ip):
        """Handle request for specific missing chunks"""
        from_user = parsed.get('FROM')
        file_id = parsed.get('FILE_ID')
        missing_chunks_str = parsed.get('MISSING_CHUNKS')
        token = parsed.get('TOKEN')
        
        if not self.client._validate_token_or_log(token, expected_scope='file', expected_user_id=from_user, sender_ip=sender_ip, message_type='CHUNK_REQUEST'):
            return
            
        try:
            missing_chunks = [int(x) for x in missing_chunks_str.split(',')]
        except:
            utils.log(f"Invalid missing chunks format from {from_user}", level="WARN")
            return
            
        if file_id not in self.outgoing_files:
            return
            
        # Send requested chunks
        threading.Thread(
            target=self._resend_chunks,
            args=(file_id, from_user, missing_chunks),
            daemon=True
        ).start()

    def _resend_chunks(self, file_id, target_user_id, chunk_indices):
        """Resend specific chunks"""
        file_info = self.outgoing_files[file_id]
        filepath = file_info['filename']
        
        try:
            with open(filepath, 'rb') as f:
                total_chunks = (file_info['filesize'] + self.chunk_size - 1) // self.chunk_size
                
                print(f"📤 Resending {len(chunk_indices)} missing chunks...")
                
                for chunk_index in chunk_indices:
                    if chunk_index >= total_chunks:
                        continue
                        
                    f.seek(chunk_index * self.chunk_size)
                    chunk_data = f.read(self.chunk_size)
                    
                    if chunk_data:
                        self.send_file_chunk(target_user_id, file_id, chunk_index, chunk_data, total_chunks)
                        time.sleep(0.02)  # Small delay between resends
                        
        except Exception as e:
            utils.log(f"Error resending chunks for {file_id}: {e}", level="ERROR")

    def list_transfers(self):
        """List current file transfers"""
        print("\n📁 File Transfers:")
        print("\n📤 Outgoing:")
        for file_id, info in self.outgoing_files.items():
            status = info.get('status', 'unknown')
            print(f"  {file_id}: {info['display_name']} → {info['target_user']} ({status})")
            
        print("\n📥 Incoming:")
        for file_id, info in self.incoming_files.items():
            status = info.get('status', 'unknown')
            progress = ""
            if status == 'accepted' and 'chunks' in info:
                total = info.get('total_chunks', 1)
                received = len(info['chunks'])
                progress = f" ({received}/{total} chunks)"
            print(f"  {file_id}: {info['filename']} ← {info['from']} ({status}){progress}")

    def cleanup_old_transfers(self, max_age_hours=24):
        """Clean up old completed/failed transfers"""
        now = time.time()
        max_age_seconds = max_age_hours * 3600
        
        # Clean outgoing
        to_remove = []
        for file_id, info in self.outgoing_files.items():
            age = now - info.get('created', now)
            if age > max_age_seconds and info.get('status') in ['completed', 'failed', 'rejected']:
                to_remove.append(file_id)
        
        for file_id in to_remove:
            del self.outgoing_files[file_id]
            
        # Clean incoming  
        to_remove = []
        for file_id, info in self.incoming_files.items():
            age = now - info.get('created', now)
            if age > max_age_seconds and info.get('status') in ['completed', 'failed']:
                to_remove.append(file_id)
                
        for file_id in to_remove:
            del self.incoming_files[file_id]
            if file_id in self.chunk_requests:
                del self.chunk_requests[file_id]
                
        if to_remove:
            utils.log(f"Cleaned up {len(to_remove)} old transfers", level="INFO")