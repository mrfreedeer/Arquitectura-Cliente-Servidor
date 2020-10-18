import zmq
import csv
import hashlib
import argparse
import sys
import os
import ntpath
import menupy
import ast
import re

context = zmq.Context()
tcpstr = "tcp://"

# The client executes the python file and should see a menu
# where files, of any kind, can be uploaded, or downloaded. 
# When uploading, a file is fragmented and uploaded, a list is created
# assimilating a magnet to keep registry of where to download the file parts
# Thus, a client needs a root address to connect to the ring and make request

parser = argparse.ArgumentParser()
parser.add_argument("-ra","--rootaddress", type=str, help="Root address if Node is not Root")
parser.add_argument("-d", "--debugger", help="Debugger address")
parser.add_argument("-ch", "--chunksize", help="Chunksize for file storage")

args = parser.parse_args()

chunksize = (args.chunksize * (1024 ** 2))if args.chunksize else (1024**2 * 3)
debugsocket = context.socket(zmq.PAIR)
debugsocket.connect(tcpstr + "localhost:7000")
debugsocket.send_json({"op":"Nodecount"})
msg = debugsocket.recv_json()
nodecount = msg["count"]   
if not args.rootaddress:
    ft = 0
    NewMenu = menupy.InputMenu("----------Chord root address menu ------------\n"+ "\tNodecount: " + str(nodecount)+"\n", title_color="cyan")
    if ft > 0:
        NewMenu.title = "Invalid address, please try again!"
        NewMenu.title_color = "red"
    NewMenu.add_input("Root address", color="yellow" if ft==0 else "red", input_text="192.168.1.14:6666", input_color="blue")
    result = NewMenu.run()
    rootaddress = result["Root address"]    
else:
    rootaddress = args.rootaddress

def listFiles():
    return os.listdir("files")
def listFromIndex():
    fileList = []
    with open('index.csv', 'r') as csvFile:
        reader = csv.reader(csvFile)
        for row in reader:
            fileList.append(row)
    csvFile.close()
    return [i[0] for i in fileList]

class Client():
    def __init__(self, rootaddress):
        if not os.path.exists('files'):
                os.makedirs('files')
        if not os.path.exists('downloads'):
                os.makedirs('downloads')
        self.rootsocket = context.socket(zmq.REQ)
        self.rootsocket.connect(tcpstr + rootaddress)
        self.querysocket = context.socket(zmq.REQ)
       
        self.servers = {}
     
    def responsible(self, key):
        return {
            "op" : "responsible",
            "id" : key
        }

    def download(self, filename):
        try:
            with open('index.csv', 'r')  as csvFile, open("downloads/" + filename, "ab") as f:
                reader = csv.reader(csvFile)
                for row in reader:
                    if row[0] == filename:
                        parts = ast.literal_eval(row[1])
                        parts = [n.strip() for n in parts]
                        print(parts)
                        part = 0

                        while True:
                            print("ITERATION : ", part)
                            print(parts[part])
                            sha = ntpath.splitext(parts[part])[0]
                            self.rootsocket.send_json({
                                "op" : "responsible",
                                "intent" : "download",

                                "id" : int(sha,16)
                            })
                            msg = self.rootsocket.recv_json()
                            while not msg["found"]:
                                address = msg["address"]
                                self.querysocket.connect(tcpstr + address)
                                self.querysocket.send_json({
                                "op" : "responsible",
                                "intent" : "download",
                                "id" : int(sha,16)
                                })
                                msg = self.querysocket.recv_json()
                                self.querysocket.disconnect(tcpstr + address)
                            self.querysocket.connect(tcpstr + msg["address"])
                            # print("Found responsible: ")
                            # print(msg["id"]//(1024**10))
                            # print(msg)
                            self.querysocket.send_json({
                                "op": "download",
                                "filename": parts[part]
                            })
                            partbytes = self.querysocket.recv_json()
                            print("MESSAGE: ", partbytes["op"])
                            if partbytes["op"] == "download":
                                f.write(partbytes["bytes"].encode('iso8859-15'))
                            else:
                                print("Whoops, something went wrong ")
                                print(partbytes["message"])
                                return False  
                            if part == (len(parts)-1):
                                return True
                            else:
                                part += 1                     
                                
        except Exception as e:
            print("Whoops, something went wrong: ")
            print(e)
            return False

    def upload(self, filename):
        try:
            with open("files/"+filename, "rb") as f, open("index.csv", "a") as indexfile:
                indexwriter = csv.writer(indexfile)                
                
                statinfo = os.stat("files/"+filename)
                f.seek(0,0)
                chunk = f.read() if statinfo.st_size <= chunksize else f.read(chunksize)
                ext = ntpath.splitext(filename)[1]
                partsinfo = []
                while chunk != b"":
                    shacode = hashlib.sha512(chunk).hexdigest()
                    print(len(shacode))
                    chunkfilename = shacode + ext
                    shakey = int(shacode,16) % (2**512)
                    self.rootsocket.send_json(self.responsible(shakey))
                    msg = self.rootsocket.recv_json()
                    print("finding responsible")
                    while not msg["found"]:
                        self.servers[msg["id"]] = msg["address"]
                        address = msg["address"]
                        self.querysocket.connect(tcpstr + msg["address"])
                        self.querysocket.send_json(self.responsible(shakey))
                        msg = self.querysocket.recv_json()
                        self.querysocket.disconnect(tcpstr + address)
                    print("--------------------")
                    print("KEY: ", shakey//(1024**10))
                    print("Found responsible: ")
                    print(msg["id"]//(1024**10))
                    print(msg)
                    self.querysocket.connect(tcpstr + msg["address"])

                    self.querysocket.send_json({
                        "op" : "upload",
                        "filename" : chunkfilename,
                        "bytes" : chunk.decode('iso8859-15')
                    })
                    print("SENT MESSAGE")
                    print(self.querysocket.recv_json())
                    partsinfo.append(shacode + ext)
                    chunk = f.read(chunksize)
                print("PARTSINFO: ", partsinfo)
                partstring = str(partsinfo)
                indexwriter.writerow([filename, partstring])
                indexfile.close()
                f.close()
        except Exception as e:
            print("Whoops, something went wrong: ")
            print(e)


chordClient = Client(rootaddress)
menutitle = "------------------Chord client------------------\n  Root address: " + rootaddress
menutitle += "\t Node count: " + str(nodecount) + "\n\n"
NewMenu = menupy.OptionMenu(menutitle, title_color="cyan")

NewMenu.add_option("Download")
NewMenu.add_option("Upload")
NewMenu.add_option("Exit", color="red")
op = ""

while op != "Exit":
     
    op = NewMenu.run()
    if op == "Download":
        while op != "Back":
           
            filesMenu = menupy.OptionMenu("------------------Download------------------\n", title_color="cyan")
            files = listFromIndex()
            for i in files:
                filesMenu.add_option(i)
            filesMenu.add_option("Back", color="red")
            op = filesMenu.run()
            if op != "Back":
                chordClient.download(op)
        
    if op == "Upload":
        while op != "Back":
            
            filesMenu = menupy.OptionMenu("------------------Upload------------------\n", title_color="cyan")
            files = listFiles()
            for i in files:
                filesMenu.add_option(i)
            filesMenu.add_option("Back", color="red")
            op = filesMenu.run()
            if op != "Back":
                chordClient.upload(op)

        




