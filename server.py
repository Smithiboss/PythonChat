import socket
import threading


class Server:
    def __init__(self, host, port, peers):
        self.host = host
        self.port = port
        self.peers = peers
        self.clients = []
        self.nicknames = []

        # start server
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(self.peers)
        print("Listening at {}".format(self.server_socket.getsockname()))
        self.main(self.server_socket)

    def broadcast(self, msg):
        for client in self.clients:
            client.sendall(msg.encode())
        print(msg)

    def handle(self, client):
        while True:
            try:
                msg = client.recv(1024).decode()
                self.broadcast(msg)
            except socket.error:
                print("Error!")
                break

    def main(self, soc):
        while True:
            client, addr = soc.accept()

            client.sendall("NICKNAME".encode())
            nickname = client.recv(1024).decode()

            self.clients.append(client)
            self.nicknames.append(nickname)

            self.broadcast("{} connected to the chat!".format(nickname))

            thread = threading.Thread(target=self.handle, args=(client,))
            thread.start()


if __name__ == "__main__":
    server = Server("", 12345, 5)
