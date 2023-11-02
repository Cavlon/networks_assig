import socket
import sys
from threading import Thread


PORT = int(sys.argv[1])  # Port to listen on (non-privileged ports are > 1023)
all_conns = []

def broadcast(message):
    for connection in all_conns:
        connection.sendall(message.encode())

def on_client_connect(conn, addr, name):
    leaveMessage = name + ' has left'
    while True:
        try:
            data = conn.recv(1024).decode()
        except socket.error:
            print(f'Disconnection by {name} from {addr}')
            all_conns.remove(conn)
            broadcast(leaveMessage)
            conn.close()
            return
        print(f'received>> {data}')
        if data == '/exit':
            break
        print(f'sending data back to {name} at {addr}')
        message = data.upper()
        conn.sendall(message.encode()) 
    print(f'Disconnection by {name} from {addr}') 
    broadcast(leaveMessage)
    all_conns.remove(conn)
    conn.sendall('/exit'.encode())
    conn.close()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', PORT))
s.listen(5)
while True:
    print("Waiting for Connection")
    conn, addr = s.accept()
    all_conns.append(conn)
    name = conn.recv(1024).decode()
    print(f"Connected by {name} from {addr}")
    welcMessage = name + ' has joined'
    for connection in all_conns:
        connection.sendall(welcMessage.encode())
    t = Thread(target=on_client_connect, args=(conn, addr, name))
    t.start()