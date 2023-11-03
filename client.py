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
        message = input('Write your message: ')
        try:
            s.sendall(message.encode())
        except socket.error:
            break
        if message == '/exit':
            break
    return

def receiver(s):
    global end
    while end == False:
        try:
            data = s.recv(1024).decode()
        except socket.error:
            print('\n>>Disconnected from server')
            break

        if data == '/exit':
            break
        print(f'\n{data}')
    return

if __name__ == "__main__":
    connect()