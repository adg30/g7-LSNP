#!/usr/bin/env python3
"""
LSNP (Local Social Networking Protocol) Client
A decentralized social networking client for LAN environments.

This is the modular version of the LSNP client, broken down into logical components:
- client.py: Core client functionality
- handlers/: Message handlers for different features
- cli.py: Command line interface
- network.py: Network communication
- peers.py: Peer management
- parser.py: Message parsing
- utils.py: Utility functions
"""

from client import LSNPClient

def main():
    """Main entry point for the LSNP client"""
    try:
        # Create and start the client
        client = LSNPClient()
        client.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
