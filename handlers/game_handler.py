import time
import secrets
import utils
import parser

class GameHandler:
    def __init__(self, client):
        self.client = client
        self.tictactoe_games = {}  # game_id -> {'players': [X, O], 'board': [...], 'turn': X, 'moves': [], 'status': ...}

    def send_tictactoe_invite(self, target_user_id, game_id):
        now = int(time.time())
        ttl_seconds = 3600
        token = f"{self.client.user_id}|{now + ttl_seconds}|game"
        message_id = secrets.token_hex(8)
        msg = parser.format_message({
            'TYPE': 'TICTACTOE_INVITE',
            'FROM': self.client.user_id,
            'TO': target_user_id,
            'GAMEID': game_id,
            'MESSAGE_ID': message_id,
            'SYMBOL': 'X',
            'TIMESTAMP': now,
            'TOKEN': token,
        })
        peer_info = self.client.peer_manager.peers.get(target_user_id)
        if peer_info and peer_info.get('ip_address'):
            dest_ip = peer_info['ip_address']
            self.client.network.send_message(msg, dest_ip=dest_ip)
            utils.log(f"Sent TICTACTOE_INVITE for {game_id} to {target_user_id} via {dest_ip}", level="INFO")

            # Create a local game state for the inviting user
            self.tictactoe_games[game_id] = {
                'players': [self.client.user_id, target_user_id],
                'board': [' '] * 9,
                'turn': self.client.user_id,  # The inviting player goes first
                'moves': [],
                'status': 'pending'  # Waiting for the other player to accept
            }

    def handle_tictactoe_invite(self, parsed, sender_ip):
        game_id = parsed.get('GAMEID') or parsed.get('GAME_ID')  # Support both RFC and legacy format
        from_user = parsed.get('FROM')
        to_user = parsed.get('TO')
        token = parsed.get('TOKEN')
        if to_user != self.client.user_id:
            return
        if not self.client._validate_token_or_log(token, expected_scope='game', expected_user_id=from_user, sender_ip=sender_ip, message_type='TICTACTOE_INVITE'):
            return
        self.tictactoe_games[game_id] = {
            'players': [from_user, self.client.user_id],
            'board': [' '] * 9,
            'turn': from_user,
            'moves': [],
            'status': 'invited'
        }
        display_name = self.client.peer_manager.get_display_name(from_user)
        utils.log_protocol_event("GAME_INVITE_RECEIVED", f"game={game_id} from={display_name}", sender_ip, "TICTACTOE_INVITE")
        print(f"\n🎮 [TICTACTOE] Game invite from {display_name} (game_id: {game_id})")
        print("Commands:")
        print(f"  ttt accept {game_id} - Accept and start the game")
        print(f"  ttt reject {game_id} - Decline the invite")
        print("\n💡 After accepting, use 'ttt move <game_id> <position>' to play!")
        print("   Positions: 0-8 (top-left to bottom-right)")

    def send_tictactoe_accept(self, game_id):
        """Accept a Tic Tac Toe game invite"""
        if game_id not in self.tictactoe_games:
            print(f"Game {game_id} not found")
            return
            
        game = self.tictactoe_games[game_id]
        if game['status'] != 'invited':
            print(f"Game {game_id} is not in invited status")
            return
            
        game['status'] = 'active'
        print(f"Game {game_id} accepted and started!")
        
        # Send acceptance to other player
        now = int(time.time())
        ttl_seconds = 3600
        token = f"{self.client.user_id}|{now + ttl_seconds}|game"
        msg = parser.format_message({
            'TYPE': 'TICTACTOE_ACCEPT',
            'GAMEID': game_id,
            'FROM': self.client.user_id,
            'TIMESTAMP': now,
            'TOKEN': token,
        })
        
        other_player = [p for p in game['players'] if p != self.client.user_id][0]
        peer_info = self.client.peer_manager.peers.get(other_player)
        if peer_info and peer_info.get('ip_address'):
            dest_ip = peer_info['ip_address']
            self.client.network.send_message(msg, dest_ip=dest_ip)
            utils.log(f"Sent TICTACTOE_ACCEPT for {game_id} to {other_player}", level="INFO")

    def send_tictactoe_reject(self, game_id):
        """Reject a Tic Tac Toe game invite"""
        if game_id not in self.tictactoe_games:
            print(f"Game {game_id} not found")
            return
            
        game = self.tictactoe_games[game_id]
        if game['status'] != 'invited':
            print(f"Game {game_id} is not in invited status")
            return
            
        # Send rejection to other player
        now = int(time.time())
        ttl_seconds = 3600
        token = f"{self.client.user_id}|{now + ttl_seconds}|game"
        msg = parser.format_message({
            'TYPE': 'TICTACTOE_REJECT',
            'GAMEID': game_id,  
            'FROM': self.client.user_id,
            'TO': self._get_other_player(game_id),  
            'TIMESTAMP': now,
            'TOKEN': token,
        })
        
        other_player = self._get_other_player(game_id)
        peer_info = self.client.peer_manager.peers.get(other_player)
        if peer_info and peer_info.get('ip_address'):
            dest_ip = peer_info['ip_address']
            self.client.network.send_message(msg, dest_ip=dest_ip)
            utils.log(f"Sent TICTACTOE_REJECT for {game_id} to {other_player}", level="INFO")
            print(f"Rejection sent to {self.client.peer_manager.get_display_name(other_player)}")
        else:
            print(f"Warning: Could not send rejection - {other_player} not found")
        
        # Remove from our list
        del self.tictactoe_games[game_id]
        print(f"Game {game_id} rejected and removed")

    def send_tictactoe_move(self, game_id, position):
        # First, validate the move locally
        if game_id not in self.tictactoe_games:
            print(f"Game {game_id} not found")
            return False
            
        game = self.tictactoe_games[game_id]
        
        # Check if game is finished
        if game.get('status') == 'finished':
            print(f"Game {game_id} has already ended. No more moves allowed.")
            return False
        
        # Check if it's our turn
        if not game.get('turn') or game['turn'] != self.client.user_id:
            if game.get('turn'):
                print(f"It's not your turn. Current turn: {self.client.peer_manager.get_display_name(game['turn'])}")
            else:
                print(f"Game {game_id} has no active turn (game may be finished)")
            return False
            
        # Check if position is valid and empty
        try:
            position = int(position)
            if not (0 <= position <= 8):
                print("Position must be 0-8")
                return False
            if game['board'][position] != ' ':
                print(f"Position {position} is already occupied")
                return False
        except (ValueError, TypeError):
            print("Position must be a number 0-8")
            return False
        
        # Make the move locally first
        game['board'][position] = self._get_player_symbol(game_id)
        game['moves'].append((self.client.user_id, position))
        
        # Display the updated board BEFORE checking for win
        self._display_game_board(game_id)
        
        # Check for game result BEFORE switching turns
        result = self._check_game_result(game_id)
        if result:
            print(f"\n🎮 Game Over! {result}")
            
            # Mark game as finished
            game['status'] = 'finished'
            game['turn'] = None  # Clear turn since game is over
            
            # Send result to other player
            self.send_tictactoe_result(game_id, result)
            return True
        
        # Only switch turns if game continues
        game['turn'] = self._get_other_player(game_id)
        
        # Send the move to the other player
        now = int(time.time())
        ttl_seconds = 3600
        token = f"{self.client.user_id}|{now + ttl_seconds}|game"
        message_id = secrets.token_hex(8)
        msg = parser.format_message({
            'TYPE': 'TICTACTOE_MOVE',
            'FROM': self.client.user_id,
            'TO': self._get_other_player(game_id),
            'GAMEID': game_id,
            'MESSAGE_ID': message_id,
            'POSITION': position,
            'SYMBOL': self._get_player_symbol(game_id),
            'TURN': len(game['moves']),
            'TIMESTAMP': now,
            'TOKEN': token,
        })
        
        other_player = self._get_other_player(game_id)
        peer_info = self.client.peer_manager.peers.get(other_player)
        if peer_info and peer_info.get('ip_address'):
            dest_ip = peer_info['ip_address']
            self.client.network.send_message(msg, dest_ip=dest_ip)
            utils.log(f"Sent TICTACTOE_MOVE for {game_id} to {other_player} via {dest_ip}", level="INFO")
            print(f"\n➡️ Waiting for {self.client.peer_manager.get_display_name(other_player)}'s move...")
            return True
        else:
            print(f"Cannot send move - no known IP for {other_player}")
            return False

    def handle_tictactoe_move(self, parsed, sender_ip):
        """Handle TICTACTOE_MOVE message from other player"""
        game_id = parsed.get('GAMEID')
        from_user = parsed.get('FROM')
        position = parsed.get('POSITION')
        symbol = parsed.get('SYMBOL')
        turn = parsed.get('TURN')
        token = parsed.get('TOKEN')
        message_id = parsed.get('MESSAGE_ID')
        
        if game_id not in self.tictactoe_games:
            utils.log(f"Received move for unknown game {game_id} from {from_user}", level="WARN")
            return
            
        if not self.client._validate_token_or_log(token, expected_scope='game', expected_user_id=from_user, sender_ip=sender_ip, message_type='TICTACTOE_MOVE'):
            return
            
        game = self.tictactoe_games[game_id]
        
        # Check if game is already finished
        if game.get('status') == 'finished':
            utils.log(f"Ignoring move for finished game {game_id}", level="WARN")
            return
        
        # Check if it's the other player's turn
        if game['turn'] != from_user:
            utils.log(f"Move from {from_user} ignored - not their turn (current turn: {game['turn']})", level="WARN")
            return
            
        # Check if position is valid and empty
        try:
            position = int(position)
            if not (0 <= position <= 8):
                utils.log(f"Invalid position {position} from {from_user}", level="WARN")
                return
            if game['board'][position] != ' ':
                utils.log(f"Position {position} already occupied by {from_user}", level="WARN")
                return
        except (ValueError, TypeError):
            utils.log(f"Invalid position format {position} from {from_user}", level="WARN")
            return
            
        # Make the move
        game['board'][position] = 'X' if from_user == game['players'][0] else 'O'
        game['moves'].append((from_user, position))
        
        # Display updated board
        print(f"\n🎮 {self.client.peer_manager.get_display_name(from_user)} made a move!")
        self._display_game_board(game_id)

        # Send ACK for the move
        if message_id:
            self.client.send_ack(message_id, sender_ip)
        
        # Check for game result BEFORE switching turns
        result = self._check_game_result(game_id)
        
        if result:
            # Game ended
            print(f"\n🎮 Game Over! {result}")
            game['status'] = 'finished'
            game['turn'] = None  # Clear turn since game is over
            # The move sender should have already sent the result
        else:
            # Game continues - switch turns to us
            game['turn'] = self.client.user_id
            print(f"\n➡️ It's your turn! Use: ttt move {game_id} <position>")

    def _check_game_result(self, game_id):
        """Check if the game has a winner or is a draw"""
        game = self.tictactoe_games[game_id]
        board = game['board']
        
        # Check rows
        for i in range(0, 9, 3):
            if board[i] == board[i+1] == board[i+2] != ' ':
                return f"{board[i]} wins (row)"
                
        # Check columns
        for i in range(3):
            if board[i] == board[i+3] == board[i+6] != ' ':
                return f"{board[i]} wins (column)"
                
        # Check diagonals
        if board[0] == board[4] == board[8] != ' ':
            return f"{board[0]} wins (diagonal)"
        if board[2] == board[4] == board[6] != ' ':
            return f"{board[2]} wins (diagonal)"
            
        # Check for draw (all positions filled)
        if len(game['moves']) == 9:
            return "Draw"
            
        return None  # Game continues

    def send_tictactoe_result(self, game_id, result):
        now = int(time.time())
        ttl_seconds = 3600
        token = f"{self.client.user_id}|{now + ttl_seconds}|game"
        message_id = secrets.token_hex(8)
        msg = parser.format_message({
            'TYPE': 'TICTACTOE_RESULT',
            'GAMEID': game_id,
            'FROM': self.client.user_id,
            'RESULT': result,
            'SYMBOL': self._get_player_symbol(game_id),
            'MESSAGE_ID': message_id,
            'TIMESTAMP': now,
            'TOKEN': token,
        })
        players = self.tictactoe_games.get(game_id, {}).get('players', [])
        for player in players:
            if player == self.client.user_id:
                continue
            peer_info = self.client.peer_manager.peers.get(player)
            if peer_info and peer_info.get('ip_address'):
                dest_ip = peer_info['ip_address']
                self.client.network.send_message(msg, dest_ip=dest_ip)
                utils.log(f"Sent TICTACTOE_RESULT for {game_id} to {player} via {dest_ip}", level="INFO")

    def handle_tictactoe_result(self, parsed, sender_ip):
        game_id = parsed.get('GAMEID')
        from_user = parsed.get('FROM')
        result = parsed.get('RESULT')
        token = parsed.get('TOKEN')
        
        if game_id not in self.tictactoe_games:
            return
            
        if not self.client._validate_token_or_log(token, expected_scope='game', expected_user_id=from_user, sender_ip=sender_ip, message_type='TICTACTOE_RESULT'):
            return
        
        # Update the game state to show the final result
        game = self.tictactoe_games[game_id]
        game['status'] = 'finished'
        game['turn'] = None  # Clear turn since game is over
        
        utils.log(f"Game {game_id} finished: {result}", level="INFO")
        print(f"\n[TICTACTOE:{game_id}] Game finished: {result}")
        
        # Show the final board state
        self._display_game_board(game_id)

    def handle_tictactoe_accept(self, parsed, sender_ip):
        """Handle TICTACTOE_ACCEPT message"""
        game_id = parsed.get('GAME_ID')
        from_user = parsed.get('FROM')
        token = parsed.get('TOKEN')
        if game_id not in self.tictactoe_games:
            return
        if not self.client._validate_token_or_log(token, expected_scope='game', expected_user_id=from_user, sender_ip=sender_ip, message_type='TICTACTOE_ACCEPT'):
            return
        self.tictactoe_games[game_id]['status'] = 'active'
        display_name = self.client.peer_manager.get_display_name(from_user)
        print(f"\n[TICTACTOE:{game_id}] {display_name} accepted the game invite!")
        print(f"[TICTACTOE:{game_id}] Game started! It's your turn to make the first move.")
        # Display the initial board
        self._display_game_board(game_id)

    def handle_tictactoe_reject(self, parsed, sender_ip):
        """Handle TICTACTOE_REJECT message - INVITER receives this"""
        game_id = parsed.get('GAMEID')
        from_user = parsed.get('FROM')
        token = parsed.get('TOKEN')
        
        # Debug logging
        utils.log(f"Received TICTACTOE_REJECT for game {game_id} from {from_user}", level="DEBUG")
        
        if game_id not in self.tictactoe_games:
            utils.log(f"Game {game_id} not found in local games", level="WARN")
            return
            
        if not self.client._validate_token_or_log(token, expected_scope='game', expected_user_id=from_user, sender_ip=sender_ip, message_type='TICTACTOE_REJECT'):
            return
            
        display_name = self.client.peer_manager.get_display_name(from_user)
        print(f"\n[TICTACTOE:{game_id}] {display_name} rejected the game invite.")
        
        # Remove the game from inviter's list
        if game_id in self.tictactoe_games:
            del self.tictactoe_games[game_id]
            utils.log(f"Removed rejected game {game_id} from local games", level="INFO")
            print(f"Game {game_id} removed from your games list.")
    def _get_other_player(self, game_id):
        """Get the other player's user ID in a game"""
        if game_id not in self.tictactoe_games:
            return None
        players = self.tictactoe_games[game_id]['players']
        return players[1] if players[0] == self.client.user_id else players[0]
    
    def _get_player_symbol(self, game_id):
        """Get the current player's symbol (X or O)"""
        if game_id not in self.tictactoe_games:
            return 'X'
        players = self.tictactoe_games[game_id]['players']
        return 'X' if players[0] == self.client.user_id else 'O'

    def _display_game_board(self, game_id):
        """Display the Tic Tac Toe board with enhanced information"""
        if game_id not in self.tictactoe_games:
            print(f"Game {game_id} not found")
            return
            
        game = self.tictactoe_games[game_id]
        board = game['board']
        
        print(f"\n🎮 Tic Tac Toe Board ({game_id})")
        print(f"Status: {game['status'].upper()}")
        
        # Only show current turn if game is active AND has a valid turn
        if game['status'] == 'active' and game.get('turn'):
            current_player = self.client.peer_manager.get_display_name(game['turn'])
            print(f"Current Turn: {current_player}")
        elif game['status'] == 'finished':
            print("Game has ended!")
        
        # Display the board
        print("\nCurrent Board:")
        for i in range(0, 9, 3):
            row = [cell if cell != ' ' else '_' for cell in board[i:i+3]]
            print(f" {row[0]} | {row[1]} | {row[2]} ")
            if i < 6:
                print("---+---+---")
        
        # Show move history
        if game['moves']:
            print(f"\n📝 Move History ({len(game['moves'])} moves):")
            for i, (player, pos) in enumerate(game['moves'], 1):
                player_name = self.client.peer_manager.get_display_name(player)
                symbol = 'X' if player == game['players'][0] else 'O'
                print(f"  {i}. {player_name} ({symbol}) → position {pos}")
        
        # Show available positions and commands ONLY if game is active
        if game['status'] == 'active':
            available = [i for i, cell in enumerate(board) if cell == ' ']
            if available:
                print(f"\n📍 Available positions: {', '.join(map(str, available))}")
            
            # Only show move commands if it's the player's turn
            if game.get('turn') == self.client.user_id:
                print(f"\n💡 Your turn! Commands:")
                print(f"  ttt move {game_id} <position> - Make a move")
            elif game.get('turn'):
                current_player = self.client.peer_manager.get_display_name(game['turn'])
                print(f"\n⏳ Waiting for {current_player}'s move...")
        elif game['status'] == 'finished':
            print(f"\n🏁 This game has ended. Use 'ttt list' to see all games.")
        
        # Always show board command
        print(f"  ttt board {game_id} - Show this board again")
