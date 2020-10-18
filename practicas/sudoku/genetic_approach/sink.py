import sys
import zmq

context = zmq.Context()

receiver = context.socket(zmq.PULL)
receiver.bind("tcp://*:5558")

sender = context.socket(zmq.PUSH)
sender.bind("tcp://*:5560")

while True: 
    workerMessage = receiver.recv_json()
    print("Receiving", workerMessage)
    if workerMessage["solved"]:
        print("SOLVEEEED SINK")
        sender.send_json({
            'solved': True,
            'solution': workerMessage["solution"]
        })