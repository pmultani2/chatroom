from socket import *
import threading
import select

class ServerTCP:
  def __init__(self, server_port):
    self.server_port = server_port
    self.server_socket = socket(AF_INET, SOCK_STREAM)
    self.server_socket.bind((gethostbyname(gethostname()), self.server_port))
    self.server_socket.listen(5)
    self.clients = {}
    self.run_event = threading.Event()
    self.handle_event = threading.Event()

  def accept_client(self):
    readable, writable, erorred = select.select([self.server_socket], [], [], 60)
    if self.server_socket in readable:
      connection, address = self.server_socket.accept()
      
      name = connection.recv(1024).decode()
      if (name in self.clients.values()):
        connection.sendall("Name already taken".encode())
        return False
      connection.sendall("Welcome".encode())
      self.clients[connection] = name
      self.broadcast(connection, "join")
      return True
    return False
  
  def close_client(self, client_socket):
    try:
      self.clients.pop(client_socket)
      client_socket.close()
      return True
    except:
      return False
    
  def broadcast(self, client_socket_sent, message):
    broadcast_message = ""
    name = self.clients[client_socket_sent]
    if "join" in message:
      broadcast_message = f"User {name} has joined"
    elif "exit" in message:
      broadcast_message = f"User {name} left"
    else:
      broadcast_message = f"{name}: {message}"
    for client in self.clients:
      if client != client_socket_sent:
        client.sendall(broadcast_message.encode())
    
  def shutdown(self):
    for client in list(self.clients):
      client.sendall("server-shutdown".encode())
      self.close_client(client)
    self.run_event.set()
    self.handle_event.set()
    self.server_socket.close()
  
  def get_clients_number(self):
    return len(self.clients)
  
  def handle_client(self, client_socket):
    while not self.handle_event.is_set():
      try:
        readable, writable, errored = select.select([client_socket], [], [], 60)
        if client_socket in readable:
          message = client_socket.recv(1024).decode()
          self.broadcast(client_socket, message)
          if "exit" in message:
            break
      except:
        break
    self.close_client(client_socket)
  
  def run(self):
    while not self.run_event.is_set():
      try:
        new_connection = self.accept_client()
        if new_connection:
          client_thread = threading.Thread(target=self.handle_client, args=(list(self.clients.keys())[-1],))
          client_thread.start()
      except:
        break
    self.shutdown()

class ClientTCP:
  def __init__(self, client_name, server_port):
    self.server_addr = gethostbyname(gethostname())
    self.client_socket = socket(AF_INET, SOCK_STREAM)
    self.server_port = server_port
    self.client_name = client_name
    self.exit_run = threading.Event()
    self.exit_receive = threading.Event()
  
  def connect_server(self):
    self.client_socket.connect((self.server_addr, self.server_port))
    self.client_socket.sendall(self.client_name.encode())
    readable, writable, errored = select.select([self.client_socket], [], [], 60)
    if self.client_socket in readable:
      response = self.client_socket.recv(1024).decode()
      if "Welcome" in response:
        return True
      return False
    return False
  
  def send(self, text):
    self.client_socket.sendall(text.encode())
  
  def receive(self):
    while not self.exit_receive.is_set():
      readable, writable, errored = select.select([self.client_socket], [], [], 60)
      if self.client_socket in readable:
        message = self.client_socket.recv(1024).decode()
        if "server-shutdown" in message:
          self.exit_run.set()
          self.exit_receive.set()
          break
        else:
          print(message)
  
  def run(self):
    conn = self.connect_server()
    if conn:
      receive_thread = threading.Thread(target=self.receive, args=())
      receive_thread.start()
      while not self.exit_run.is_set():
        try:
          message = input()
          if message == "exit":
            break
          self.send(message)
        except:
          break
      self.send("exit")
      self.exit_receive.set()

class ServerUDP:
  def __init__(self, server_port):
    self.server_port = server_port
    self.server_socket = socket(AF_INET, SOCK_DGRAM)
    self.server_socket.bind(("", self.server_port))
    self.clients = {}
    self.messages = []
  
  def accept_client(self, client_addr, message):
    try:
      name = message.split(":")[0]
      if name in self.clients.values():
        return False
      self.server_socket.sendto("Welcome".encode(), client_addr)
      self.clients[client_addr] = name
      self.messages.append((client_addr, f"User {name} joined"))
      self.broadcast()
      return True
    except:
      return False

  def close_client(self, client_addr):
    try:
      name = self.clients.pop(client_addr)
      self.messages.append((client_addr, f"User {name} left"))
      self.broadcast()
      return True
    except:
      return False
  
  def broadcast(self):
    tuple = self.messages[-1]
    sender = tuple[0]
    message = tuple[1]
    for client in self.clients:
      if client != sender:
        self.server_socket.sendto(message.encode(), client)

  def shutdown(self):
    for client in list(self.clients):
      self.server_socket.sendto("server-shutdown".encode(), client)
      self.close_client(client)
    self.server_socket.close()
  
  def get_clients_number(self):
    return len(self.clients)
  
  def run(self):
    while True:
      try:
        readable, writable, errored = select.select([self.server_socket], [], [], 60)
        if self.server_socket in readable:
          message, address = self.server_socket.recvfrom(2048)
          message = message.decode()
          if "join" in message:
            self.accept_client(address, message)
          elif "exit" in message:
            self.close_client(address)
          else:
            if address in self.clients:
              self.messages.append((address, message))
              self.broadcast()
      except:
        break
    self.shutdown()

class ClientUDP:
  def __init__(self, client_name, server_port):
    self.server_addr = gethostbyname(gethostname())
    self.client_socket = socket(AF_INET, SOCK_DGRAM)
    self.server_port = server_port
    self.client_name = client_name
    self.exit_run = threading.Event()
    self.exit_receive = threading.Event()
  
  def connect_server(self):
    self.send("join")
    readable, writable, errored = select.select([self.client_socket], [], [], 60)
    if self.client_socket in readable:
      response, address = self.client_socket.recvfrom(2048)
      response = response.decode()
      if "Welcome" in response:
        return True
      return False
    return False

  def send(self, text):
    message = f"{self.client_name}: {text}"
    self.client_socket.sendto(message.encode(), (self.server_addr, self.server_port))
  
  def receive(self):
    while not self.exit_receive.is_set():
      r, w, e = select.select([self.client_socket], [], [], 60)
      if self.client_socket in r:
        message, address = self.client_socket.recvfrom(2048)
        message = message.decode()
        if "server-shutdown" in message:
          self.exit_run.set()
          self.exit_receive.set()
          break
        else:
          print(message)
  
  def run(self):
    conn = self.connect_server()
    if conn:
      receive_thread = threading.Thread(target=self.receive, args=())
      receive_thread.start()
      while not self.exit_run.is_set():
        try:
          msg = input()
          if "exit" in msg:
            break
          self.send(msg)
        except:
          break
      self.send("exit")
      self.exit_receive.set()
    




    




  






