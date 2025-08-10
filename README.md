# Local Social Networking Protocol (LSNP) Implementation

A complete implementation of the Local Social Networking Protocol over UDP for CSNETWK's Major Course Output

## Features Implemented

### Milestone 1 (Basic Protocol)
- ✅ **User Discovery & Presence**: PING and PROFILE messages every 5 minutes
- ✅ **Messaging**: POST, DM, FOLLOW, UNFOLLOW messages
- ✅ **Protocol Compliance**: Key-value, UTF-8, blank-line terminated format
- ✅ **Verbose & Non-Verbose Modes**: Configurable logging
- ✅ **Token Validation**: Basic token structure and validation

### Milestone 2 (Advanced Features)
- ✅ **Profile Pictures**: AVATAR_URL and AVATAR_HASH support
- ✅ **Likes**: LIKE/UNLIKE messages tied to POST_TIMESTAMP
- ✅ **File Transfer**: FILE_OFFER, FILE_CHUNK, FILE_RECEIVED with Base64 encoding
- ✅ **Token Handling**: Full scope validation (broadcast, chat, file, follow, game, group)
- ✅ **Group Management**: GROUP_CREATE, GROUP_UPDATE, GROUP_MESSAGE
- ✅ **Tic Tac Toe Game**: TICTACTOE_INVITE, TICTACTOE_MOVE, TICTACTOE_RESULT
- ✅ **Enhanced Logging**: Protocol events, token checks, retries, drops

## Quick Start

### Prerequisites
- Python 3.6+
- Two or more machines on the same network (or multiple terminals on one machine)

### Installation
1. Clone the repository
2. Navigate to the project directory
3. Run the client: `python main.py`

### Basic Usage

#### Starting the Client
```bash
python main.py
```
You'll be prompted to enter your display name.

#### Discovering Peers
```bash
LSNP> peers
```
Shows all discovered peers on the network.

#### Basic Social Features
```bash
# Follow a user
LSNP> follow user@192.168.1.4

# Create a post
LSNP> post
Enter post content: Hello world!

# Send private message
LSNP> message user@192.168.1.4 Hello there!

# Like a post
LSNP> like user@192.168.1.4 1234567890
```

## Milestone Verification

This section provides a step-by-step guide to verify the functionality of each milestone.

### Milestone 1: Basic Functionality

1.  **Clean Architecture & Logging**:
    *   Verify the file structure in the "File Structure" section.
    *   Run the client with `python main.py` and use the `verbose` command to toggle logging. Observe the detailed output.

2.  **Protocol Compliance Test Suite**:
    *   Use the `cli_test.py` script to craft and send messages.
    *   `python cli_test.py send <message_type> <key=value...>`
    *   Example: `python cli_test.py send PROFILE USER_ID=test@127.0.0.1 DISPLAY_NAME=tester`

3.  **Message Sending and Receiving**:
    *   Run two clients on the same network.
    *   From one client, send a DM to the other: `message <user_id> Hello!`
    *   Verify that the message is received on the other client.

4.  **Protocol Parsing and Message Format**:
    *   In verbose mode, observe the parsed messages.
    *   Use the `peers` command to see a list of known peers.
    *   Use `viewposts` and receive DMs to see the formatted output.

### Milestone 2: Basic User Discovery and Messaging

1.  **User Discovery and Presence**:
    *   Run two clients. They should automatically discover each other within 5 minutes.
    *   Use the `peers` command to verify that the other client is listed.

2.  **Messaging Functionality**:
    *   **POST**: Use the `post` command. Only followers should see the post.
    *   **DM**: Use the `message` command to send a private message.
    *   **FOLLOW/UNFOLLOW**: Use the `follow` and `unfollow` commands. Use the `followers` command to verify.

### Milestone 3: Advanced Functionality

1.  **Profile Picture and Likes**:
    *   **Avatar**: Use `avatar set <image_file>` and `avatar clear`. Use `peers` on another client to see the avatar information.
    *   **Likes**: Use `like <user_id> <timestamp>` on a post. The author of the post will receive a notification. Only followers can like a post.

2.  **File Transfer**:
    *   Use `sendfile <user> <file>` to offer a file.
    *   The other user must use `acceptfile <file_id>` to receive it.
    *   Check the `downloads` directory for the transferred file.

3.  **Token Handling and Scope Validation**:
    *   This is handled automatically by the client.
    *   In verbose mode, you can see token validation logs for each action.

4.  **Group Management**:
    *   Use `group create <name> <members>` to create a group.
    *   Use `group message <id> <text>` to send a message to the group.
    *   Use `group list` to see your groups.
    *   Use `group update` to add/remove members.

5.  **Game Support (Tic Tac Toe)**:
    *   Use `ttt invite <user_id>` to start a game.
    *   The other user must `ttt accept <game_id>`.
    *   Use `ttt move <game_id> <pos>` to play.
    *   Use `ttt board <game_id>` to see the board.

## Detailed Command Reference

### General Commands

#### `help`
Show the help message with all available commands.
```
LSNP> help
```

#### `exit`
Exit the LSNP client.
```
LSNP> exit
```

### Profile & Discovery

#### `peers`
Show all discovered peers on the network.
```
LSNP> peers
```

#### `verbose`
Toggle verbose logging mode.
```
LSNP> verbose
```

#### `avatar set <image_file>`
Set your profile picture from an image file.
```
LSNP> avatar set my_avatar.png
```

#### `avatar clear`
Remove your profile picture.
```
LSNP> avatar clear
```

#### `avatar info`
Show information about your current avatar.
```
LSNP> avatar info
```

### Social Networking

#### `follow <user_id>`
Follow a user. You can use display names or full user IDs.
```
LSNP> follow user@192.168.1.4
LSNP> follow Alice
```

#### `unfollow <user_id>`
Unfollow a user.
```
LSNP> unfollow user@192.168.1.4
```

#### `followers`
Show your current followers.
```
LSNP> followers
```

#### `post`
Create a new post.
```
LSNP> post
Enter post content: This is my first post!
```

#### `viewposts`
View the most recent posts from users you follow.
```
LSNP> viewposts
```

#### `message <user_id> <text>`
Send a private message to a user.
```
LSNP> message user@192.168.1.4 Hello there!
```

#### `like <user_id> <timestamp>`
Like a post by its timestamp.
```
LSNP> like user@192.168.1.4 1234567890
```

#### `unlike <user_id> <timestamp>`
Unlike a post by its timestamp.
```
LSNP> unlike user@192.168.1.4 1234567890
```

#### `revoke <token>`
Revoke a token.
```
LSNP> revoke user@192.168.1.4|1234567890|follow
```

### File Sharing

#### `sendfile <user> <file>`
Offer to send a file to a user.
```
LSNP> sendfile user@192.168.1.4 document.pdf
```

#### `acceptfile <file_id>`
Accept an incoming file transfer.
```
LSNP> acceptfile some_file_id
```

#### `rejectfile <file_id>`
Reject an incoming file transfer.
```
LSNP> rejectfile some_file_id
```

#### `listfiles`
Show all active and recent file transfers.
```
LSNP> listfiles
```

#### `fileinfo <file_id>`
Show detailed information about a file transfer.
```
LSNP> fileinfo some_file_id
```

#### `downloads`
List all files that have been successfully downloaded.
```
LSNP> downloads
```

#### `cleanup [hours]`
Clean up old file transfers. Defaults to 24 hours.
```
LSNP> cleanup
LSNP> cleanup 48
```

### Group Management

#### `group create <name> <members>`
Create a new group with a list of comma-separated members.
```
LSNP> group create MyFriends user@192.168.1.4,user@192.168.1.5
```

#### `group message <id> <text>`
Send a message to a group.
```
LSNP> group message my_group_id Hello everyone!
```

#### `group list`
List all the groups you are a member of.
```
LSNP> group list
```

#### `group update <id> [--add user1,user2] [--remove user3]`
Add or remove members from a group.
```
LSNP> group update my_group_id --add user@192.168.1.6 --remove user@192.168.1.4
```

### Tic Tac Toe

#### `ttt invite <user_id>`
Invite a user to play Tic Tac Toe.
```
LSNP> ttt invite user@192.168.1.4
```

#### `ttt accept <game_id>`
Accept a Tic Tac Toe game invitation.
```
LSNP> ttt accept some_game_id
```

#### `ttt reject <game_id>`
Reject a Tic Tac Toe game invitation.
```
LSNP> ttt reject some_game_id
```

#### `ttt move <game_id> <pos>`
Make a move in a Tic Tac Toe game (positions 0-8).
```
LSNP> ttt move some_game_id 4
```

#### `ttt board <game_id>`
Show the game board.
```
LSNP> ttt board some_game_id
```

#### `ttt list`
List all your active Tic Tac Toe games.
```
LSNP> ttt list
```

### Testing

#### `test packetloss <rate>`
Enable packet loss simulation with a given rate (0.0 to 1.0).
```
LSNP> test packetloss 0.1
```

#### `test disable`
Disable the packet loss simulation.
```
LSNP> test disable
```

## Protocol Details

### Message Format
All messages follow the RFC specification:
- Key-value pairs
- UTF-8 encoding
- Blank-line terminated
- Optional raw content for file chunks

### Token Format
Tokens use the format: `user_id|expiry|scope`
- `user_id`: The user's identifier
- `expiry`: Unix timestamp when token expires
- `scope`: Permission scope (broadcast, chat, file, follow, game, group)

### Network Configuration
- **Port**: 50999 (configurable in `config.py`)
- **Broadcast**: Automatically detected based on local network
- **Buffer Size**: 65535 bytes
- **Encoding**: UTF-8

## Troubleshooting

### Common Issues

#### "No known IP for user"
- **Cause**: User not discovered yet or using display name instead of user ID
- **Solution**: Use `peers` command to see available users, then use full user ID

#### "Port in use"
- **Cause**: Another instance is running
- **Solution**: Close other instances or change port in `config.py`

#### "Cannot send message"
- **Cause**: Network connectivity issues or firewall blocking
- **Solution**: Check network connectivity and firewall settings

#### "User not found"
- **Cause**: Using display name that doesn't exist
- **Solution**: Use `peers` to see actual user IDs

### Debug Mode
Enable verbose logging to see detailed protocol information:
```
LSNP> verbose
```

## File Structure
```
g7-LSNP/
├── main.py              # Main client application
├── network.py           # Network communication layer
├── parser.py            # Message parsing and formatting
├── peers.py             # Peer management
├── utils.py             # Utility functions and logging
├── config.py            # Configuration settings
├── cli_test.py          # CLI testing utilities
└── tests/               # Unit tests
    └── test_parser.py   # Parser tests
```

## Configuration

Edit `config.py` to modify:
- **PORT**: Network port (default: 50999)
- **BROADCAST**: Broadcast address (auto-detected)
- **BUFFER_SIZE**: Network buffer size
- **VERBOSE_MODE**: Default logging level

## Work Distribution

The tasks were distributed among the team members based on the following roles:
-   **Primary**: Responsible for the main implementation of the feature.
-   **Secondary**: Assists the primary member and is familiar with the feature's code.
-   **Reviewer**: Reviews the code for correctness, style, and adherence to the protocol.

| Task / Role                     | Member 1 (Aaron)                               | Member 2 (Robbie)                            | Member 3 (Austin)                              | Member 4 (Rai)                             |
| ------------------------------- | ------------------------------------------- | ------------------------------------------- | ------------------------------------------- | ------------------------------------------- |
| **Network Communication**       |                                             |                                             |                                             |                                             |
| UDP Socket Setup                | Primary                                     | Reviewer                                    | Secondary                                   |                                             |
| mDNS Discovery Integration      | Secondary                                   | Primary                                     | Reviewer                                    |                                             |
| IP Address Logging              | Reviewer                                    | Secondary                                   | Primary                                     |                                             |
| **Core Feature Implementation** |                                             |                                             |                                             |                                             |
| Core Messaging                  | Primary                                     | Reviewer                                    |                                             | Secondary                                   |
| File Transfer                   | Secondary                                   | Primary                                     |                                             | Reviewer                                    |
| Tic Tac Toe Game                | Reviewer                                    | Secondary                                   | Primary                                     |                                             |
| Group Creation / Messaging      |                                             | Reviewer                                    | Secondary                                   | Primary                                     |
| Induced Packet Loss             | Primary                                     |                                             | Reviewer                                    | Secondary                                   |
| Acknowledgement / Retry         | Secondary                                   | Reviewer                                    |                                             | Primary                                     |
| **UI & Logging**                |                                             |                                             |                                             |                                             |
| Verbose Mode Support            | Reviewer                                    |                                             | Primary                                     | Secondary                                   |
| Terminal Grid Display           | Primary                                     | Secondary                                   |                                             | Reviewer                                    |
| Message Parsing & Debug Output  | Secondary                                   | Primary                                     | Reviewer                                    |                                             |
| **Testing and Validation**      |                                             |                                             |                                             |                                             |
| Inter-group Testing             | Reviewer                                    | Primary                                     | Secondary                                   |                                             |
| Correct Parsing Validation      | Primary                                     | Reviewer                                    |                                             | Secondary                                   |
| Token Expiry & IP Match         | Secondary                                   |                                             | Reviewer                                    | Primary                                     |
| **Documentation & Coordination**|                                             |                                             |                                             |                                             |
| RFC & Project Report            | Primary                                     | Reviewer                                    | Secondary                                   |                                             |
| Milestone Tracking              | Secondary                                   |                                             | Reviewer                                    | Primary                                     |

## AI Disclaimer

This project was developed with the assistance of AI tools, including ChatGPT and GitHub Copilot. These tools were used for:
- **Code Generation**: Generating boilerplate code, utility functions, and initial class structures.
- **Debugging**: Identifying and fixing bugs in the network and parsing logic.
- **Protocol Design**: Refining the LSNP message formats and token validation rules.
- **Documentation**: Writing and formatting the README and other documentation.

All AI-generated code was reviewed, tested, and adapted to fit the project's requirements. The final implementation represents our own work and understanding of the protocol.
