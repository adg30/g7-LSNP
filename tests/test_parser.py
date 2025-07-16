import unittest
import sys
import os

# Get the absolute path to the .idea directory where our modules are located
idea_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.idea'))
# Insert this directory at the beginning of sys.path so Python finds our modules
sys.path.insert(0, idea_dir)

# --- DIAGNOSTIC PRINT STATEMENTS ---
print(f"Project Root: {os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))}")
print(f"Idea Directory Added to Path: {idea_dir}")
print(f"sys.path: {sys.path}")
# -----------------------------------

# Now, import modules directly since their containing directory is on sys.path
import parser
import utils
import config

class TestParser(unittest.TestCase):

    def setUp(self):
        # Ensure verbose mode is on for testing logs
        config.VERBOSE_MODE = True

    def test_parse_profile_message(self):
        message = """TYPE: PROFILE
USER_ID: test@127.0.0.1
DISPLAY_NAME: TestUser
STATUS: Testing LSNP

"""
        parsed = parser.parse_message(message)
        self.assertIn('TYPE', parsed)
        self.assertEqual(parsed['TYPE'], 'PROFILE')
        self.assertEqual(parsed['USER_ID'], 'test@127.0.0.1')
        self.assertEqual(parsed['DISPLAY_NAME'], 'TestUser')
        self.assertEqual(parsed['STATUS'], 'Testing LSNP')

    def test_parse_message_with_raw_content(self):
        message = """TYPE: FILE_CHUNK
FILEID: 123
CHUNK_INDEX: 0

RAW_DATA_HERE
"""
        parsed = parser.parse_message(message)
        self.assertEqual(parsed['TYPE'], 'FILE_CHUNK')
        self.assertEqual(parsed['RAW_CONTENT'], 'RAW_DATA_HERE')

    def test_parse_malformed_message(self):
        message = """TYPE: PING
USER_ID test@127.0.0.1

""" # Missing colon in USER_ID line
        parsed = parser.parse_message(message)
        self.assertIn('TYPE', parsed)
        self.assertEqual(parsed['TYPE'], 'PING')
        self.assertNotIn('USER_ID', parsed) # Malformed line should be skipped

    def test_format_profile_message(self):
        data = {
            'TYPE': 'PROFILE',
            'USER_ID': 'test@127.0.0.1',
            'DISPLAY_NAME': 'TestUser',
            'STATUS': 'Testing LSNP'
        }
        formatted = parser.format_message(data)
        expected = """TYPE: PROFILE
USER_ID: test@127.0.0.1
DISPLAY_NAME: TestUser
STATUS: Testing LSNP

"""
        self.assertEqual(formatted, expected)

    def test_format_message_with_raw_content(self):
        data = {
            'TYPE': 'FILE_CHUNK',
            'FILEID': '123',
            'CHUNK_INDEX': '0',
            'RAW_CONTENT': 'RAW_DATA_HERE'
        }
        formatted = parser.format_message(data)
        expected = """TYPE: FILE_CHUNK
FILEID: 123
CHUNK_INDEX: 0

RAW_DATA_HERE"""
        self.assertEqual(formatted, expected)

if __name__ == '__main__':
    unittest.main()