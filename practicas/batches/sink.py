import sys
import time
import zmq

context = zmq.Context()

receiver = context.socket(zmq.PULL)
receiver.bind("tcp://*:5558")

sender = context.socket(zmq.PUSH)

sender.bind("tcp://*:5560")

while True: 
    batchSize = int(receiver.recv_string())
    for i in range(batchSize):
        ans = receiver.recv_string()
    sender.send_string("Finished")
    print("finished")