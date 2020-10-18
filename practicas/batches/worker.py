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
    timedelay = float(vent.recv_string())
    time.sleep(timedelay)
    sink.send_string('Done')
    