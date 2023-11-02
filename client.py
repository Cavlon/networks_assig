#!/usr/bin/env python3

import socket
import sys
from threading import Thread

end = False

def connect():
    USER = sys.argv[1]
    HOST = sys.argv[2]  # The server's hostname or IP address
    PORT = int(sys.argv[3])  # The port used by the server

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.sendall(USER.encode())

    send = Thread(target=sender, args=(s,))
    send.start()
    receiver(s)
    send.join()
    s.close()

def sender(s):
    while True:
        message = input('\nWrite your message: ')
        if message == '/exit':
            s.sendall(message.encode())
            break
        s.sendall(message.encode())
    return

def receiver(s):
    global end
    while end == False:
        data = s.recv(1024).decode()
        if data == '/exit':
            break
        print(f'\nreceived>> {data}')
    return

if __name__ == "__main__":
    connect()