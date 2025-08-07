# Local Social Networking Protocol (LSNP) Implementation

A complete implementation of the Local Social Networking Protocol over UDP for CSNETWK's Major Course Output

## Features Implemented

### Milestone 2 (Basic Protocol)
- ✅ **User Discovery & Presence**: PING and PROFILE messages every 5 minutes
- ✅ **Messaging**: POST, DM, FOLLOW, UNFOLLOW messages
- ✅ **Protocol Compliance**: Key-value, UTF-8, blank-line terminated format
- ✅ **Verbose & Non-Verbose Modes**: Configurable logging
- ✅ **Token Validation**: Basic token structure and validation

### Milestone 3 (Advanced Features)
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
# Follow a user first
LSNP> follow user@192.168.1.4

# Create a post (sent to followers only)
LSNP> post
Enter post content: Hello world!

# Send private message
LSNP> message user@192.168.1.4 Hello there!

# Like a post
LSNP> like user@192.168.1.4 1234567890
```

## Detailed Command Reference

### Basic Commands (Milestone 2)

#### `peers`
Show all discovered peers on the network.
```
LSNP> peers
```

#### `follow <user_id>`
Follow a user. You can use display names or full user IDs.
```
LSNP> follow user@192.168.1.4
LSNP> follow pc  # if 'pc' is the display name
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
Create a new post (sent to your followers only).
```
LSNP> post
Enter post content: This is my first post!
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

#### `verbose`
Toggle verbose logging mode.
```
LSNP> verbose
```

### Advanced Commands (Milestone 3)

#### File Transfer
```bash
# Send a file to a user
LSNP> sendfile user@192.168.1.4 test.txt
```

#### Group Management
```bash
# Create a group
LSNP> group create mygroup "My Group" user@192.168.1.4,user@192.168.1.5

# Send message to group
LSNP> group message mygroup Hello group!

# List your groups
LSNP> group list

# Show group members
LSNP> group members mygroup
```

#### Tic Tac Toe Game
```bash
# Invite someone to play
LSNP> ttt invite user@192.168.1.4

# Make a move (positions 0-8)
LSNP> ttt move game_1234567890 4

# Show game board
LSNP> ttt board game_1234567890

# List active games
LSNP> ttt list
```

## Testing Guide

### Single Machine Testing
1. Open multiple terminal windows
2. Run `python main.py` in each terminal
3. Use different display names for each instance
4. Test communication between instances

### Multi-Machine Testing
1. Ensure all machines are on the same network
2. Run `python main.py` on each machine
3. Use `peers` command to verify discovery
4. Test all features between machines

### Testing Checklist
- [ ] Peer discovery works (`peers` command)
- [ ] Follow/unfollow functionality
- [ ] Post creation and viewing
- [ ] Private messaging
- [ ] File transfer
- [ ] Group creation and messaging
- [ ] Tic Tac Toe game
- [ ] Token validation and revocation
- [ ] Verbose logging

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

#### "No posts received"
- **Cause**: Users haven't followed each other
- **Solution**: Use `follow <user_id>` to follow someone before posting

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

