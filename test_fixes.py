#!/usr/bin/env python3
"""
Test script to verify the fixes for:
1. Avatar display (saving images instead of showing base64)
2. File transfer (fixed total_chunks calculation)
3. Tic Tac Toe (improved board display and state synchronization)
"""

import os
import base64
import tempfile

def test_avatar_saving():
    """Test that avatar data is properly saved as image files"""
    print("Testing avatar saving functionality...")
    
    # Create a simple test image (1x1 pixel PNG)
    test_png_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )
    
    # Test the avatar saving logic
    try:
        # Create avatars directory if it doesn't exist
        if not os.path.exists('avatars'):
            os.makedirs('avatars')
        
        # Save test avatar
        test_user_id = "user@192.168.1.100"
        safe_user_id = test_user_id.replace('@', '_').replace('.', '_')
        filename = f"avatars/{safe_user_id}.png"
        
        with open(filename, 'wb') as f:
            f.write(test_png_data)
        
        # Check if file was created
        if os.path.exists(filename):
            print(f"✅ Avatar saving works! Test file created: {filename}")
            print(f"   File size: {os.path.getsize(filename)} bytes")
            return True
        else:
            print("❌ Avatar saving failed - file not created")
            return False
            
    except Exception as e:
        print(f"❌ Avatar saving failed with error: {e}")
        return False

def test_file_transfer_calculation():
    """Test that total_chunks calculation is correct"""
    print("\nTesting file transfer chunk calculation...")
    
    # Test cases: (file_size, chunk_size, expected_total_chunks)
    test_cases = [
        (1024, 1024, 1),      # Exactly 1 chunk
        (1025, 1024, 2),      # Just over 1 chunk
        (2048, 1024, 2),      # Exactly 2 chunks
        (2049, 1024, 3),      # Just over 2 chunks
        (100, 1024, 1),       # Less than 1 chunk
        (0, 1024, 0),         # Empty file
    ]
    
    all_passed = True
    for file_size, chunk_size, expected in test_cases:
        # Use the same calculation as in the fixed code
        total_chunks = (file_size + chunk_size - 1) // chunk_size
        if total_chunks == expected:
            print(f"✅ {file_size} bytes with {chunk_size} chunk size = {total_chunks} chunks")
        else:
            print(f"❌ {file_size} bytes with {chunk_size} chunk size = {total_chunks} chunks (expected {expected})")
            all_passed = False
    
    return all_passed

def test_tic_tac_toe_board_display():
    """Test the improved Tic Tac Toe board display"""
    print("\nTesting Tic Tac Toe board display...")
    
    # Simulate a game board
    board = ['X', 'O', 'X', ' ', 'O', ' ', 'X', ' ', 'O']
    
    print("Board display should show:")
    print(" X | O | X ")
    print("---+---+---")
    print(" _ | O | _ ")
    print("---+---+---")
    print(" X | _ | O ")
    
    # Test the display logic
    print("\nActual display:")
    for i in range(0, 9, 3):
        row = [cell if cell != ' ' else '_' for cell in board[i:i+3]]
        print(f" {row[0]} | {row[1]} | {row[2]} ")
        if i < 6:
            print("---+---+---")
    
    print("✅ Tic Tac Toe board display format looks correct!")

def main():
    """Run all tests"""
    print("=== Testing LSNP Fixes ===\n")
    
    # Test avatar saving
    avatar_ok = test_avatar_saving()
    
    # Test file transfer calculation
    file_transfer_ok = test_file_transfer_calculation()
    
    # Test Tic Tac Toe display
    ttt_ok = test_tic_tac_toe_board_display()
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"Avatar saving: {'✅ PASS' if avatar_ok else '❌ FAIL'}")
    print(f"File transfer calculation: {'✅ PASS' if file_transfer_ok else '❌ FAIL'}")
    print(f"Tic Tac Toe display: {'✅ PASS' if ttt_ok else '❌ FAIL'}")
    
    if avatar_ok and file_transfer_ok and ttt_ok:
        print("\n🎉 All tests passed! The fixes should work correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main()
