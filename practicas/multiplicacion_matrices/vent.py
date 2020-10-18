import string
import random as rnd
import hashlib
import zmq
import time
import csv
import json

context = zmq.Context()

# socket with workers
workers = context.socket(zmq.PUSH)
workers.bind("tcp://*:5557")

# socket with sink
sink = context.socket(zmq.PUSH)
sink.connect("tcp://localhost:5558")

print("Input n, when workers are ready...")
n = input()
sink.send_string(n) # Send matrix size
n = int(n)
print("sending tasks to workers")


def genRandomMatrix(n):
    return [[rnd.randint(0,10) for j in range(n)] for i in range(n)]

m2T = [[0 for i in range(n)]for i in range(n)]
def transposeMatrix(n, m2T, m2):
    for i in range(n):
        for j in range(n):
            m2T[j][i] = m2[i][j]

        
 
m1 = genRandomMatrix(n)
m2 = genRandomMatrix(n)

transposeMatrix(n,m2T, m2)


# with open("matrix1.csv", "w") as mat1, open("matrix2.txt", "w") as mat2:
#     print(type(m1))
#     wr = csv.writer(mat1)
#     print(type(wr))
#     wr.writerow(m1)
#     wr = csv.writer(mat2)
#     wr.writerow(m2)
#     mat1.close()
#     mat2.close()

# with open("matrix1.csv", "rb") as mat1, open("matrix2.txt", "rb") as mat2:
#     while True:
#         workers.send_json({"matrix1": mat1.read().decode(), "matrix2":mat2.read().decode()})
print(m1,"\n\n",m2)
for i in range(len(m1[0])):
    for j in range(len(m2)):
        workers.send_json({"matrix1": m1, 
        "matrix2": m2T, "i": i, "j":j})
    


