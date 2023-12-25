import socket
import sys
import os
import select
from datetime import datetime

BUFFER = 1024
PORT = 0

# Each entry holds a 2-element list, element 1 is a tuple with (socket, name), element 2 is the address of the unicast target
client_info = dict()

# Holds the active sockets
socks = []

# Gets the current time and formats it
def get_time():
    return datetime.now().strftime("%d-%m-%Y %H:%M:%S")

# Correctly formats a server log entry and writes it to the server log
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
        client_info[client][0][0].sendall(message.encode())

# Runs whenever a client disconnects
def disconnect(addr):
    conn = client_info[addr][0][0]
    name = client_info[addr][0][1]

    # Sends a leave message to all other clients
    leaveMessage = '>>' + name + ' has left'
    print(f'Disconnection by {name} from {addr}')
    logger(f'{addr} disconnected from server')
    broadcast(leaveMessage)

    # Remove the clients information from the active client information
    client_info.pop(addr)
    socks.remove(conn)    

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

    client_info[addr][0][0].sendall(message.encode())

# Sends a file from the download folder to a client
def download(addr, filename):
    conn = client_info[addr][0][0]
    print('Started Sending Data')
    logger(f'Start download of {filename} to {addr}')

    # Flag for starting a download
    conn.sendall(f'<d> {filename}'.encode())

    # Open the file and progrssively send its data until there is none left
    with open(os.path.join('./download/', filename), "rb") as f:
        data = f.read(BUFFER)
        while data:
            try:
                conn.sendall(data)
            except BlockingIOError:
                pass
            data = f.read(BUFFER)


    # Flag for the end of a download
    conn.sendall(f'</d>'.encode())
    print('Finished Sending Data')
    logger(f'Finish download of {filename} to {addr}')

def active_client(sock):
    # Get relavent client information
    addr = sock.getpeername()
    conn = client_info[addr][0][0]
    name = client_info[addr][0][1]
    targetaddr = client_info[addr][1]

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
        # If the client requests to disconnect
        conn.sendall(f'>>Goodbye {name}'.encode())
        disconnect(addr)

        # Notify the disconnecting client that the prerequistes for disconnection is complete
        conn.sendall('/exit'.encode())
        conn.close()
        return

    # Client requests to unicast to a specific address
    if data.startswith('/uni'):
        try:
            if len(client_info) > 1:
                # Retrieve the arguments from the command
                params = data.split()
                temp = (params[1], int(params[2]))

                if temp == addr:
                    conn.sendall("You can't send messages to yourself".encode())
                    return

                conn.sendall(f'Directly Connected to {client_info[temp][0][1]}'.encode())
                client_info[addr][1] = temp
                logger(f'{addr} unicasting to {temp}')
            
        except ValueError:  # If the port number isn't a number
            conn.sendall('Invalid command'.encode())
        except IndexError:  # If there are too little parameters
            conn.sendall('Invalid command'.encode())
        except KeyError:    # If the specified address doesn't exist
            conn.sendall("Address doesn't exist".encode())
        return

    if data.startswith('/download'):
        try:  
            # Retrieve the arguments from the command 
            params = data.split()
            file =' '.join(params[1:])
            print(file)

            # Checks if the specified file exists in the download folder
            if not os.path.exists(os.path.join('./download/', file)):
                conn.sendall("File doesn't exist".encode())
                return

            logger(f'{addr} request to download {file}')
            download(addr, file)
            
        except IndexError:  # If there are too little parameters
            conn.sendall('Invalid command'.encode())
        return

    # Client requests to broadcast
    if data == '/broad':
        client_info[addr][1] = None
        logger(f'{addr} switched to broadcast mode')
        return

    # Client requests a list of all the connected clients
    if data == '/members':
        message = 'List of members and their ports:\n'

        for client in client_info.keys():
            message += f'{client_info[client][0][1]} at address {client}\n'

        conn.sendall(message.encode()) 
        logger(f'{addr} requested a list of members')
        return

    if data == '/files':
        list_files(addr)
        logger(f'{addr} requested a list of files')
        return

    # Unicast to the selected target if it still exists
    if targetaddr:
        if targetaddr in client_info:
            print(f'Sending data to {client_info[targetaddr][0][1]} at {targetaddr}')
            data = f'{name} (whisper)>>' + data
            client_info[targetaddr][0][0].sendall(data.encode()) 
            logger(f"{addr} sent '{data}' to {targetaddr}")
            return
        
        conn.sendall(">>Unicast target doesn't exist, switching to broadcast".encode())
        client_info[addr][1] = None
        logger(f'{addr} switched to broadcast mode')
        return

    # Broadcast if the message wasn't a command and there isn't a unicast target
    print(f'sending data back to everyone')
    data = f'{name}>>' + data
    broadcast(data, addr)
    logger(f"{addr} sent '{data}' to all members")

def init():
    global PORT
    try:
        PORT = int(sys.argv[1])
    except ValueError:
        print('Invalid port number')
        return
    except IndexError:
        print('Port number not specified')
        return

    # Creates the download folder if it doesn't already exist
    path = './download'
    if not os.path.exists(path):
        os.mkdir(path)
        print('Created Download Folder')

    # Create a socket and bind the address info
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', PORT))
    s.listen(5)
    s.setblocking(False)

    logger('SERVER START')

    # Add the server socket to the list of active sockets
    socks.append(s)

    while True:
        # Create a selector using the avaliable sockets
        r,_,_ = select.select(socks,[],[])

        # Iterate through each active socket
        for sock in r:
            if sock is s:   # The server socket

                # Extract client information from the new connection
                conn, addr = s.accept()
                conn.setblocking(False)
                name = conn.recv(BUFFER).decode()
                info = (conn, name)

                # Notify of the successful connection
                print(f"Connected by {name} from {addr}")
                conn.sendall(f'>>Welcome {name}!'.encode())
                welcMessage = '>>' + name + ' has joined'
                broadcast(welcMessage)

                logger(f'{name} from {addr} connected to server')
                
                # Add the new client as an active connection
                client_info.update({addr:[info, None]})
                socks.append(conn)

            else:   # A client socket
                active_client(sock)
                

if __name__ == "__main__":
    init()