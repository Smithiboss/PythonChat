import threading
import socket
import customtkinter
from PIL import Image
import queue


class Server:
    def __init__(self, host, port, peers):
        # attributes
        self.host = host
        self.port = port
        self.peers = peers
        self.clients = []
        self.nicknames = []
        self.message_queue = queue.Queue()
        self.app = app

        # start server
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(self.peers)
        self.app.display_message("Listening at {}".format(self.server_socket.getsockname()))

        # start write thread
        write_thread = threading.Thread(target=self.write)
        write_thread.daemon = True
        write_thread.start()

        # start main thread
        main_thread = threading.Thread(target=self.main, args=(self.server_socket,))
        main_thread.daemon = True
        main_thread.start()

    # broadcast a message to all connected clients and server itself
    def broadcast(self, msg):
        for client in self.clients:
            client.sendall(msg.encode())
        self.app.display_message(msg)

    # method for handling a single client
    def handle(self, client):
        while True:
            try:
                msg = client.recv(1024).decode()
                self.broadcast(msg)
            except socket.error:
                print("Error!")
                break

    # write function for server
    def write(self):
        while True:
            msg = self.message_queue.get()
            formatted_msg = "{}: {}".format("Server", msg)
            self.broadcast(formatted_msg)

    # adds a message to the queue
    def add_to_queue(self, msg):
        self.message_queue.put(msg)

    # main thread, waits for connections and starts single threads for every client
    def main(self, soc):
        while True:
            client, addr = soc.accept()

            client.sendall("NICKNAME".encode())
            nickname = client.recv(1024).decode()

            self.clients.append(client)
            self.nicknames.append(nickname)

            self.broadcast("{} connected to the chat!".format(nickname))

            handle_thread = threading.Thread(target=self.handle, args=(client,))
            handle_thread.daemon = True
            handle_thread.start()


class Client:
    def __init__(self, host, port, nickname):
        self.app = app
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.nickname = nickname
        self.message_queue = queue.Queue()
        try:
            self.client_socket.connect((host, port))
            self.app.display_message("Successfully connected to {}".format(self.client_socket.getpeername()))
        except socket.error as e:
            print(e)

        receive_thread = threading.Thread(target=self.receive)
        receive_thread.daemon = True
        receive_thread.start()
        write_thread = threading.Thread(target=self.write)
        write_thread.daemon = True
        write_thread.start()

    # waits for a message from the server and displays it
    def receive(self):
        while True:
            try:
                msg = self.client_socket.recv(1024).decode()
                if msg == "NICKNAME":
                    self.client_socket.sendall(self.nickname.encode())
                    continue
                self.app.display_message(msg)
            except socket.error:
                self.app.display_message("An error occurred...")
                break

    # write function for client
    def write(self):
        while True:
            msg = self.message_queue.get()
            formatted_msg = "{}: {}".format(self.nickname, msg)
            self.client_socket.sendall(formatted_msg.encode())

    # adds a message to the queue
    def add_to_queue(self, msg):
        self.message_queue.put(msg)


class App(customtkinter.CTk, threading.Thread):
    def __init__(self):
        super().__init__()
        # configuration for main window
        self.title("Chatroom")
        self.geometry("500x500")
        self.resizable(False, False)

        # main window grid config
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # images
        self.main_image = customtkinter.CTkImage(Image.open(r'res/python.png'), size=(300, 300))
        self.send_icon = customtkinter.CTkImage(Image.open(r'res/send_arrow.png'), size=(35, 35))

        # create the main frame containing all frames
        self.main_frame = customtkinter.CTkFrame(self,
                                                 fg_color='#202020',
                                                 corner_radius=0)
        self.main_frame.grid(row=0, column=0, sticky="nswe")

        # display menu frame
        self.menu_frame()

    # handles the menu frame
    def menu_frame(self):
        # destroy previous widgets
        self.widget_destroy(self.main_frame)

        # main_frame grid-configuration
        self.main_frame.grid_columnconfigure(0, weight=1, uniform="equal")
        self.main_frame.grid_columnconfigure(1, weight=1, uniform="equal")
        self.main_frame.grid_rowconfigure(0, weight=2)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=0)
        self.main_frame.grid_rowconfigure(3, weight=0)
        self.main_frame.grid_rowconfigure(4, weight=0)
        self.main_frame.grid_rowconfigure(5, weight=0)

        main_image_label = customtkinter.CTkLabel(self.main_frame,
                                                  image=self.main_image,
                                                  text="")
        start_button = customtkinter.CTkButton(self.main_frame,
                                               text="Start Chatroom",
                                               text_color="#202020",
                                               font=("Arial", 25),
                                               corner_radius=10,
                                               fg_color="#8A2BE2",
                                               hover_color="#9400D3",
                                               command=lambda: self.chatroom_settings("SERVER"))
        join_button = customtkinter.CTkButton(self.main_frame,
                                              text="Join Chatroom",
                                              text_color="#202020",
                                              font=("Arial", 25),
                                              corner_radius=10,
                                              fg_color="#8A2BE2",
                                              hover_color="#9400D3",
                                              command=lambda: self.chatroom_settings("CLIENT"))
        main_image_label.grid(row=0, column=0, columnspan=2, sticky="nswe")
        start_button.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nswe")
        join_button.grid(row=1, column=1, padx=10, pady=(0, 10), sticky="nswe")

    # setting screen before starting/joining a chatroom
    def chatroom_settings(self, config):
        # destroy previous widgets
        self.widget_destroy(self.main_frame)

        # main frame grid configuration
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_rowconfigure(3, weight=1)
        self.main_frame.grid_rowconfigure(4, weight=1)
        self.main_frame.grid_rowconfigure(5, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)

        title_label = customtkinter.CTkLabel(self.main_frame,
                                             text_color="#ffffff",
                                             font=("Arial", 30))
        ip_label = customtkinter.CTkLabel(self.main_frame,
                                          text_color="#ffffff",
                                          font=("Arial", 20))
        port_label = customtkinter.CTkLabel(self.main_frame,
                                            text_color="#ffffff",
                                            font=("Arial", 20))
        peers_label = customtkinter.CTkLabel(self.main_frame,
                                             text_color="#ffffff",
                                             font=("Arial", 20))
        start_button = customtkinter.CTkButton(self.main_frame,
                                               text="Start",
                                               text_color="#202020",
                                               font=("Arial", 20),
                                               fg_color="#8A2BE2",
                                               hover_color="#9400D3")
        abort_button = customtkinter.CTkButton(self.main_frame,
                                               text="Abort",
                                               text_color="#202020",
                                               font=("Arial", 20),
                                               fg_color="#8A2BE2",
                                               hover_color="#9400D3",
                                               command=self.menu_frame)
        nickname_label = customtkinter.CTkLabel(self.main_frame,
                                                text="Nickname:",
                                                text_color="#ffffff",
                                                font=("Arial", 20))
        self.port_entry = customtkinter.CTkEntry(self.main_frame,
                                                 placeholder_text="Enter server port...",
                                                 text_color="#ffffff",
                                                 fg_color="#202020",
                                                 border_color="#8A2BE2")
        self.ip_entry = customtkinter.CTkEntry(self.main_frame,
                                               text_color="#ffffff",
                                               fg_color="#202020",
                                               border_color="#8A2BE2")
        self.nickname_entry = customtkinter.CTkEntry(self.main_frame,
                                                     placeholder_text="Enter your nickname...",
                                                     text_color="#ffffff",
                                                     fg_color="#202020",
                                                     border_color="#8A2BE2")
        self.peers_entry = customtkinter.CTkEntry(self.main_frame,
                                                  placeholder_text="Enter client number...",
                                                  text_color="#ffffff",
                                                  fg_color="#202020",
                                                  border_color="#8A2BE2")
        if config == "SERVER":
            # build frame with server-preset
            title_label.grid(row=0, column=0, columnspan=2)
            ip_label.grid(row=1, column=0)
            port_label.grid(row=2, column=0)
            peers_label.grid(row=3, column=0)
            self.ip_entry.grid(row=1, column=1)
            self.port_entry.grid(row=2, column=1)
            self.peers_entry.grid(row=3, column=1)
            start_button.grid(row=5, column=1)
            abort_button.grid(row=5, column=0)

            # configure text
            title_label.configure(text="Start Chatroom")
            ip_label.configure(text="Allow connections from:")
            peers_label.configure(text="Number of Clients:")
            port_label.configure(text="Server Port:")
            self.ip_entry.configure(placeholder_text="Leave blank...")

            # configure buttons
            start_button.configure(command=lambda: self.chat("SERVER"))
        else:
            # build frame with client-preset
            title_label.grid(row=0, column=0, columnspan=2)
            ip_label.grid(row=1, column=0)
            port_label.grid(row=2, column=0)
            self.ip_entry.grid(row=1, column=1)
            self.port_entry.grid(row=2, column=1)
            nickname_label.grid(row=3, column=0)
            self.nickname_entry.grid(row=3, column=1)
            start_button.grid(row=5, column=1)
            abort_button.grid(row=5, column=0)

            # configure text
            title_label.configure(text="Join Chatroom")
            ip_label.configure(text="Server IP:")
            port_label.configure(text="Server Port:")
            self.ip_entry.configure(placeholder_text="Enter server IP...")

            # configure buttons
            start_button.configure(command=lambda: self.chat("CLIENT"))

    def chat(self, config):
        self.config = config
        # initializes variables containing key values
        if self.config == "CLIENT":
            self.nickname = self.nickname_entry.get()
        else:
            self.peers = int(self.peers_entry.get())
        self.ip = self.ip_entry.get()
        self.port = int(self.port_entry.get())

        # destroy all widgets
        self.widget_destroy(self.main_frame)

        # main frame grid configuration
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_rowconfigure(3, weight=0)
        self.main_frame.grid_rowconfigure(4, weight=0)
        self.main_frame.grid_columnconfigure(0, weight=6)
        self.main_frame.grid_columnconfigure(1, weight=1)

        # create widgets
        head_frame = customtkinter.CTkFrame(self.main_frame,
                                            fg_color="#202020",
                                            corner_radius=0)

        # grid configuration for head-frame
        head_frame.grid_columnconfigure(0, weight=1)
        head_frame.grid_columnconfigure(1, weight=1)
        head_frame.grid_rowconfigure(0, weight=1)

        # create more widgets
        self.chatbox = customtkinter.CTkTextbox(self.main_frame,
                                                width=460,
                                                height=380,
                                                text_color="#ffffff",
                                                fg_color="#202020",
                                                scrollbar_button_color="#8A2BE2",
                                                scrollbar_button_hover_color="#9400D3",
                                                border_color="#8A2BE2",
                                                border_width=2,
                                                state="disabled")
        self.text_entry = customtkinter.CTkEntry(self.main_frame,
                                                 width=400,
                                                 font=("Arial", 15),
                                                 placeholder_text="Send a message...",
                                                 text_color="#ffffff",
                                                 fg_color="#202020",
                                                 border_color="#8A2BE2")
        send_button = customtkinter.CTkButton(self.main_frame,
                                              width=40,
                                              text="",
                                              image=self.send_icon,
                                              fg_color="#8A2BE2",
                                              hover_color="#9400D3")
        abort_button = customtkinter.CTkButton(head_frame,
                                               text_color="#202020",
                                               font=("Arial", 20),
                                               fg_color="#8A2BE2",
                                               hover_color="#9400D3")
        title_label = customtkinter.CTkLabel(head_frame,
                                             text="Chatroom",
                                             fg_color="#202020",
                                             text_color="#ffffff",
                                             font=("Arial", 20))

        if self.config == "SERVER":
            # build server based chat-frame
            head_frame.grid(row=0, column=0, columnspan=2, sticky="nwe")
            self.chatbox.grid(row=1, column=0, columnspan=2, pady=(0, 10), padx=(20, 20), sticky="nswe")
            self.text_entry.grid(row=2, column=0, padx=(20, 0), pady=(0, 10), sticky="nsw")
            send_button.grid(row=2, column=1, padx=(0, 20), pady=(0, 10), sticky="nse")
            abort_button.grid(row=0, column=1, padx=(0, 20), pady=(10, 0), sticky="nse")
            title_label.grid(row=0, column=0, padx=(20, 0), pady=(10, 0), sticky="nsw")

            # configure text
            abort_button.configure(text="Stop server")

            # configure commands
            send_button.configure(command=self.send_server_message)

            # start server thread
            server_thread = threading.Thread(target=self.start_server)
            server_thread.daemon = True
            server_thread.start()
        else:
            # build client based chat-frame
            head_frame.grid(row=0, column=0, columnspan=2, sticky="nwe")
            self.chatbox.grid(row=1, column=0, columnspan=2, pady=(0, 10), padx=(20, 20), sticky="nswe")
            self.text_entry.grid(row=2, column=0, padx=(20, 0), pady=(0, 10), sticky="nsw")
            send_button.grid(row=2, column=1, padx=(0, 20), pady=(0, 10), sticky="nse")
            abort_button.grid(row=0, column=1, padx=(0, 20), pady=(10, 0), sticky="nse")
            title_label.grid(row=0, column=0, padx=(20, 0), pady=(10, 0), sticky="nsw")

            # configure text
            abort_button.configure(text="Leave chat")

            # configure commands
            send_button.configure(command=self.send_client_message)

            # create client instance
            client_thread = threading.Thread(target=self.start_client)
            client_thread.daemon = True
            client_thread.start()

    # destroys every widgets in a given parent-widget
    def widget_destroy(self, widget):
        for elem in widget.winfo_children():
            elem.destroy()

    # displays given message in the textbox
    def display_message(self, msg):
        self.chatbox.configure(state="normal")
        self.chatbox.insert(customtkinter.END, msg + "\n")
        self.chatbox.yview(customtkinter.END)
        self.chatbox.configure(state="disabled")

    # TODO: Check if methods below can be optimized
    # method for sending a message from a client
    def send_client_message(self):
        msg = self.text_entry.get()
        if msg:
            self.client.add_to_queue(msg)

    # method for sending a message from the server
    def send_server_message(self):
        msg = self.text_entry.get()
        if msg:
            self.server.add_to_queue(msg)

    # creates an instance of Server class
    def start_server(self):
        self.server = Server(self.ip, self.port, self.peers)

    # creates an instance of Client class
    def start_client(self):
        self.client = Client(self.ip, self.port, self.nickname)


# runs the mainloop
if __name__ == "__main__":
    app = App()
    app.mainloop()
