# Send multiparts
import zmq
import json

ctx = zmq.Context()
s = ctx.socket(zmq.REQ)

s.connect("tcp://localhost:5555")

s.send_multipart([b"listfiles"])

m = s.recv_json()

print("Recibí: {}".format(m))
