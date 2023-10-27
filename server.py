from audioop import add
import socket
import sys
from threading import Thread


PORT = int(sys.argv[1])  # Port to listen on (non-privileged ports are > 1023)
all_conns = []

def on_client_connect(conn, addr, name):
    while True:
        data = conn.recv(1024).decode()
        print(f'received>> {data}')
        if data:
            print(f'sending data back to {name} at {addr}')
            message = data.upper()
            conn.sendall(message.encode())      
        else:
            print('no data from', addr)
            break
    leaveMessage = name + ' has left'
    for connection in all_conns:
        connection.sendall(leaveMessage.encode())
    all_conns.remove(conn)
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