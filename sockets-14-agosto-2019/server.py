import zmq

ctx = zmq.Context()
s = ctx.socket(zmq.REP) # Etapa número 1

s.bind("tcp://*:5555") # Etapa número 2

while True:
    d = s.recv_json()

    resp = 0
    if (d["operacion"] == "suma"):
        resp = d["op1"] + d["op2"] 

    s.send(resp)