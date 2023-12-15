import socket
import sys
import os
from threading import Thread
from datetime import datetime

BUFFER = 4096
PORT = int(sys.argv[1])
# Holds the address, connection and name of each connected client
client_info = dict()

def get_time():
    return datetime.now().strftime("%d-%m-%Y %H:%M:%S")

def logger(message):
    entry = f'[{get_time()}] {message}\n'
    print(entry)
    with open('server.log', 'a') as log:
        log.write(entry)

# Send a message to every connected client
def broadcast(message, addr = None):       
    for client in client_info.keys():
        # Don't send the message to the sender if they are specified
        if client == addr:
            continue
        client_info[client][0].sendall(message.encode())

# Runs whenever a client disconnects
def disconnect(addr):
    name = client_info[addr][1]
    leaveMessage = '>>' + name + ' has left'
    print(f'Disconnection by {name} from {addr}')
    logger(f'{addr} disconnected from server')
    client_info.pop(addr)
    # Sends a leave message to all other clients
    broadcast(leaveMessage)

# Lists all the files in the download folder
def list_files(addr):
    path = './download'
    # Retrieves all items in the folder
    contents = os.listdir(path)
    message = 'List of downloadable files:\n'

    # Only lists the files
    for item in contents:
        if os.path.isfile(os.path.join(path, item)):
            message += f'{item}\n'

    client_info[addr][0].sendall(message.encode())

# Sends a file from the download folder to a client
def download(addr, filename):
    conn = client_info[addr][0]
    print('Started Sending Data')
    logger(f'Start download of {filename} to {addr}')

    # Flag for starting a download
    conn.sendall(f'<d> {filename}'.encode())

    # Open the file and progrssively send its data until there is none left
    with open(os.path.join('./download/', filename), "rb") as f:
        while True:
            data = f.read(BUFFER)
            conn.sendall(data)

            # Once there is no more data left to send, end the transfer
            if not data:
                break

    # Flag for the end of a download
    conn.sendall(f'</d>'.encode())
    print('Finished Sending Data')
    logger(f'Finish download of {filename} to {addr}')

def active_client(addr):
    targetaddr = None
    conn = client_info[addr][0]
    name = client_info[addr][1]

    # Keep waiting for client data until they disconnect or exit
    while True:

        try:
            # Wait for a message from the client
            data = conn.recv(BUFFER).decode()

        #In case of forceful disconnection
        except socket.error:
            logger(f'Socket error from {addr}')
            disconnect(addr)
            conn.close()
            return
        
        print(f'received>> {data}')

        # Client requests a disconnection
        if data == '/exit':
            break

        # Client requests to unicast to a specific address
        if data.startswith('/uni'):
            try:
                if len(client_info) > 1:
                    # Retrieve the arguments from the command
                    params = data.split()
                    temp = (params[1], int(params[2]))

                    if temp == addr:
                        conn.sendall("You can't send messages to yourself".encode())
                        continue

                    conn.sendall(f'Directly Connected to {client_info[temp][1]}'.encode())
                    targetaddr = temp
                    logger(f'{addr} unicasting to {targetaddr}')
                
            except ValueError:  # If the port number isn't a number
                conn.sendall('Invalid command'.encode())
            except IndexError:  # If there are too little parameters
                conn.sendall('Invalid command'.encode())
            except KeyError:    # If the specified address doesn't exist
                conn.sendall("Address doesn't exist".encode())
            continue

        if data.startswith('/download'):
            try:  
                # Retrieve the arguments from the command 
                params = data.split()
                file = params[1]

                # Checks if the specified file exists in the download folder
                if not os.path.exists(os.path.join('./download/', file)):
                    conn.sendall("File doesn't exist".encode())
                    continue

                logger(f'{addr} request to download {file}')
                download(addr, file)
                
            except IndexError:  # If there are too little parameters
                conn.sendall('Invalid command'.encode())
            continue

        # Client requests to broadcast
        if data == '/broad':
            targetaddr = None
            logger(f'{addr} switched to broadcast mode')
            continue

        # Client requests a list of all the connected clients
        if data == '/members':
            message = 'List of members and their ports:\n'

            for client in client_info.keys():
                message += f'{client_info[client][1]} at address {client}\n'

            conn.sendall(message.encode()) 
            logger(f'{addr} requested a list of members')
            continue

        if data == '/files':
            list_files(addr)
            logger(f'{addr} requested a list of files')
            continue

        # Unicast to the selected target if it still exists
        if targetaddr:
            if targetaddr in client_info:
                print(f'Sending data to {client_info[targetaddr][1]} at {targetaddr}')
                data = f'{name} (whisper)>>' + data
                client_info[targetaddr][0].sendall(data.encode()) 
                logger(f'{addr} sent {data} to {targetaddr}')
                continue
            conn.sendall(">>Unicast target doesn't exist, switching to broadcast".encode())
            targetaddr = None
            logger(f'{addr} switched to broadcast mode')
            continue

        # Broadcast if the message wasn't a command and there isn't a unicast target
        print(f'sending data back to everyone')
        data = f'{name}>>' + data
        broadcast(data, addr)
        logger(f'{addr} sent {data} to all members')

    # If the client requests to disconnect
    conn.sendall(f'>>Goodbye {name}'.encode())
    disconnect(addr)

    # Notify the disconnecting client that the prerequistes for disconnection is complete
    conn.sendall('/exit'.encode())
    conn.close()

def init():
    # Creates the download folder if it doesn't already exist
    path = './download'
    if not os.path.exists(path):
        os.mkdir(path)
        print('Created Download Folder')

    # Create a socket and bind the address info
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', PORT))
    s.listen(5)

    logger('SERVER START')

    # Keep waiting for new connections
    while True:
        print("Waiting for Connection")

        # Extract and store client information from the new connection
        conn, addr = s.accept()
        name = conn.recv(BUFFER).decode()
        info = (conn, name)

        # Notify of the successful connection
        print(f"Connected by {name} from {addr}")
        conn.sendall(f'>>Welcome {name}!'.encode())
        welcMessage = '>>' + name + ' has joined'
        broadcast(welcMessage)

        logger(f'{name} from {addr} connected to server')
        
        client_info.update({addr:info})

        # Dedicate a unique thread to each connected client
        t = Thread(target=active_client, args=(addr, ))
        t.start()

if __name__ == "__main__":
    init()