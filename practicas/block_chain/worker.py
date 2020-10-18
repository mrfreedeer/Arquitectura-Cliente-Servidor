import sys
import time
import zmq
import string
import random
import hashlib

context = zmq.Context()

def hashString(s):
    sha = hashlib.sha256()
    sha.update(s.encode('ascii'))
    return sha.hexdigest()

def generation(challenge, size = 25):
    answer = ''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits)
                      for x in range(size))
    attempt = challenge + answer
    return attempt, answer

work = context.socket(zmq.PULL)
work.connect("tcp://localhost:5557")

# Socket to send messages to
sink = context.socket(zmq.PUSH)
sink.connect("tcp://localhost:5558")

# Process tasks forever
found = False
challenge = work.recv_string()
random.seed()
while not found:
    attempt, answer = generation(challenge, 64)
    print(attempt)
    hash = hashString(attempt)
    print(hash)
    if hash.startswith('0000'):
        print("FOUND!")
        found = True
        print(hash)
        sink.send_string(answer)