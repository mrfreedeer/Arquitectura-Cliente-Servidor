import string
import random
import hashlib
import zmq
import time
import sys
from random import sample
from operator import itemgetter

# Init context
context = zmq.Context()
# socket with workers
workers = context.socket(zmq.PUSH)
workers.bind("tcp://*:5557")
# socket with recv sink
recvsink = context.socket(zmq.PULL)
recvsink.connect("tcp://localhost:5560")

def genBoard():
    base  = 3  # Will generate any size of random sudoku board in O(n^2) time
    side  = base*base
    nums  = sample(range(1,side+1),side) # random numbers
    board = [[nums[(base*(r%base)+r//base+c)%side] for c in range(side) ] for r in range(side)]
    rows  = [ r for g in sample(range(base),base) for r in sample(range(g*base,(g+1)*base),base) ] 
    cols  = [ c for g in sample(range(base),base) for c in sample(range(g*base,(g+1)*base),base) ]            
    board = [[board[r][c] for c in cols] for r in rows]
    return board # List of nine lists

def genSudoku(board):
    side = 9
    squares = side*side
    empties = squares * 3//4
    for p in sample(range(squares),empties):
        board[p//side][p%side] = 0
    print("Solving sudoku:")
    numSize = len(str(side))
    for line in board: print("["+"  ".join(f"{n or '.':{numSize}}" for n in line)+"]")
    return board

## FUNCTIONS
## Alain T's function https://stackoverflow.com/questions/45471152/how-to-create-a-sudoku-puzzle-in-python
def printSudoku(sudoku):
    print('------------------')
    for line in sudoku:
        print(line)    

def checkZero(x, l):
    if x == 0:
        return random.randint(1, l)
    else:
        return x

def newBoard(b):
    new_l = [[checkZero(x, len(b)) for x in i] for i in b]
    return new_l

def genPopulation(sudoku, n):
    pop = []
    for i in range(n):
        pop.append(newBoard(sudoku))
    return pop

#hardest sudoku according to Finnish mathematician
#Arto Inkala. Rated 11 in difficulty in a five star system

sudoku = [[8,0,0,0,0,0,0,0,0], 
[0,0,3,6,0,0,0,0,0], 
[0,7,0,0,9,0,2,0,0], 
[0,5,0,0,0,7,0,0,0], 
[0,0,0,0,4,5,7,0,0], 
[0,0,0,1,0,0,0,3,0], 
[0,0,1,0,0,0,0,6,8], 
[0,0,8,5,0,0,0,1,0], 
[0,9,0,0,0,0,4,0,0]]

# sudoku = [[15, 2, 12, 0, 9, 0, 0, 0, 0, 8, 5, 0, 0, 0, 3, 0],
# [0, 0, 11, 13, 0, 0, 14, 0, 0, 9, 0, 7, 0, 0, 0, 12],
# [9, 0, 0, 7, 0, 11, 0, 0, 0, 0, 0, 0, 0, 0, 8, 5],
# [0, 0, 0, 0, 0, 12, 0, 0, 0, 3, 0, 13, 0,0, 9, 10],
# [0, 6, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0,0, 0, 0, 1],
# [11, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 15, 0, 0, 2],
# [0, 0, 2, 15, 0, 1, 0, 0, 0, 5, 0, 8, 0, 0, 0, 0],
# [0, 0, 1, 0, 11, 0, 0, 0, 7, 0, 2, 0, 8, 0, 5, 0],
# [0, 0, 0, 0, 0, 0, 0, 0, 0, 6, 15, 0, 16, 0, 4, 0],
# [6, 12, 0, 0, 0, 0, 0, 0, 5, 0, 8, 0, 0, 0, 13, 0],
# [13, 11, 0, 0, 0, 0, 0, 16, 10, 0, 0,0, 0, 12, 6, 10],
# [0, 0, 0, 16, 0, 0, 0, 0, 0, 13, 0, 0, 2, 0, 7, 0],
# [16, 0, 0, 0, 14, 0, 0, 5, 0, 1, 0, 0, 0, 0, 2, 0],
# [0, 0, 0, 0, 0, 0, 8, 0, 9, 0, 0, 0, 0, 0, 14, 0],
# [0, 0, 6, 0, 2, 0, 9, 0, 0, 0, 0, 0, 0, 3, 0, 10],
# [2, 0, 7, 12, 0, 0, 0, 0, 0, 0, 6, 5, 0, 0, 0, 0]]

board = genBoard()
sudoku = genSudoku(board)

print('original sudoku')
printSudoku(sudoku)
print("Press enter when workers are ready...")
_ = input()
print("sending tasks to workers")

sudokusize = len(sudoku)
# Send initial sudoku
tstart = time.time()
for i in range(5):
    workers.send_json({
        'sudoku': sudoku,
        'size': sudokusize
    })
solutionFound = False

sink_msg = recvsink.recv_json()
solutionFound = sink_msg["solved"]

if solutionFound:
    tend = time.time()
    printSudoku(sink_msg['solution'])
    print("TIME:", tend-tstart)
# else:
#     todo = filterSudokus(sink_msg["work"], hashList, globalTodo)
#     cont = 1
#     print("Len globalTodo:", len(globalTodo))

#     while len(globalTodo) > 0 and cont > 0:
#         workers.send_json({
#             'sudoku': globalTodo.pop()[0],
#             'size' : sudokusize
#         })
#         cont -= 1