from chatroom import ClientTCP, ClientUDP
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--name", "-n", type=str, help="Client name")
args = parser.parse_args()

protocol = int(input())

if protocol == 0:
  client = ClientTCP(args.name, 8080)
  client.run()
elif protocol == 1:
  client = ClientUDP(args.name, 8080)
  client.run()