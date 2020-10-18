import sys
import time
import zmq

context = zmq.Context()

receiver= context.socket(zmq.PULL)
receiver.bind("tcp://*:5558")

matrixSize = int(receiver.recv_string())
resultmatrix = [[0 for i in range(matrixSize)]for i in range(matrixSize)]

# Wait for start of batch
for i in range(matrixSize**2):
    workerAns = receiver.recv_json()
    resultmatrix[workerAns["i"]][workerAns["j"]] = workerAns["result"]

for i in range(matrixSize):
    for j in range(matrixSize):
        print(resultmatrix[i][j], end='\t')
    print("\n")