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

class Sudoku(object):
    def __init__(self, sudokulist, sinksocket, size=9):
        self.sinksocket = sinksocket
        self.table = sudokulist
        self.size = size
        self.othernodes = []
        self.blankspaces = []
        self.minPossibilities = []
        self.iterations = 0
        self.sent = False
        
        while self.iterations < 3:
            print("iteration:", self.iterations)
            while self.filter():
                print("filter")
            
            print(len(self.minPossibilities))
            print(self.minPossibilities)

            if len(self.minPossibilities) == 0: #If there are no possibilities, list is empty ([])
                self.sendToSink(self.checkSolution(self.table))
            elif not self.checkSolution(self.table) :
                print("BI: ", self.blockindex, "NI: ", self.numberindex)
                for line in self.table:
                    print(line)
                self.chosen = random.randint(0,len(self.minPossibilities)-1)
                self.table[self.blockindex][self.numberindex] = self.minPossibilities[0]
            
                for i in range(1, len(self.minPossibilities)):
                    newSudoku = copy.deepcopy(self.table)
                    newSudoku[self.blockindex][self.numberindex] = self.minPossibilities[i]
                    blankspaces = self.checkBlanks(newSudoku)
                    self.othernodes.append((newSudoku, blankspaces))
            else:
                self.sendToSink(True)
                break
            self.iterations += 1

        if not self.sent:
            blankspaces = self.checkBlanks(self.table)
            self.othernodes.insert(0,(self.table, blankspaces))
            print(self.othernodes)
            self.sendToSink()


    def checkBlanks(self,table):
        cont = 0
        for block in self.table: 
            if 0 in block:
                cont += 1
        return cont
    def sendToSink(self, solution = False):
        self.sent =  True
        print("sending more work")
        try:
            if solution:
                self.sinksocket.send_json({
                    "solved" : True,
                    "solution": self.table
                })
            else:
                self.sinksocket.send_json({
                    "solved" : False,
                    "work": self.othernodes
                })
        except Exception as e:
            print("error: ", e)

        print("FEED ME WORK")
    def checkSolution(self, table):
        for block in table: 
            if 0 in block:
                return False
        return True

    def checkRow(self, possibilities, block):
        for neighbour in block:
            if neighbour in possibilities:
                possibilities.remove(neighbour)
    def checkCol(self, possibilities, numberindex):
        for block in self.table:
            if block[numberindex] in possibilities:
                possibilities.remove(block[numberindex]) 
    def checkBlock(self, possibilites, numberindex, blockindex):
        blocksize = int (math.sqrt(self.size))
        col = (numberindex // blocksize) * blocksize 
        row = (blockindex // blocksize) * blocksize
        for i in range(blocksize):
            for j in range(blocksize):
                if self.table[row+i][col+j] in possibilites:
                    possibilites.remove(self.table[row+i][col+j])
    def filter(self):
        print("filtering")
        self.minPossibilities = [i + 1 for i in range(self.size)]
        for block in self.table:
            counter = 0
            for number in block:
                if number == 0:
                    possibilities = [i + 1 for i in range(self.size)]
                    numberindex = counter
                    blockindex = self.table.index(block)
                    self.checkRow(possibilities, block)
                    self.checkCol(possibilities, numberindex)
                    self.checkBlock(possibilities, numberindex, blockindex)

                    if len(possibilities) == 1:
                        self.table[blockindex][numberindex] = possibilities[0]
                        return True
                    elif len(possibilities) <= len(self.minPossibilities):
                        self.minPossibilities = possibilities
                        self.numberindex = numberindex
                        self.blockindex = blockindex      
                counter += 1
        return False

# Socket to send messages to
sink = context.socket(zmq.PUSH)
sink.connect("tcp://"+ ventip +":5558")

# Process tasks forever

while True:
    print("Getting new work todo")
    message = vent.recv_json()
    # for row in message["sudoku"]:
    #     print(row)
    print("RECEIVING NEW WORK")
    size = message["size"] if "size" in message else 9
    sudok = Sudoku(message["sudoku"], sink, size)
    del sudok
    