import sys
import time
import zmq
import string
import random
import math
import hashlib
import copy

context = zmq.Context()

vent = context.socket(zmq.PULL)
ventip = "localhost" if len( sys.argv)==1 else sys.argv[1]
vent.connect("tcp://" + ventip + ":5557")


# Socket to send messages to
sink = context.socket(zmq.PUSH)
sink.connect("tcp://"+ ventip +":5558")


# https://terribleatmaths.wordpress.com/2013/09/20/python-check-whether-a-simple-sudoku-solution-is-correct/
def check_sudoku(sudoku):
    ## checks rows
    n = len(sudoku)
    for row in sudoku:
        i = 1
        while i <= n:
            if i not in row:
                return False
            i += 1
    ## transposes matrix (don't forget to define n=len())
    j = 0    
    transpose = []
    temp_row = []
    while j < n:
        for row in sudoku:
            temp_row.append(row[j])
        transpose.append(temp_row)
        temp_row = []
        j += 1
    ## checks columns
    for row in transpose:
        i = 1
        while i <= n:
            if i not in row:
                return False, []
            i += 1
    return True, sudoku

def newBoard(b):
    for block in b:
        opt = list(set(range(1,len(b)+1)) - set(block))
        index = 0
        for number in block:
            if number == 0:
                picked = random.choice(opt)
                block[index] = picked
                opt.remove(picked)
            index += 1
        

    return b

def genPopulation(sudoku, n):
    population = []
    for i in range(n):
        population.append(newBoard(sudoku))
    return population

def printSudoku(sudoku):
    print('------------------')
    for line in sudoku:
        print(line)

cont = 0
solutionsExplored = 0
message = vent.recv_json()
while True:
    print('iteration:', cont)
    print('Solutions explored:', solutionsExplored)
    print("Getting new work todo")
    print("Working")
    size = message["size"] if "size" in message else 9
    print('creating pop')
    pop_size = 50000
    pop = genPopulation(message['sudoku'], pop_size)
    for i in range(len(pop)):
        solutionFound, sol = check_sudoku(message['sudoku'])
        solutionsExplored += 1
        if solutionFound:
            print('solution found')
            sink.send_json({
                'solved': True,
                'solution': sol
            })
        else:
            print('No solution')
    cont +=1
    print('random board')
    printSudoku(pop[random.randint(0, pop_size)])
