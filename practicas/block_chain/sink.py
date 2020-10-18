import sys
import time
import zmq

context = zmq.Context()

recvWorker = context.socket(zmq.PULL)
recvWorker.bind("tcp://*:5558")

recvVent = context.socket(zmq.PUSH)
recvVent.connect("tcp://localhost:5560")
recvVent.send_string('0')

# Wait for start of batch
s = recvWorker.recv_string()
print("answer",s)