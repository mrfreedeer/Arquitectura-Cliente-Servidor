import string
import random
import hashlib
import zmq
import time
import sys
from random import sample
from operator import itemgetter


## FUNCTIONS
## Alain T's function https://stackoverflow.com/questions/45471152/how-to-create-a-sudoku-puzzle-in-python
def genBoard():
    base  = 4  # Will generate any size of random sudoku board in O(n^2) time
    side  = base*base
    nums  = sample(range(1,side+1),side) # random numbers
    board = [[nums[(base*(r%base)+r//base+c)%side] for c in range(side) ] for r in range(side)]
    rows  = [ r for g in sample(range(base),base) for r in sample(range(g*base,(g+1)*base),base) ] 
    cols  = [ c for g in sample(range(base),base) for c in sample(range(g*base,(g+1)*base),base) ]            
    board = [[board[r][c] for c in cols] for r in rows]
    return board # List of nine lists

def genSudoku(board):
    side = 16
    squares = side*side
    empties = squares * 3//4
    for p in sample(range(squares),empties):
        board[p//side][p%side] = 0
    print("Solving sudoku:")
    numSize = len(str(side))
    for line in board: print("["+"  ".join(f"{n or '.':{numSize}}" for n in line)+"]")
    return board

def printSolution(sudoku):
    print('Solution Found')
    for line in sudoku:
        print(line)

board = genBoard()
# sudoku = genSudoku(board)

printSolution(board)

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
                return False
            i += 1
    return True, sudoku

print(board)
board = [[8, 1, 2, 7, 5, 3, 6, 4, 9],
[9, 4, 3, 6, 8, 2, 1, 7, 5],
[6, 7, 5, 4, 9, 1, 2, 8, 3],
[1, 5, 4, 2, 3, 7, 8, 9, 6],
[3, 6, 9, 8, 4, 5, 7, 2, 1],
[2, 8, 7, 1, 6, 9, 5, 3, 4],
[5, 2, 1, 9, 7, 4, 3, 6, 8],
[4, 3, 8, 5, 2, 6, 9, 1, 7],
[7, 9, 6, 3, 1, 8, 4, 5, 2]]


print(check_sudoku(board))
