import zmq
import argparse
ctx = zmq.Context()
debug = ctx.socket(zmq.PULL)

debug.bind("tcp://*:5000")
nodes = 0
parser = argparse.ArgumentParser()

parser.add_argument("-c", "--client", type=str, help="Client address")

args = parser.parse_args()

clientsocket = ctx.socket(zmq.PAIR)
if args.client:
    clientsocket.bind("tcp://*"+args.client)
    print("client")
else:
    clientsocket.bind("tcp://*:7000")


poller = zmq.Poller()
poller.register(debug, zmq.POLLIN)
poller.register(clientsocket, zmq.POLLIN)
while True:
    socks = dict(poller.poll())
    if debug in socks:
        msg = debug.recv_json()
        if "op" in msg and msg["op"] == "++": 
            nodes += 1
   
        print(msg)
        print("----------------------------")
    if clientsocket in socks:
        print(clientsocket.recv_json())
        clientsocket.send_json({
            "op" : "nodecount",
            "count" : nodes
        })