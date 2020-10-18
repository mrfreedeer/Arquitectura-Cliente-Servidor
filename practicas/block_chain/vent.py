import string
import random
import hashlib
import zmq
import time

def hashString(s):
    sha = hashlib.sha256()
    sha.update(s.encode('ascii'))
    return sha.hexdigest()


context = zmq.Context()

# socket with workers
workers = context.socket(zmq.PUSH)
workers.bind("tcp://*:5557")

# socket with sink
sink = context.socket(zmq.PUSH)
sink.connect("tcp://localhost:5559")

print("Press enter when workers are ready...")
_ = input()
print("sending tasks to workers")

# sink.send(b'0')

challenge = hashString("migueloolol")
while True:
    workers.send_string(challenge)