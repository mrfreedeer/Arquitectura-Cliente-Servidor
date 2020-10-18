import sys
import time
import zmq
import string
import random
import hashlib

context = zmq.Context()

vent = context.socket(zmq.PULL)
vent.connect("tcp://localhost:5557")

# Socket to send messages to
sink = context.socket(zmq.PUSH)
sink.connect("tcp://localhost:5558")

# Process tasks forever

while True:
    message = vent.recv_json()
    matrix1 = message["matrix1"]
    matrix2 = message["matrix2"]
    row = message["i"]
    col = message["j"]
    result = 0
    for (i,j) in zip(matrix1[row], matrix2[col]):
        result += i*j
    sink.send_json({"result": result, "i": row, "j": col})


