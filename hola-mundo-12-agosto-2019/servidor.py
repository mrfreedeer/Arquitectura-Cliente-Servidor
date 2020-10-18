import zmq

ctx = zmq.Context()
s = ctx.socket(zmq.REP) # Etapa número 1

s.bind("tcp://*:5555") # Etapa número 2

while True:
    m = s.recv()
    print("Mensaje recibido: {}".format(m))
    s.send_string("mundo")

print("Esto no debería aparecer")