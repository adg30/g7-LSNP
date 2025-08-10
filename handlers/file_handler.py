import time
import secrets
import utils
import parser

class FileHandler:
    def __init__(self, client):
        self.client = client
        self.incoming_files = {}  # file_id -> {'filename': ..., 'chunks': {}, 'total': N, 'hash': ..., 'from': ...}
        self.outgoing_files = {}  # file_id -> {'filename': ..., 'filesize': ..., 'filehash': ...}

    def send_file_offer(self, target_user_id, filename, filesize, filehash):
        now = int(time.time())
        ttl_seconds = 3600
        token = f"{self.client.user_id}|{now + ttl_seconds}|file"
        message_id = secrets.token_hex(8)
        
        # Store file information for later chunk sending
        file_id = f"{self.client.user_id}_{filename}_{int(time.time())}"
        self.outgoing_files[file_id] = {
            'filename': filename,
            'filesize': int(filesize),
            'filehash': filehash,
            'target_user': target_user_id
        }
        
        msg = parser.format_message({
            'TYPE': 'FILE_OFFER',
            'FROM': self.client.user_id,
            'TO': target_user_id,
            'FILENAME': filename,
            'FILESIZE': filesize,
            'FILEHASH': filehash,
            'MESSAGE_ID': message_id,
            'TIMESTAMP': now,
            'TOKEN': token,
        })
        peer_info = self.client.peer_manager.peers.get(target_user_id)
        if peer_info and peer_info.get('ip_address'):
            dest_ip = peer_info['ip_address']
            self.client.network.send_message(msg, dest_ip=dest_ip)
            utils.log(f"Sent FILE_OFFER for {filename} to {target_user_id} via {dest_ip}", level="INFO")
            print(f"File offer sent with ID: {file_id}")
        else:
            utils.log(f"Cannot send FILE_OFFER — no known IP for {target_user_id}", level="WARN")

    def handle_file_offer(self, parsed, sender_ip):
        from_user = parsed.get('FROM')
        to_user = parsed.get('TO')
        filename = parsed.get('FILENAME')
        filesize = parsed.get('FILESIZE')
        filehash = parsed.get('FILEHASH')
        token = parsed.get('TOKEN')
        if to_user != self.client.user_id:
            return
        if not self.client._validate_token_or_log(token, expected_scope='file', expected_user_id=from_user, sender_ip=sender_ip, message_type='FILE_OFFER'):
            return
        display_name = self.client.peer_manager.get_display_name(from_user)
        utils.log_protocol_event("FILE_OFFER_RECEIVED", f"file={filename} size={filesize} from={display_name}", sender_ip, "FILE_OFFER")
        print(f"\n[FILE_OFFER] {display_name} wants to send you '{filename}' ({filesize} bytes, hash: {filehash})")
        
        # Store file offer for user interaction
        file_id = f"{from_user}_{filename}_{int(time.time())}"
        self.incoming_files[file_id] = {
            'filename': filename,
            'filesize': int(filesize),
            'filehash': filehash,
            'from': from_user,
            'chunks': {},
            'total_chunks': 0,
            'status': 'pending'
        }
        print(f"File ID: {file_id}")
        print("Commands: acceptfile <file_id> or rejectfile <file_id>")

    def send_file_accept(self, file_id):
        """Send acceptance of file transfer"""
        if file_id not in self.incoming_files:
            print(f"File {file_id} not found")
            return
            
        file_info = self.incoming_files[file_id]
        from_user = file_info['from']
        
        # Send ACK to start file transfer
        self.client.social_handler.send_ack(f"file_accept_{file_id}", self.client.peer_manager.peers.get(from_user, {}).get('ip_address'))
        file_info['status'] = 'accepted'
        
        # Request file chunks from sender
        print(f"File transfer accepted: {file_id}")
        print("Requesting file chunks...")
        
        # Send file request message
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

    def send_file_reject(self, file_id):
        """Send rejection of file transfer"""
        if file_id not in self.incoming_files:
            print(f"File {file_id} not found")
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
        print(f"File transfer rejected: {file_id}")

    def send_file_chunk(self, target_user_id, file_id, chunk_index, chunk_data, total_chunks):
        now = int(time.time())
        ttl_seconds = 3600
        token = f"{self.client.user_id}|{now + ttl_seconds}|file"
        msg = parser.format_message({
            'TYPE': 'FILE_CHUNK',
            'FROM': self.client.user_id,
            'TO': target_user_id,
            'FILEID': file_id,
            'CHUNK_INDEX': chunk_index,
            'TOTAL_CHUNKS': total_chunks,
            'CHUNK_SIZE': len(chunk_data),
            'TIMESTAMP': now,
            'TOKEN': token,
            'DATA': utils.base64_encode(chunk_data),
        })
        peer_info = self.client.peer_manager.peers.get(target_user_id)
        if peer_info and peer_info.get('ip_address'):
            dest_ip = peer_info['ip_address']
            self.client.network.send_message(msg, dest_ip=dest_ip)
            utils.log(f"Sent FILE_CHUNK {chunk_index} for {file_id} to {target_user_id} via {dest_ip}", level="INFO")
        else:
            utils.log(f"Cannot send FILE_CHUNK — no known IP for {target_user_id}", level="WARN")

    def handle_file_chunk(self, parsed, sender_ip):
        from_user = parsed.get('FROM')
        to_user = parsed.get('TO')
        file_id = parsed.get('FILEID')
        chunk_index = int(parsed.get('CHUNK_INDEX', -1))
        total_chunks = int(parsed.get('TOTAL_CHUNKS', -1))
        chunk_size = int(parsed.get('CHUNK_SIZE', -1))
        token = parsed.get('TOKEN')
        data = parsed.get('DATA')
        if to_user != self.client.user_id or file_id is None or chunk_index < 0 or data is None:
            return
        if not self.client._validate_token_or_log(token, expected_scope='file', expected_user_id=from_user, sender_ip=sender_ip, message_type='FILE_CHUNK'):
            return
        chunk_data = utils.base64_decode(data)
        if file_id not in self.incoming_files:
            self.incoming_files[file_id] = {'chunks': {}, 'from': from_user, 'total_chunks': total_chunks}
        self.incoming_files[file_id]['chunks'][chunk_index] = chunk_data
        utils.log(f"Received FILE_CHUNK {chunk_index}/{total_chunks} for {file_id} from {from_user}", level="INFO")
        
        # Check if all chunks received and reassemble file
        self._check_file_completion(file_id)

    def _check_file_completion(self, file_id):
        """Check if all file chunks are received and reassemble the file"""
        if file_id not in self.incoming_files:
            return
            
        file_info = self.incoming_files[file_id]
        chunks = file_info['chunks']
        total_chunks = file_info.get('total_chunks', 0)
        
        # Use actual total_chunks if available, otherwise estimate
        if total_chunks > 0:
            expected_chunks = total_chunks
        else:
            # Estimate total chunks based on file size (assuming 1KB chunks)
            expected_chunks = (file_info['filesize'] + 1023) // 1024
        
        # Check if we have all chunks to attempt reassembly
        if len(chunks) >= expected_chunks:
            try:
                # Reassemble file
                file_data = b''
                for i in range(expected_chunks):
                    if i in chunks:
                        file_data += chunks[i]
                    else:
                        utils.log(f"Missing chunk {i} for {file_id}", level="WARN")
                        return
                
                # Save file
                filename = file_info['filename']
                with open(filename, 'wb') as f:
                    f.write(file_data)
                
                # Send completion acknowledgment
                self.send_file_received(file_info['from'], file_id)
                
                # Clean up
                del self.incoming_files[file_id]
                
                print(f"\n[FILE_TRANSFER] File '{filename}' received and saved successfully!")
                utils.log(f"File {file_id} reassembled and saved as {filename}", level="INFO")
                
            except Exception as e:
                utils.log(f"Error reassembling file {file_id}: {e}", level="ERROR")

    def send_file_received(self, target_user_id, file_id):
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
            utils.log(f"Sent FILE_RECEIVED for {file_id} to {target_user_id} via {dest_ip}", level="INFO")
        else:
            utils.log(f"Cannot send FILE_RECEIVED — no known IP for {target_user_id}", level="WARN")

    def handle_file_received(self, parsed, sender_ip):
        from_user = parsed.get('FROM')
        to_user = parsed.get('TO')
        file_id = parsed.get('FILE_ID')
        token = parsed.get('TOKEN')
        if to_user != self.client.user_id or file_id is None:
            return
        if not self.client._validate_token_or_log(token, expected_scope='file', expected_user_id=from_user, sender_ip=sender_ip, message_type='FILE_RECEIVED'):
            return
        utils.log(f"File transfer complete: {file_id} acknowledged by {from_user}", level="INFO")
        print(f"\n[FILE_TRANSFER] File {file_id} successfully received by {from_user}.")

    def handle_file_reject(self, parsed, sender_ip):
        """Handle FILE_REJECT message"""
        from_user = parsed.get('FROM')
        file_id = parsed.get('FILE_ID')
        token = parsed.get('TOKEN')
        
        if not self.client._validate_token_or_log(token, expected_scope='file', expected_user_id=from_user, sender_ip=sender_ip, message_type='FILE_REJECT'):
            return
            
        utils.log(f"File {file_id} rejected by {from_user}", level="INFO")
        print(f"\n[FILE] File {file_id} was rejected by {self.client.peer_manager.get_display_name(from_user)}")
        
        # Remove from outgoing files if tracking
        if file_id in self.outgoing_files:
            del self.outgoing_files[file_id]

    def handle_file_request(self, parsed, sender_ip):
        """Handle FILE_REQUEST message - start sending file chunks"""
        from_user = parsed.get('FROM')
        file_id = parsed.get('FILE_ID')
        token = parsed.get('TOKEN')
        
        if not self.client._validate_token_or_log(token, expected_scope='file', expected_user_id=from_user, sender_ip=sender_ip, message_type='FILE_REQUEST'):
            return
            
        utils.log(f"File request received for {file_id} from {from_user}", level="INFO")
        print(f"\n[FILE] {self.client.peer_manager.get_display_name(from_user)} requested file {file_id}")
        
        # Find the file to send
        file_to_send = None
        for fid, file_info in self.outgoing_files.items():
            if fid == file_id or file_id in fid:  # Allow partial matching
                file_to_send = file_info
                break
        
        if not file_to_send:
            print(f"File {file_id} not found in outgoing files")
            return
            
        # Start sending file chunks
        print(f"Starting file transfer: {file_to_send['filename']} ({file_to_send['filesize']} bytes)")
        
        try:
            with open(file_to_send['filename'], 'rb') as f:
                chunk_size = 1024  # 1KB chunks
                chunk_index = 0
                
                # Calculate total chunks first
                file_size = file_to_send['filesize']
                total_chunks = (file_size + chunk_size - 1) // chunk_size
                
                while True:
                    chunk_data = f.read(chunk_size)
                    if not chunk_data:
                        break
                        
                    # Send chunk
                    self.send_file_chunk(from_user, file_id, chunk_index, chunk_data, total_chunks)
                    chunk_index += 1
                    
                    # Small delay to prevent overwhelming the network
                    time.sleep(0.01)
                
                print(f"File transfer completed: {chunk_index} chunks sent")
                
        except Exception as e:
            print(f"Error sending file: {e}")
            utils.log(f"Error sending file {file_id}: {e}", level="ERROR")
