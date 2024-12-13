from chatroom import ServerTCP, ServerUDP

protocol = int(input())

if protocol == 0:
  server = ServerTCP(8080)
  server.run()
elif protocol == 1:
  server = ServerUDP(8080)
  server.run()