How to start the server:
Open the terminal and run
	python server.py [port]
	Example: python server.py 80

How to start a client:
Open the terminal and run
	python client.py [username] [hostname] [port]
	Example: python client.py John 127.0.0.1 80

Writing a message in the client terminal and pressing enter will either unicast or broadcast that message
By default the mode is on broadcast

Certain commands can be executed by entering the desired command into the client terminal

Commands:
- /exit: Disconnects the client from the server

- /uni [targetaddress] [targetport]: Switches messaging mode to unicast to the specified target
Example: /uni 127.0.0.1 12345

- /broad: Switches messaging mode to broadcast

- /members: Lists all the currently connected clients, their names, addresses and port numbers

- /files: Lists all downloadable files in the server's download folder

- /download [filename]: Requests the server to download the file of the specified name and stores the file in a folder sharing the name of the client
Example: /download example.txt