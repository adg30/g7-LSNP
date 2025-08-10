import time
import os
import utils

class CLI:
    def __init__(self, client):
        self.client = client

    def run(self):
        """Run the command line interface"""
        print(f"\n=== LSNP Client Started ===")
        print(f"User: {self.client.user_id}")
        print(f"Display Name: {self.client.display_name}")
        print(f"Type 'help' for available commands")
        print(f"Type 'exit' to quit")
        
        while True:
            try:
                cmd = input("\nLSNP> ").strip().split()
                
                if not cmd:
                    continue
                    
                command = cmd[0].lower()
                
                if command == "exit":
                    break
                elif command == "help":
                    self.show_help()
                elif command == "peers":
                    self.client.peer_manager.display_all_peers()
                elif command == "verbose":
                    utils.VERBOSE = not utils.VERBOSE
                    print(f"Verbose mode: {'ON' if utils.VERBOSE else 'OFF'}")
                elif command == "follow" and len(cmd) > 1:
                    target = cmd[1]
                    if not target.startswith("user@"):
                        user_id = self.client.get_user_id_by_display_name(target)
                        if user_id:
                            target = user_id
                        else:
                            print(f"User '{target}' not found. Use full user ID (e.g., user@192.168.1.4)")
                            continue
                    self.client.social_handler.send_follow_action(target, "FOLLOW")
                elif command == "unfollow" and len(cmd) > 1:
                    target = cmd[1]
                    if not target.startswith("user@"):
                        user_id = self.client.get_user_id_by_display_name(target)
                        if user_id:
                            target = user_id
                        else:
                            print(f"User '{target}' not found. Use full user ID (e.g., user@192.168.1.4)")
                            continue
                    self.client.social_handler.send_follow_action(target, "UNFOLLOW")
                elif command == "followers":
                    self.client.peer_manager.display_followers(self.client.user_id)
                elif command == "post":
                    content = input("Enter your post: ").strip()
                    if content:
                        self.client.social_handler.send_post(content)
                    else:
                        print("Post content cannot be empty")
                elif command == "viewposts":
                    if self.client.social_handler.posts:
                        print("\n=== Recent Posts ===")
                        for timestamp, post in sorted(self.client.social_handler.posts.items(), reverse=True):
                            author_name = self.client.peer_manager.get_display_name(post['author'])
                            print(f"[{time.ctime(timestamp)}] {author_name}: {post['content']}")
                    else:
                        print("No posts available")
                elif command == "message" and len(cmd) > 2:
                    target = cmd[1]
                    if not target.startswith("user@"):
                        user_id = self.client.get_user_id_by_display_name(target)
                        if user_id:
                            target = user_id
                        else:
                            print(f"User '{target}' not found. Use full user ID (e.g., user@192.168.1.4)")
                            continue
                    content = " ".join(cmd[2:])
                    self.client.social_handler.send_dm(target, content)
                elif command == "like" and len(cmd) > 2:
                    target = cmd[1]
                    if not target.startswith("user@"):
                        user_id = self.client.get_user_id_by_display_name(target)
                        if user_id:
                            target = user_id
                        else:
                            print(f"User '{target}' not found. Use full user ID (e.g., user@192.168.1.4)")
                            continue
                    try:
                        post_timestamp = int(cmd[2])
                        self.client.social_handler.send_like(target, post_timestamp, "LIKE")
                    except ValueError:
                        print("Post timestamp must be a number")
                elif command == "unlike" and len(cmd) > 2:
                    target = cmd[1]
                    if not target.startswith("user@"):
                        user_id = self.client.get_user_id_by_display_name(target)
                        if user_id:
                            target = user_id
                        else:
                            print(f"User '{target}' not found. Use full user ID (e.g., user@192.168.1.4)")
                            continue
                    try:
                        post_timestamp = int(cmd[2])
                        self.client.social_handler.send_like(target, post_timestamp, "UNLIKE")
                    except ValueError:
                        print("Post timestamp must be a number")
                elif command == "revoke" and len(cmd) > 1:
                    token = cmd[1]
                    self.client.social_handler.send_revoke(token)
                elif command == "avatar":
                    if len(cmd) < 2:
                        print("Usage: avatar <set|clear|info> [image_file]")
                        print("Examples:")
                        print("  avatar set profile.png")
                        print("  avatar clear")
                        print("  avatar info")
                        continue
                    
                    subcmd = cmd[1].lower()
                    if subcmd == "set" and len(cmd) > 2:
                        image_file = cmd[2]
                        success, message = self.client.profile_handler.set_avatar_from_file(image_file)
                        print(message)
                        if success:
                            print("Avatar will be included in your next profile broadcast")
                    elif subcmd == "clear":
                        success, message = self.client.profile_handler.clear_avatar()
                        print(message)
                    elif subcmd == "info":
                        if self.client.profile_handler.avatar_type and self.client.profile_handler.avatar_data:
                            print(f"Current Avatar:")
                            print(f"  Type: {self.client.profile_handler.avatar_type}")
                            print(f"  Encoding: {self.client.profile_handler.avatar_encoding}")
                            print(f"  Data Size: {len(self.client.profile_handler.avatar_data)} characters")
                            print(f"  Base64 Preview: {self.client.profile_handler.avatar_data[:50]}...")
                        else:
                            print("No avatar set")
                    else:
                        print("Usage: avatar <set|clear|info> [image_file]")
                        print("Examples:")
                        print("  avatar set profile.png")
                        print("  avatar clear")
                        print("  avatar info")

                # --- ENHANCED MILESTONE 3 COMMANDS ---
                elif command == "sendfile":
                    if len(cmd) > 2:
                        target = cmd[1]
                        # Try to find user ID by display name if not full user ID
                        if not target.startswith("user@"):
                            user_id = self.client.get_user_id_by_display_name(target)
                            if user_id:
                                target = user_id
                            else:
                                print(f"❌ User '{target}' not found. Use full user ID (e.g., user@192.168.1.4)")
                                continue
                        filename = cmd[2]
                        
                        # Use the improved file handler
                        file_id = self.client.file_handler.send_file_offer(target, filename)
                        if file_id:
                            print(f"✅ File offer sent: {os.path.basename(filename)} (ID: {file_id})")
                        else:
                            print(f"❌ Failed to send file offer")
                    else:
                        print("Usage: sendfile <user_id> <filename>")
                        print("Example: sendfile user@192.168.1.4 test.txt")
                        print("         sendfile Alice document.pdf")

                elif command == "acceptfile":
                    if len(cmd) == 2:
                        file_id = cmd[1]
                        self.client.file_handler.send_file_accept(file_id)
                    else:
                        print("Usage: acceptfile <file_id>")
                        print("Example: acceptfile alice_document_1691234567_abc123")

                elif command == "rejectfile":
                    if len(cmd) == 2:
                        file_id = cmd[1]
                        self.client.file_handler.send_file_reject(file_id)
                    else:
                        print("Usage: rejectfile <file_id>")
                        print("Example: rejectfile alice_document_1691234567_abc123")

                elif command == "listfiles":
                    # Use the improved list_transfers method
                    self.client.file_handler.list_transfers()

                elif command == "fileinfo":
                    if len(cmd) == 2:
                        file_id = cmd[1]
                        # Check both incoming and outgoing files
                        file_info = None
                        direction = None
                        
                        if file_id in self.client.file_handler.incoming_files:
                            file_info = self.client.file_handler.incoming_files[file_id]
                            direction = "📥 Incoming"
                        elif file_id in self.client.file_handler.outgoing_files:
                            file_info = self.client.file_handler.outgoing_files[file_id]
                            direction = "📤 Outgoing"
                        
                        if file_info:
                            print(f"\n📁 File Information - {direction}")
                            print(f"File ID: {file_id}")
                            print(f"Filename: {file_info.get('filename', file_info.get('display_name', 'Unknown'))}")
                            print(f"Size: {file_info['filesize']} bytes ({file_info['filesize']//1024} KB)")
                            print(f"Status: {file_info.get('status', 'Unknown')}")
                            
                            if 'filehash' in file_info:
                                print(f"Hash: {file_info['filehash']}")
                            
                            if direction == "📥 Incoming":
                                print(f"From: {self.client.peer_manager.get_display_name(file_info['from'])}")
                                if 'chunks' in file_info:
                                    total = file_info.get('total_chunks', 1)
                                    received = len(file_info['chunks'])
                                    progress = (received / total * 100) if total > 0 else 0
                                    print(f"Progress: {received}/{total} chunks ({progress:.1f}%)")
                            else:
                                print(f"To: {self.client.peer_manager.get_display_name(file_info['target_user'])}")
                        else:
                            print(f"❌ File ID '{file_id}' not found")
                    else:
                        print("Usage: fileinfo <file_id>")
                        print("Example: fileinfo alice_document_1691234567_abc123")

                elif command == "downloads":
                    # List files in the downloads directory
                    downloads_dir = getattr(self.client.file_handler, 'downloads_dir', 'downloads')
                    try:
                        if os.path.exists(downloads_dir):
                            files = [f for f in os.listdir(downloads_dir) if os.path.isfile(os.path.join(downloads_dir, f))]
                            if files:
                                print(f"\n📂 Downloaded Files ({downloads_dir}):")
                                for i, filename in enumerate(files, 1):
                                    filepath = os.path.join(downloads_dir, filename)
                                    size = os.path.getsize(filepath)
                                    modified = time.ctime(os.path.getmtime(filepath))
                                    print(f"  {i}. {filename} ({size} bytes) - {modified}")
                            else:
                                print(f"📂 Downloads directory is empty ({downloads_dir})")
                        else:
                            print(f"📂 Downloads directory doesn't exist yet ({downloads_dir})")
                    except Exception as e:
                        print(f"❌ Error listing downloads: {e}")

                elif command == "cleanup":
                    # Clean up old transfers
                    if len(cmd) >= 2:
                        try:
                            hours = int(cmd[1])
                            self.client.file_handler.cleanup_old_transfers(max_age_hours=hours)
                            print(f"✅ Cleaned up transfers older than {hours} hours")
                        except ValueError:
                            print("❌ Invalid hours value")
                    else:
                        # Default cleanup (24 hours)
                        self.client.file_handler.cleanup_old_transfers()
                        print("✅ Cleaned up transfers older than 24 hours")
                    print("💡 Use 'cleanup <hours>' to specify age limit")

                elif command == "group":
                    if len(cmd) < 2:
                        print("Usage: group <create|message|list> [args...]")
                        print("Examples:")
                        print("  group create mygroup user1,user2,user3")
                        print("  group message mygroup Hello everyone!")
                        print("  group list")
                        continue
                    
                    subcmd = cmd[1].lower()
                    if subcmd == "create" and len(cmd) > 2:
                        group_name = cmd[2]
                        members = cmd[3].split(',') if len(cmd) > 3 else []
                        members.append(self.client.user_id)  # Include self
                        group_id = f"group_{int(time.time())}"
                        self.client.group_handler.send_group_create(group_id, group_name, members)
                        print(f"Group '{group_name}' created with ID: {group_id}")
                    elif subcmd == "message" and len(cmd) > 2:
                        group_id = cmd[2]
                        content = " ".join(cmd[3:]) if len(cmd) > 3 else ""
                        if content:
                            self.client.group_handler.send_group_message(group_id, content)
                        else:
                            print("Message content cannot be empty")
                    elif subcmd == "list":
                        if self.client.group_handler.groups:
                            print("\n=== Your Groups ===")
                            for group_id, group_info in self.client.group_handler.groups.items():
                                print(f"{group_id}: {group_info['name']} ({len(group_info['members'])} members)")
                        else:
                            print("No groups")
                    elif subcmd == "update" and len(cmd) > 2:
                        group_id = cmd[2]
                        add_members = []
                        remove_members = []
                        i = 3
                        while i < len(cmd):
                            if cmd[i] == '--add' and i + 1 < len(cmd):
                                add_members = cmd[i+1].split(',')
                                i += 2
                            elif cmd[i] == '--remove' and i + 1 < len(cmd):
                                remove_members = cmd[i+1].split(',')
                                i += 2
                            else:
                                print(f"Invalid argument: {cmd[i]}")
                                break
                        self.client.group_handler.send_group_update(group_id, add_members, remove_members)
                    else:
                        print("Usage: group <create|message|list|update> [args...]")

                elif command == "ttt":
                    if len(cmd) < 2:
                        print("Usage: ttt <invite|accept|reject|move|board|list> [args...]")
                        print("Examples:")
                        print("  ttt invite user@192.168.1.4")
                        print("  ttt accept game_1234567890")
                        print("  ttt reject game_1234567890")
                        print("  ttt move game_1234567890 4")
                        print("  ttt board game_1234567890")
                        print("  ttt list")
                        continue
                    
                    subcmd = cmd[1].lower()
                    if subcmd == "invite" and len(cmd) > 2:
                        target = cmd[2]
                        # Try to find user ID by display name if not full user ID
                        if not target.startswith("user@"):
                            user_id = self.client.get_user_id_by_display_name(target)
                            if user_id:
                                target = user_id
                            else:
                                print(f"User '{target}' not found. Use full user ID (e.g., user@192.168.1.4)")
                                continue
                        
                        # Prevent self-invites
                        if target == self.client.user_id:
                            print("You cannot invite yourself to a game!")
                            continue
                            
                        game_id = f"game_{int(time.time())}"
                        self.client.game_handler.send_tictactoe_invite(target, game_id)
                        print(f"Tic Tac Toe invite sent to {target} (game_id: {game_id})")
                    elif subcmd == "accept" and len(cmd) > 2:
                        game_id = cmd[2]
                        self.client.game_handler.send_tictactoe_accept(game_id)
                    elif subcmd == "reject" and len(cmd) > 2:
                        game_id = cmd[2]
                        self.client.game_handler.send_tictactoe_reject(game_id)
                    elif subcmd == "move" and len(cmd) > 3:
                        game_id = cmd[2]
                        try:
                            position = int(cmd[3])
                            if 0 <= position <= 8:
                                success = self.client.game_handler.send_tictactoe_move(game_id, position)
                                if not success:
                                    print("Move failed. Check the game status.")
                            else:
                                print("Position must be 0-8")
                        except ValueError:
                            print("Position must be a number 0-8")
                    elif subcmd == "board" and len(cmd) > 2:
                        game_id = cmd[2]
                        if game_id in self.client.game_handler.tictactoe_games:
                            self.client.game_handler._display_game_board(game_id)
                        else:
                            print(f"Game {game_id} not found")
                    elif subcmd == "list":
                        if self.client.game_handler.tictactoe_games:
                            print("\n=== Your Tic Tac Toe Games ===")
                            for game_id, game_info in self.client.game_handler.tictactoe_games.items():
                                print(f"{game_id}: {game_info['status']} (turn: {game_info['turn']})")
                        else:
                            print("No active games")
                    else:
                        print("Usage: ttt <invite|accept|reject|move|board|list> [args...]")

                elif command == "test":
                    if len(cmd) < 2:
                        print("Usage: test <packetloss|disable> [rate]")
                        print("Examples:")
                        print("  test packetloss 0.1")
                        print("  test disable")
                        continue
                    
                    subcmd = cmd[1].lower()
                    if subcmd == "packetloss" and len(cmd) > 2:
                        try:
                            rate = float(cmd[2])
                            if 0 <= rate <= 1:
                                utils.enable_packet_loss_simulation(rate)
                                print(f"Packet loss simulation enabled with rate {rate}")
                            else:
                                print("Rate must be between 0 and 1")
                        except ValueError:
                            print("Rate must be a number")
                    elif subcmd == "disable":
                        utils.disable_packet_loss_simulation()
                        print("Packet loss simulation disabled")
                    else:
                        print("Usage: test <packetloss|disable> [rate]")

                else:
                    print("Unknown command. Type 'help' for usage information or try:")
                    print("  peers, follow, unfollow, post, message, like, unlike, revoke, verbose")
                    print("  sendfile, group, ttt, exit")
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
        
        # Cleanup
        self.client.cleanup()
        print("Goodbye!")

    def show_help(self):
        """Show help information"""
        print(f"\n=== LSNP Client Help ===")
        print(f"User: {self.client.user_id} | Display: {self.client.display_name}")
        
        print("\n📱 PROFILE & DISCOVERY")
        print("  peers                    - Show all discovered peers")
        print("  verbose                  - Toggle verbose logging")
        print("  avatar set <image_file>  - Set profile picture")
        print("  avatar clear             - Remove profile picture")
        print("  avatar info              - Show avatar information")
        
        print("\n👥 SOCIAL NETWORKING")
        print("  follow <user_id>         - Follow a user")
        print("  unfollow <user_id>       - Unfollow a user")
        print("  followers                - Show your followers")
        print("  post                     - Create a new post")
        print("  viewposts                - View recent posts")
        print("  message <user_id> <text> - Send private message")
        print("  like <user_id> <timestamp> - Like a post")
        print("  unlike <user_id> <timestamp> - Unlike a post")
        
        print("\n📁 FILE SHARING")
        print("  sendfile <user> <file> - Offer file to user")
        print("  acceptfile <file_id>   - Accept file transfer")
        print("  rejectfile <file_id>   - Reject file transfer")
        print("  listfiles             - Show all file transfers")
        print("  fileinfo <file_id>    - Show detailed file info")
        print("  downloads             - List downloaded files")
        print("  cleanup [hours]       - Clean up old transfers")
        print("")
        
        print("\n👥 GROUP MANAGEMENT")
        print("  group create <name> <members> - Create a group")
        print("  group message <id> <text>     - Send group message")
        print("  group list                     - List your groups")
        print("  group update <id> [--add user1,user2] [--remove user3] - Update group members")
        
        print("\n🎮 TIC TAC TOE")
        print("  ttt invite <user_id>     - Invite user to play")
        print("  ttt accept <game_id>     - Accept game invite")
        print("  ttt reject <game_id>     - Reject game invite")
        print("  ttt move <game_id> <pos> - Make a move (0-8)")
        print("  ttt board <game_id>      - Show game board")
        print("  ttt list                 - List active games")
        
        print("\n🧪 TESTING")
        print("  test packetloss <rate>   - Enable packet loss simulation")
        print("  test disable             - Disable packet loss simulation")
        
        print("\n💡 TIPS:")
        print("  - Use display names instead of user IDs where possible")
        print("  - File transfers require acceptance before starting")
        print("  - Tic Tac Toe positions: 0-8 (top-left to bottom-right)")
        print("  - Type 'exit' to quit the client")
