#!/usr/bin/env python3

import socket
import sys
from threading import Thread

def connect():
    USER = sys.argv[1]
    HOST = sys.argv[2]  # The server's hostname or IP address
    PORT = int(sys.argv[3])  # The port used by the server

    # message = input("Input lowercase sentence: ")

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.sendall(USER.encode())

    send = Thread(target=sender, args=(s,))
    receive = Thread(target=receiver, args=(s,))
    receive.start()
    send.start()
    receive.join()
    send.join()

def sender(s):
    while True:
        message = input('\nWrite your message: ')
        if message == '/exit':
            break
        s.sendall(message.encode())
    s.close()
        

def receiver(s):
    while s:
        data = s.recv(1024).decode()
        print(f'\nreceived>> {data}')

if __name__ == "__main__":
    connect()