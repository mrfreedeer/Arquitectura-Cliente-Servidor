import string
import random
import hashlib
import zmq
import time
import sys


context = zmq.Context()

# socket with workers
workers = context.socket(zmq.PUSH)
workers.bind("tcp://*:5557")

# socket with send sink
sendsink = context.socket(zmq.PUSH)
sendsink.connect("tcp://localhost:5558")

# socket with recv sink
recvsink = context.socket(zmq.PULL)
recvsink.connect("tcp://localhost:5560")

print("Press enter when workers are ready...")
_ = input()
print("sending tasks to workers")
numtask = int(sys.argv[1])
batchsize = int(sys.argv[2])
ready = True

tasklist = [random.random() for i in range(numtask)]
index = 0

while index < numtask:
    sendsink.send_string(str(batchsize))
    print("Sending batch of %d".format(batchsize))
    print(tasklist[index:])
    for i in range(batchsize):
        workers.send_string(str(tasklist[index]))
        index += 1
    recvsink.recv_string()