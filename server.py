import socket
import sys
from threading import Thread


PORT = int(sys.argv[1])  # Port to listen on (non-privileged ports are > 1023)
all_conns = []
all_addr = []
all_names = []

def broadcast(message, exclude=None):       
    for connection in all_conns:
        if exclude:
            if connection == exclude:
                continue
        connection.sendall(message.encode())

def disconnect(conn, addr, name):
    leaveMessage = name + ' has left'
    print(f'Disconnection by {name} from {addr}')
    all_conns.remove(conn)
    all_addr.remove(addr)
    all_names.remove(name)
    broadcast(leaveMessage)

def on_client_connect(conn, addr, name):
    unicast = False
    targetconn = None
    while True:
        try:
            data = conn.recv(1024).decode()
        except socket.error:
            disconnect(conn, addr, name)
            conn.close()
            return
        
        print(f'received>> {data}')
        if data == '/exit':
            break
        elif data.startswith('/uni'):
            try:
                params = data.split()
                targetaddr = (params[1], int(params[2]))
                ind = all_addr.index(targetaddr)
                targetconn = all_conns[ind]
            except ValueError:
                conn.sendall('Invalid command'.encode())
                continue
            except IndexError:
                conn.sendall('Invalid command'.encode())
                continue
            unicast = True
            continue
        elif data == '/broad':
            unicast = False
            continue
        elif data == '/members':
            message = 'List of members and their ports:\n'
            for i in range(len(all_conns)):
                message += f'{all_names[i]} at port {all_addr[i]}\n'
            conn.sendall(message.encode()) 
            continue

        if unicast:
            print(f'sending data back to {name} at {addr}')
            targetconn.sendall(data.encode()) 
        else:
            broadcast(data, conn)

    conn.sendall(f'Goodbye {name}'.encode())
    disconnect(conn, addr, name)

    conn.sendall('/exit'.encode())
    conn.close()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', PORT))
s.listen(5)

while True:
    print("Waiting for Connection")

    conn, addr = s.accept()
    name = conn.recv(1024).decode()

    print(f"Connected by {name} from {addr}")
    conn.sendall(f'Welcome {name}!'.encode())

    welcMessage = name + ' has joined'
    for connection in all_conns:
        connection.sendall(welcMessage.encode())

    all_conns.append(conn)
    all_addr.append(addr)
    all_names.append(name)

    t = Thread(target=on_client_connect, args=(conn, addr, name))
    t.start()