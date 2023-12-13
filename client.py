import socket
import sys
from threading import Thread

def connect():
    USER = sys.argv[1] # The client's name
    HOST = sys.argv[2]  # The server's hostname or IP address
    PORT = int(sys.argv[3])  # The port used by the server

    # Create a socket and connect to the server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    # Initialise by sending the user's name
    s.sendall(USER.encode())

    # Separate the sending and receiving functionality with a new thread
    send = Thread(target=sender, args=(s,))
    send.start()
    receiver(s)
    send.join()

    # Once both the receiver and sender functions end, close the socket
    s.close()

def sender(s):
    # Keep requesting inputs until an error or exit
    while True:
        message = input('Write your message: ')
        try:
            # Send the input message to the server
            s.sendall(message.encode())

        except socket.error:
            # Safely exit if there was a forceful disconnection
            break
        
        # End sending functionality if client exits
        if message == '/exit':
            break
    return

def receiver(s):
    # Keep receiving messages until an error or notified of an exit
    while True:
        try:
            # Receive a message from the server
            data = s.recv(1024).decode()

        except socket.error:
            # Safely exit if there was a forceful disconnection
            print('\n>>Disconnected from server')
            break

        # End receiving functionality if client exits
        if data == '/exit':
            break

        print(f'\n{data}')
    return

if __name__ == "__main__":
    connect()