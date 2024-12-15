import socket
import threading


class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.nickname = input("Nickname: ")
        try:
            self.client_socket.connect((host, port))
            print("Successfully connected to {}".format(self.client_socket.getpeername()))
        except socket.error as e:
            print(e)

        receive_thread = threading.Thread(target=self.receive)
        receive_thread.start()
        write_thread = threading.Thread(target=self.write)
        write_thread.start()

    def receive(self):
        while True:
            try:
                msg = self.client_socket.recv(1024).decode()
                if msg == "NICKNAME":
                    self.client_socket.sendall(self.nickname.encode())
                    continue
                print(msg)
            except socket.error:
                print("An error occurred...")
                break

    def write(self):
        while True:
            msg = "{}: {}".format(self.nickname, input(""))
            self.client_socket.sendall(msg.encode())


if __name__ == "__main__":
    client = Client("127.0.0.1", 12345)
