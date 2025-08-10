#!/usr/bin/env python3
"""
LSNP Protocol Compliance Test Suite - Enhanced with File Transfer
CLI tool for crafting, parsing, and simulating LSNP messages
"""

# THIS IS JUST FOR TESTING PURPOSES

import sys
import time
import secrets
import parser
import utils
import config

class LSNPTestSuite:
    def __init__(self):
        self.test_messages = {
            # Original message types
            "PING": {
                "TYPE": "PING",
                "USER_ID": "test@192.168.1.100"
            },
            "PROFILE": {
                "TYPE": "PROFILE", 
                "USER_ID": "john@192.168.1.100",
                "DISPLAY_NAME": "John Doe",
                "STATUS": "Available for chat"
            },
            "POST": {
                "TYPE": "POST",
                "USER_ID": "alice@192.168.1.101", 
                "CONTENT": "Hello everyone!",
                "TIMESTAMP": str(int(time.time()))
            },
            "DM": {
                "TYPE": "DM",
                "FROM": "bob@192.168.1.102",
                "TO": "alice@192.168.1.101",
                "CONTENT": "Hey Alice!",
                "TIMESTAMP": str(int(time.time()))
            },
            
            # File transfer message types
            "FILE_OFFER": {
                "TYPE": "FILE_OFFER",
                "FROM": "alice@192.168.1.101",
                "TO": "bob@192.168.1.102",
                "FILE_ID": "alice_document_1691234567_abc123",
                "FILENAME": "document.pdf",
                "FILESIZE": "1048576",  # 1MB
                "FILEHASH": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "MESSAGE_ID": secrets.token_hex(8),
                "TIMESTAMP": str(int(time.time())),
                "TOKEN": f"alice@192.168.1.101|{int(time.time()) + 3600}|file"
            },
            "FILE_REQUEST": {
                "TYPE": "FILE_REQUEST",
                "FROM": "bob@192.168.1.102",
                "TO": "alice@192.168.1.101",
                "FILE_ID": "alice_document_1691234567_abc123",
                "TIMESTAMP": str(int(time.time())),
                "TOKEN": f"bob@192.168.1.102|{int(time.time()) + 3600}|file"
            },
            "FILE_REJECT": {
                "TYPE": "FILE_REJECT",
                "FROM": "bob@192.168.1.102",
                "TO": "alice@192.168.1.101",
                "FILE_ID": "alice_document_1691234567_abc123",
                "TIMESTAMP": str(int(time.time())),
                "TOKEN": f"bob@192.168.1.102|{int(time.time()) + 3600}|file"
            },
            "FILE_CHUNK": {
                "TYPE": "FILE_CHUNK",
                "FROM": "alice@192.168.1.101",
                "TO": "bob@192.168.1.102",
                "FILE_ID": "alice_document_1691234567_abc123",
                "CHUNK_INDEX": "0",
                "TOTAL_CHUNKS": "1024",
                "CHUNK_SIZE": "1024",
                "TIMESTAMP": str(int(time.time())),
                "TOKEN": f"alice@192.168.1.101|{int(time.time()) + 3600}|file",
                "DATA": utils.base64_encode(b"Sample chunk data for testing...")
            },
            "FILE_RECEIVED": {
                "TYPE": "FILE_RECEIVED",
                "FROM": "bob@192.168.1.102",
                "TO": "alice@192.168.1.101",
                "FILE_ID": "alice_document_1691234567_abc123",
                "TIMESTAMP": str(int(time.time())),
                "TOKEN": f"bob@192.168.1.102|{int(time.time()) + 3600}|file"
            },
            "CHUNK_REQUEST": {
                "TYPE": "CHUNK_REQUEST",
                "FROM": "bob@192.168.1.102",
                "TO": "alice@192.168.1.101",
                "FILE_ID": "alice_document_1691234567_abc123",
                "MISSING_CHUNKS": "5,12,47,128",
                "TIMESTAMP": str(int(time.time())),
                "TOKEN": f"bob@192.168.1.102|{int(time.time()) + 3600}|file"
            },
            
            # Game message types
            "TICTACTOE_INVITE": {
                "TYPE": "TICTACTOE_INVITE",
                "FROM": "alice@192.168.1.101",
                "TO": "bob@192.168.1.102",
                "GAMEID": "alice_tictactoe_1691234567",
                "MESSAGE_ID": secrets.token_hex(8),
                "SYMBOL": "X",
                "TIMESTAMP": str(int(time.time())),
                "TOKEN": f"alice@192.168.1.101|{int(time.time()) + 3600}|game"
            },
            "TICTACTOE_ACCEPT": {
                "TYPE": "TICTACTOE_ACCEPT",
                "GAME_ID": "alice_tictactoe_1691234567",
                "FROM": "bob@192.168.1.102",
                "TIMESTAMP": str(int(time.time())),
                "TOKEN": f"bob@192.168.1.102|{int(time.time()) + 3600}|game"
            },
            "TICTACTOE_MOVE": {
                "TYPE": "TICTACTOE_MOVE",
                "FROM": "alice@192.168.1.101",
                "TO": "bob@192.168.1.102",
                "GAMEID": "alice_tictactoe_1691234567",
                "MESSAGE_ID": secrets.token_hex(8),
                "POSITION": "4",  # Center position
                "SYMBOL": "X",
                "TURN": "1",
                "TIMESTAMP": str(int(time.time())),
                "TOKEN": f"alice@192.168.1.101|{int(time.time()) + 3600}|game"
            },
            "TICTACTOE_RESULT": {
                "TYPE": "TICTACTOE_RESULT",
                "GAME_ID": "alice_tictactoe_1691234567",
                "FROM": "alice@192.168.1.101",
                "RESULT": "X wins (row)",
                "TIMESTAMP": str(int(time.time())),
                "TOKEN": f"alice@192.168.1.101|{int(time.time()) + 3600}|game"
            }
        }
        
        # Group message types by category
        self.message_categories = {
            "Basic": ["PING", "PROFILE", "POST", "DM"],
            "File Transfer": ["FILE_OFFER", "FILE_REQUEST", "FILE_REJECT", "FILE_CHUNK", "FILE_RECEIVED", "CHUNK_REQUEST"],
            "Games": ["TICTACTOE_INVITE", "TICTACTOE_ACCEPT", "TICTACTOE_MOVE", "TICTACTOE_RESULT"]
        }
    
    def toggle_verbose(self):
        """Toggle verbose mode on/off"""
        config.VERBOSE_MODE = not config.VERBOSE_MODE
        status = "ON" if config.VERBOSE_MODE else "OFF"
        print(f"Verbose mode: {status}")
    
    def list_message_types(self):
        """List all available message types by category"""
        print("\n=== AVAILABLE MESSAGE TYPES ===")
        for category, types in self.message_categories.items():
            print(f"\n{category}:")
            for msg_type in types:
                print(f"  - {msg_type}")
        print("\nTotal:", len(self.test_messages))
    
    def craft_message(self, msg_type):
        """Craft a sample LSNP message"""
        if msg_type.upper() not in self.test_messages:
            print(f"❌ Unknown message type: {msg_type}")
            print("💡 Use 'list' to see available types")
            return None
        
        message_data = self.test_messages[msg_type.upper()].copy()
        formatted = parser.format_message(message_data)
        
        print(f"\n=== CRAFTED {msg_type.upper()} MESSAGE ===")
        print(formatted)
        print("=" * 50)
        return formatted
    
    def craft_custom_message(self):
        """Interactive message crafting"""
        print("\n=== CUSTOM MESSAGE BUILDER ===")
        
        msg_type = input("Message TYPE: ").strip()
        if not msg_type:
            print("❌ Message type is required")
            return None
            
        message_data = {"TYPE": msg_type.upper()}
        
        print("Enter fields (press Enter with empty value to finish):")
        while True:
            field = input("Field name: ").strip()
            if not field:
                break
            value = input(f"{field} value: ").strip()
            if value:
                message_data[field] = value
        
        try:
            formatted = parser.format_message(message_data)
            print(f"\n=== CUSTOM {msg_type.upper()} MESSAGE ===")
            print(formatted)
            print("=" * 50)
            return formatted
        except Exception as e:
            print(f"❌ Error formatting message: {e}")
            return None
    
    def parse_test(self, message_text):
        """Parse and validate a message"""
        print(f"\n=== PARSING TEST ===")
        print(f"Input:\n{message_text}")
        
        original_verbose = config.VERBOSE_MODE
        config.VERBOSE_MODE = False

        parsed = parser.parse_message(message_text)

        config.VERBOSE_MODE = original_verbose
        
        print(f"\nParsed Result:")
        if parsed:
            for key, value in parsed.items():
                # Truncate long values for readability
                display_value = value
                if isinstance(value, str) and len(value) > 100:
                    display_value = value[:97] + "..."
                print(f"  {key}: {display_value}")
            print("✅ Parsing successful")
        else:
            print("❌ Parsing failed")
        
        print("=" * 50)
        return parsed
    
    def simulate_file_transfer(self):
        """Simulate a complete file transfer scenario"""
        print("\n=== SIMULATING FILE TRANSFER SCENARIO ===")
        
        print("\n1. File Offer:")
        offer = self.craft_message("FILE_OFFER")
        
        print("\n2. File Accept (Request):")
        request = self.craft_message("FILE_REQUEST")
        
        print("\n3. File Chunk Transfer:")
        chunk = self.craft_message("FILE_CHUNK")
        
        print("\n4. Missing Chunk Request:")
        chunk_req = self.craft_message("CHUNK_REQUEST")
        
        print("\n5. Transfer Completion:")
        received = self.craft_message("FILE_RECEIVED")
        
        print("\n=== FILE TRANSFER SIMULATION COMPLETE ===")
    
    def simulate_game_session(self):
        """Simulate a Tic Tac Toe game scenario"""
        print("\n=== SIMULATING TIC TAC TOE GAME ===")
        
        print("\n1. Game Invitation:")
        invite = self.craft_message("TICTACTOE_INVITE")
        
        print("\n2. Game Acceptance:")
        accept = self.craft_message("TICTACTOE_ACCEPT")
        
        print("\n3. Game Move:")
        move = self.craft_message("TICTACTOE_MOVE")
        
        print("\n4. Game Result:")
        result = self.craft_message("TICTACTOE_RESULT")
        
        print("\n=== GAME SIMULATION COMPLETE ===")
    
    def simulate_conversation(self):
        """Simulate basic LSNP protocol interaction"""
        print("\n=== SIMULATING BASIC CONVERSATION ===")
        
        print("\n1. Peer Discovery:")
        ping = self.craft_message("PING")
        profile = self.craft_message("PROFILE")
        
        print("\n2. Social Interaction:")
        post = self.craft_message("POST") 
        dm = self.craft_message("DM")
        
        print("\n=== BASIC SIMULATION COMPLETE ===")
    
    def run_category_tests(self, category):
        """Run tests for a specific category"""
        if category not in self.message_categories:
            print(f"❌ Unknown category: {category}")
            print("Available categories:", list(self.message_categories.keys()))
            return
            
        types = self.message_categories[category]
        print(f"\n=== TESTING {category.upper()} MESSAGES ===")
        
        passed = 0
        total = len(types)
        
        for msg_type in types:
            print(f"\nTesting {msg_type}...")
            
            # Test crafting
            crafted = self.craft_message(msg_type)
            if not crafted:
                print(f"❌ {msg_type} crafting failed")
                continue
            
            # Test parsing
            parsed = self.parse_test(crafted)
            if parsed and parsed.get('TYPE') == msg_type:
                print(f"✅ {msg_type} test passed")
                passed += 1
            else:
                print(f"❌ {msg_type} test failed")
        
        print(f"\n=== {category.upper()} TEST RESULTS ===")
        print(f"Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    def run_all_tests(self):
        """Run comprehensive protocol tests"""
        print("\n=== RUNNING ALL PROTOCOL TESTS ===")
        
        passed = 0
        total = 0
        
        for category, types in self.message_categories.items():
            print(f"\n--- Testing {category} ---")
            category_passed = 0
            
            for msg_type in types:
                total += 1
                
                # Test crafting
                crafted = self.craft_message(msg_type)
                if not crafted:
                    print(f"❌ {msg_type} crafting failed")
                    continue
                
                # Test parsing
                parsed = self.parse_test(crafted)
                if parsed and parsed.get('TYPE') == msg_type:
                    passed += 1
                    category_passed += 1
                    print(f"✅ {msg_type} OK")
                else:
                    print(f"❌ {msg_type} FAILED")
            
            print(f"{category} Results: {category_passed}/{len(types)} passed")
        
        print(f"\n=== FINAL TEST RESULTS ===")
        print(f"Total Passed: {passed}/{total}")
        print(f"Overall Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED!")
        elif passed >= total * 0.8:
            print("⚠️  Most tests passed - check failures above")
        else:
            print("❌ Many tests failed - protocol compliance issues detected")
    
    def benchmark_parsing(self):
        """Benchmark message parsing performance"""
        print("\n=== PARSING BENCHMARK ===")
        import time as perf_time
        
        iterations = 1000
        total_time = 0
        
        # Test with a representative message
        test_msg = self.craft_message("FILE_CHUNK")
        
        print(f"Benchmarking {iterations} parse operations...")
        
        start_time = perf_time.time()
        for _ in range(iterations):
            parser.parse_message(test_msg)
        end_time = perf_time.time()
        
        total_time = end_time - start_time
        avg_time = (total_time / iterations) * 1000  # Convert to milliseconds
        
        print(f"Total time: {total_time:.3f}s")
        print(f"Average time per parse: {avg_time:.3f}ms")
        print(f"Throughput: {iterations/total_time:.0f} messages/second")
    
    def interactive_cli(self):
        """Interactive test mode"""
        print("\n=== LSNP PROTOCOL TEST SUITE - ENHANCED ===")
        print("Commands:")
        print("  craft <type>      - Create sample message")
        print("  custom            - Build custom message")
        print("  parse <msg>       - Parse message text")  
        print("  list              - List all message types")
        print("  simulate          - Run basic conversation simulation")
        print("  sim-file          - Simulate file transfer")
        print("  sim-game          - Simulate tic-tac-toe game")
        print("  test-all          - Run all protocol tests")
        print("  test <category>   - Test specific category")
        print("  benchmark         - Benchmark parsing performance")
        print("  verbose           - Toggle verbose mode")
        print("  help              - Show this help")
        print("  exit              - Exit test suite")
        
        while True:
            try:
                cmd = input("\nLSNP-TEST> ").strip().split(' ', 1)
                
                if not cmd or not cmd[0]:
                    continue
                
                command = cmd[0].lower()
                
                if command == "exit":
                    print("👋 Goodbye!")
                    break
                elif command == "help":
                    print("Available commands:")
                    print("  craft, custom, parse, list, simulate, sim-file, sim-game")
                    print("  test-all, test, benchmark, verbose, help, exit")
                elif command == "list":
                    self.list_message_types()
                elif command == "craft":
                    if len(cmd) > 1:
                        self.craft_message(cmd[1])
                    else:
                        print("Usage: craft <message_type>")
                        print("💡 Use 'list' to see available types")
                elif command == "custom":
                    self.craft_custom_message()
                elif command == "parse":
                    if len(cmd) > 1:
                        self.parse_test(cmd[1])
                    else:
                        print("Usage: parse <message_text>")
                elif command == "simulate":
                    self.simulate_conversation()
                elif command == "sim-file":
                    self.simulate_file_transfer()
                elif command == "sim-game":
                    self.simulate_game_session()
                elif command == "test-all":
                    self.run_all_tests()
                elif command == "test":
                    if len(cmd) > 1:
                        self.run_category_tests(cmd[1])
                    else:
                        print("Usage: test <category>")
                        print("Categories:", list(self.message_categories.keys()))
                elif command == "benchmark":
                    self.benchmark_parsing()
                elif command == "verbose":
                    self.toggle_verbose()
                else:
                    print(f"❌ Unknown command: {command}. Type 'help' for options.")
            
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    """Main entry point"""
    test_suite = LSNPTestSuite()
    
    if len(sys.argv) > 1:
        # Command line mode
        command = sys.argv[1].lower()
        if command == 'craft' and len(sys.argv) > 2:
            test_suite.craft_message(sys.argv[2])
        elif command == 'simulate':
            test_suite.simulate_conversation()
        elif command == 'sim-file':
            test_suite.simulate_file_transfer()
        elif command == 'sim-game':
            test_suite.simulate_game_session()
        elif command == 'test-all':
            test_suite.run_all_tests()
        elif command == 'test' and len(sys.argv) > 2:
            test_suite.run_category_tests(sys.argv[2])
        elif command == 'list':
            test_suite.list_message_types()
        elif command == 'benchmark':
            test_suite.benchmark_parsing()
        elif command == 'verbose':
            test_suite.toggle_verbose()
        else:
            print("Usage: python cli_test.py [craft <type>|simulate|sim-file|sim-game|test-all|test <category>|list|benchmark|verbose]")
    else:
        # Interactive mode
        test_suite.interactive_cli()

if __name__ == "__main__":
    main()