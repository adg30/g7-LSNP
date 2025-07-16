#!/usr/bin/env python3
"""
LSNP Protocol Compliance Test Suite - Milestone 1
CLI tool for crafting, parsing, and simulating LSNP messages
"""

# THIS IS JUST FOR TESTING PURPOSES

import sys
import time
import parser
import utils
import config

class LSNPTestSuite:
    def __init__(self):
        self.test_messages = {
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
            }
        }
    
    def toggle_verbose(self):
        """Toggle verbose mode on/off"""
        config.VERBOSE_MODE = not config.VERBOSE_MODE
        status = "ON" if config.VERBOSE_MODE else "OFF"
        print(f"Verbose mode: {status}")
    
    def craft_message(self, msg_type):
        """Craft a sample LSNP message"""
        if msg_type.upper() not in self.test_messages:
            print(f"Unknown message type: {msg_type}")
            print("Available types:", list(self.test_messages.keys()))
            return None
        
        message_data = self.test_messages[msg_type.upper()].copy()
        formatted = parser.format_message(message_data)
        
        print(f"\n=== CRAFTED {msg_type.upper()} MESSAGE ===")
        print(formatted)
        print("=" * 50)
        return formatted
    
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
                print(f"  {key}: {value}")
            print("✅ Parsing successful")
        else:
            print("❌ Parsing failed")
        
        print("=" * 50)
        return parsed
    
    def simulate_conversation(self):
        """Simulate LSNP protocol interaction"""
        print("\n=== SIMULATING LSNP CONVERSATION ===")
        
        print("\n1. Peer Discovery:")
        ping = self.craft_message("PING")
        profile = self.craft_message("PROFILE")
        
        print("\n2. Social Interaction:")
        post = self.craft_message("POST") 
        dm = self.craft_message("DM")
        
        print("\n=== SIMULATION COMPLETE ===")
    
    def run_all_tests(self):
        """Run comprehensive protocol tests"""
        print("\n=== RUNNING ALL PROTOCOL TESTS ===")
        
        passed = 0
        total = 0
        
        for msg_type in self.test_messages.keys():
            print(f"\nTesting {msg_type}...")
            total += 1
            
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
        
        print(f"\n=== TEST RESULTS ===")
        print(f"Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    def interactive_cli(self):
        """Interactive test mode"""
        print("\n=== LSNP PROTOCOL TEST SUITE ===")
        print("Commands:")
        print("  craft <type>     - Create sample message")
        print("  parse <msg>      - Parse message text")  
        print("  simulate         - Run conversation simulation")
        print("  test-all         - Run all protocol tests")
        print("  verbose          - Toggle verbose mode")
        print("  help             - Show this help")
        print("  exit             - Exit test suite")
        
        while True:
            try:
                cmd = input("\nTEST> ").strip().split(' ', 1)
                
                if not cmd or not cmd[0]:
                    continue
                
                command = cmd[0].lower()
                
                if command == "exit":
                    print("Goodbye!")
                    break
                elif command == "help":
                    print("Available commands:")
                    print("  craft <type>, parse <msg>, simulate, test-all, verbose, exit")
                elif command == "craft":
                    if len(cmd) > 1:
                        self.craft_message(cmd[1])
                    else:
                        print("Usage: craft <message_type>")
                        print("Available:", list(self.test_messages.keys()))
                elif command == "parse":
                    if len(cmd) > 1:
                        self.parse_test(cmd[1])
                    else:
                        print("Usage: parse <message_text>")
                elif command == "simulate":
                    self.simulate_conversation()
                elif command == "test-all":
                    self.run_all_tests()
                elif command == "verbose":
                    self.toggle_verbose()
                else:
                    print(f"Unknown command: {command}. Type 'help' for options.")
            
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")

def main():
    """Main entry point"""
    test_suite = LSNPTestSuite()
    
    if len(sys.argv) > 1:
        # Command line mode
        command = sys.argv[1].lower()
        if command in ['craft', 'simulate', 'test-all', 'verbose']:
            if command == 'craft' and len(sys.argv) > 2:
                test_suite.craft_message(sys.argv[2])
            elif command == 'simulate':
                test_suite.simulate_conversation()
            elif command == 'test-all':
                test_suite.run_all_tests()
            elif command == 'verbose':
                test_suite.toggle_verbose()
        else:
            print("Usage: python cli_test.py [craft|simulate|test-all|verbose]")
    else:
        # Interactive mode
        test_suite.interactive_cli()

if __name__ == "__main__":
    main()