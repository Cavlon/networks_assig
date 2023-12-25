import socket
import sys
import os
from threading import Thread

BUFFER = 1024

def connect():
    try:
        USER = sys.argv[1] # The client's name
        HOST = sys.argv[2]  # The server's hostname or IP address
        try:
            PORT = int(sys.argv[3])  # The port used by the server
        except ValueError:
            print('Invalid port number')
            return
    except IndexError:
        print('Not all arguments have been specified')
        return

    # Create a socket and connect to the server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        s.connect((HOST, PORT))
    except socket.gaierror:
        print("Server doesn't exist")
        return
    except ConnectionRefusedError:
        print("Server refused connection, check port number")
        return


    # Initialise by sending the user's name
    s.sendall(USER.encode())

    # Separate the sending and receiving functionality with a new thread
    send = Thread(target=sender, args=(s,))
    send.start()
    receiver(s, USER)
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

def receiver(s, USER):
    f = None
    down_buff = b''
    # Keep receiving messages until an error or notified of an exit
    while True:
        try:
            
            bytes_read = s.recv(BUFFER)

            if f:   # If in download mode
                if bytes_read.endswith('</d>'.encode()):    # Exit download mode if the end download flag is found 
                    f.write(down_buff)
                    f.close()
                    f = None
                    down_buff = b''
                    continue
                
                down_buff += bytes_read

            else:   # If in message mode
                data = bytes_read.decode()

                # End receiving functionality if client exits
                if data == '/exit':
                    break

                # Enter download mode if the download flag is found
                if data.startswith('<d>'):
                    # Find the target file name
                    file = ' '.join(data.split()[1:])
                    print(f'>>Downloading {file}')

                    # Create the client download folder if it doesn't already exist
                    path = os.path.join('.', USER)
                    if not os.path.exists(path):
                        os.mkdir(path)

                    # Setup writing to the file
                    f = open(os.path.join(path, file), 'wb')
                    continue
                print(f'{data}')

        except socket.error:
            # Safely exit if there was a forceful disconnection
            print('\n>>Disconnected from server')
            break
    return

if __name__ == "__main__":
    connect()