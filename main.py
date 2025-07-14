from socket import socket
from network import Network
from parser import parse_message, format_message
from config import PORT

network = Network(PORT)
network.start_listening()

while True:
    cmd = input("Command (profile/post/dm/peers/messages/exit): ").strip().lower()
    # call relevant functions here
    if cmd == "exit":
        print("Exiting...")
        network.stop_listening()

    elif cmd == 'profile':
        name = input("Display Name: ")
        status = input("Status: ")
        userID = name.lower() + "@" + socket.gethostbyname(socket.getsockname())
        msg = format_message({
            "TYPE": "PROFILE",
            "USER_ID": userID,
            "DISPLAY_NAME": name,
            "STATUS": status
        })
        network.send_message(msg)

    elif cmd == 'post':
        userID = input("User ID: ")
        content = input("Content: ")
        msg = format_message({
            "TYPE": "POST",
            "USER_ID": userID,
            "CONTENT": content
        })
        network.send_message(msg)

    elif cmd == "dm":
        userID = input("User ID: ")
        destIP = input("Recipient IP: ")
        content = input("Message: ")
        msg = format_message({
            "TYPE": "DM",
            "USER_ID": userID,
            "CONTENT": content
        })
        network.send_message(msg, dest_ip=destIP)

    elif cmd == "peers":
        userID = input("User ID: ")
        msg = format_message({
            "TYPE": "PING",
            "USER_ID": userID
        })
        network.send_message(msg)

