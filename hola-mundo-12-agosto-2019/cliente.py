import zmq

ctx = zmq.Context()
s = ctx.socket(zmq.REQ)

s.connect("tcp://192.168.61.148:5555")

s.send_string("")
m = s.recv()
print("Recibí: {}".format(m))
