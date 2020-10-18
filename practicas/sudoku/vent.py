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

## FUNCTIONS
## Alain T's function https://stackoverflow.com/questions/45471152/how-to-create-a-sudoku-puzzle-in-python
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
    side = 0
    squares = side*side
    empties = squares * 3//4
    for p in sample(range(squares),empties):
        board[p//side][p%side] = 0
    print("Solving sudoku:")
    numSize = len(str(side))
    # for line in board: print("["+"  ".join(f"{n or '.':{numSize}}" for n in line)+"]")
    return board

def printSolution(sudoku):
    print('Solution Found')
    for line in sudoku:
        print(line)

def filterSudokus(work, hashList, globalTodo):
    print("LEN WORK",len(work))
    print('hashlist len', len(hashList))
    print('------------------------')
    filteredList = list(filter(lambda x: hash(str(x[0])) not in hashList, work))
    # print("filteredList", filteredList)
    print('------------------------')
    hashList += list(map(lambda x: hash(str(x)), filteredList))
    globalTodo.extend(filteredList)
    print("gtodo len", len(globalTodo))
    globalTodo = sorted(globalTodo, key=itemgetter(1), reverse=True)
    print("blank space")
    print(set(i[1] for i in globalTodo))
    
    print("-------------------")
    return filteredList

board = genBoard()
sudoku = genSudoku(board)

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

# sudoku = [[8,0,9,0,10,0,0,12,16,0,15,0,0,0,0,4],
#  [0,0,15,0,0,0,5,0,0,7,0,10,0,0,13,0],
#  [2,0,0,0,0,0,0,4,0,0,0,0,0,16,0,14],
#  [0,6,0,3,0,0,14,0,0,0,11,0,9,0,0,0],
#  [0,0,0,0,0,9,0,0,1,0,0,2,0,0,0,7],
#  [11,0,0,0,14,0,0,6,0,0,0,0,0,13,0,0],
#  [0,7,0,16,0,2,0,0,12,0,0,0,0,0,1,0],
#  [0,0,0,5,8,0,0,13,0,3,0,0,0,0,0,9],
#  [12,0,4,0,0,0,7,0,13,0,8,0,11,0,0,0],
#  [0,5,0,8,0,13,0,10,0,16,0,4,0,0,0,0],
#  [0,0,14,0,0,0,9,0,6,0,0,11,0,1,0,3],
#  [1,0,0,0,3,0,0,5,0,0,0,0,6,0,16,0],
#  [14,0,7,0,0,0,10,0,0,12,0,9,0,8,2,0],
#  [0,16,0,12,0,14,0,3,0,0,0,0,13,0,0,11],
#  [5,10,0,0,6,0,11,0,0,0,14,0,0,7,0,0],
#  [15,0,1,0,0,0,0,2,0,0,0,5,0,0,0,12]]

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
# sudoku = [[8,0,0,0,0,0,0,0,0], 
# [0,0,3,6,0,0,0,0,0], 
# [0,7,0,0,9,0,2,0,0], 
# [0,5,0,0,0,7,0,0,0], 
# [0,0,0,0,4,5,7,0,0], 
# [0,0,0,1,0,0,0,3,0], 
# [0,0,1,0,0,0,0,6,8], 
# [0,0,8,5,0,0,0,1,0], 
# [0,9,0,0,0,0,4,0,0]]


# 159 0s Solvable. Solution not found, 630000 dead paths.
#Runtime: 2h 
# sudoku = [[0,9,0,0,0,0,0,0,0,0,2,10,1,15,0,0],
# [0,0,0,3,15,2,0,0,0,0,16,0,4,9,10,0],
# [0,0,0,7,12,0,8,0,1,0,0,0,14,0,0,0],
# [16,0,0,15,0,0,3,0,0,8,4,0,0,0,11,2],
# [0,11,0,2,0,15,10,0,4,0,0,0,0,0,0,6],
# [0,0,3,0,6,16,1,0,0,0,0,0,0,7,0,12],
# [12,0,0,0,13,0,0,0,16,0,15,3,9,0,0,0],
# [15,0,10,4,3,0,11,0,0,14,7,9,0,0,0,0],
# [10,0,0,0,0,8,7,0,0,1,0,12,0,11,5,0],
# [0,1,6,9,0,0,0,0,0,0,0,0,3,0,0,0],
# [0,15,11,12,0,0,0,0,7,0,0,0,0,10,0,0],
# [2,7,0,0,0,0,0,9,0,16,11,0,0,0,0,1],
# [0,8,0,0,0,11,2,0,15,0,0,1,0,3,12,0],
# [3,16,0,1,0,0,12,0,0,9,5,0,0,0,0,0],
# [0,0,0,13,0,0,0,0,0,0,0,0,2,1,0,15],
# [0,0,0,0,7,0,9,0,13,0,10,0,5,14,16,11]]



#159 0s Solvable. Solution found, 0.4 s with 4 workers
# sudoku = [
# [12,8,0,0,4,0,1,7,16,0,0,3,0,5,0,0],
# [11,9,14,0,0,8,0,0,0,0,4,0,0,3,0,0],
# [4,10,0,0,0,0,0,0,9,0,0,0,0,2,0,0],
# [6,0,13,0,0,0,0,0,8,0,0,0,1,7,0,4],
# [7,0,0,0,0,0,0,4,0,0,0,0,0,0,0,2],
# [3,0,0,4,0,0,0,0,0,0,0,0,0,0,0,7],
# [5,0,9,6,0,0,0,0,0,0,7,0,0,4,0,3],
# [2,0,8,0,0,0,0,0,0,0,0,0,0,0,0,5],
# [0,4,3,0,0,6,5,9,0,2,0,8,7,0,0,1],
# [0,12,7,0,0,4,3,0,0,5,0,9,2,8,0,0],
# [0,0,2,8,0,0,7,0,0,3,0,0,0,9,0,0],
# [0,0,5,9,0,0,2,0,0,7,1,0,3,0,4,0],
# [8,0,0,0,0,2,0,0,0,4,0,0,6,0,3,9],
# [0,7,0,1,9,0,6,0,0,0,0,0,0,0,2,10],
# [9,3,0,0,8,5,0,0,2,0,0,0,0,1,7,0],
# [10,0,0,15,0,7,0,1,3,6,9,0,0,14,5,8]
# ]

blankspaces = 0
for i in sudoku:
    for j in i:
        if j == 0:
            blankspaces += 1


printSolution(sudoku)
print("Blankspaces: ", blankspaces)
print("Press enter when workers are ready...")
_ = input()
print("sending tasks to workers")

sudokusize = len(sudoku)

# Send initial sudoku
tstart = time.time()
workers.send_json({
    'sudoku': sudoku,
    'size': sudokusize
})

solutionFound = False
hashList = []
globalTodo = []
hashList.append(hash(str(sudoku)))

while not solutionFound:
    sink_msg = recvsink.recv_json()
    solutionFound = sink_msg["solved"]
    print("Len hashList:", len(hashList))

    if solutionFound:
        tend = time.time()
        printSolution(sink_msg['solution'])
        print("TIME:", tend-tstart)
        break
    else:
        work = sink_msg["work"]
        globalTodo.extend(work)
        print("gtodo len", len(globalTodo))
        globalTodo = sorted(globalTodo, key=itemgetter(1), reverse=True)
        print("blank space", set(i[1] for i in globalTodo))
        cont = 0
        while cont < 3: 
            if (len(globalTodo) > 0):
                workers.send_json({
                    'sudoku': globalTodo.pop()[0],
                    'size' : sudokusize
                })
            else:
                print('no global todo') 
            cont += 1
        cont = 0