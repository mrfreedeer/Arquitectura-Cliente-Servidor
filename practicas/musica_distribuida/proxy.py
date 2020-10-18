import argparse
import zmq 
import os
import ntpath
import hashlib 
import csv
import pyinotify
from itertools import cycle
import json
import time

mb = (1024**2)
chunksize = (1024**2) * 3 #1MB * 3
port = 5535
ctx = zmq.Context()

# ARGS PARSER
parser = argparse.ArgumentParser()
parser.add_argument("-p", "--port", type=int , help="Socket running port")
parser.add_argument("-c", "--chunksize", type=int , help="Amount of bytes to send, default 3MB")
args = parser.parse_args()
if args.port:
    port = args.port
if args.chunksize:
    chunksize = mb * args.chunksize

# WATCH MANAGER
   
wm = pyinotify.WatchManager()
mask = (pyinotify.IN_CREATE | pyinotify.IN_DELETE )  # watched events

class EventHandler(pyinotify.ProcessEvent):
    def process_IN_DELETE(self, event):
        print("Removing:", event.pathname)

    def process_IN_CREATE(self, event):
        filename = ntpath.basename(event.pathname)
        time.sleep(0.1)
        self.proxy.upload(filename)

    def addProxy(self, proxy):
        self.proxy = proxy

class Proxy(object):
    def __init__(self):
        self.serversDict = {}
        if not os.path.exists('files'):
            os.makedirs('files')
    def acceptServer(self,request):
        try:
            socket = ctx.socket(zmq.REQ)
            socket.connect("tcp://" + request["data"]["ip"] + ":" + str(request["data"]["port"]))
            self.serversDict[request["id"]] = {"ip": request["data"]["ip"],
            "port": request["data"]["port"], "socket": socket, "id": request["id"]}
            self.socket.send_json({
                "origin" : "proxy",
                "data" : { 
                    "message": "Server added successfully"
                }
            })
         
        except Exception as serverRequestError:
            print(serverRequestError)
            
    def initializeSocket(self):
        self.socket = ctx.socket(zmq.REP)
        connection = "tcp://*:" + str(port)
        self.socket.bind(connection)
        print("...Proxy Listening...")

    def recv_json(self):
        req = self.socket.recv_json()
        return self.processRequest(req)

    def upload(self, filename):
        try:
            activeServers = cycle(self.serversDict)
            print("Opening files")
            with open("files/"+filename, "rb") as f, open("index.csv", "a") as indexfile:
                indexwriter = csv.writer(indexfile)                

                statinfo = os.stat("files/"+filename)
                sha1hash = hashlib.sha1(f.read()).hexdigest() # Leer de la ruta https://stackoverflow.com/questions/22058048/hashing-a-file-in-python
                f.seek(0,0)
                cont = 1
                chunk = f.read() if statinfo.st_size <= chunksize else f.read(chunksize)
                ext = ntpath.splitext(filename)[1]
                partsInfo = {}

                print("Writing chunk")
                while chunk != b"":
                    currentServer = self.serversDict[next(activeServers)]
                    chunkfilename = sha1hash + "-P" + str(cont) + ext

                    currentServer["socket"].send_json({
                        "origin" : "proxy",
                        "type" : "upload",
                        "data":{
                            "filename": chunkfilename,
                            "bytes" : chunk.decode('iso8859-15') #Correct byte conversion to string
                        }})
                    print("waiting for current socket: ", currentServer["socket"])
                    print("serverId: ", currentServer["id"])

                    #In case a server stores more than one part
                    if currentServer["id"] in partsInfo: 
                        partsInfo[currentServer["id"]].append(chunkfilename)
                    else: 
                        partsInfo[currentServer["id"]] = [chunkfilename]
                    ans = currentServer["socket"].recv_json()
                    chunk = f.read(chunksize)
                    cont += 1

                dictstring = json.dumps(partsInfo) #Convert index dict to string
                print("attempting to write: ", dictstring)
                indexwriter.writerow([filename, dictstring])
                indexfile.close()
                f.close()
            time.sleep(.1)
            os.remove("files/"+filename)
        except Exception as e:
            print(e)
            

    def listFiles(self):
        songlist = []
        with open('index.csv', 'r') as csvFile:
            reader = csv.reader(csvFile)
            for row in reader:
                songlist.append(row)
        csvFile.close()
        print("Sending list: ", [i[0] for i in songlist])
        self.socket.send_json({
            "status": "ok",
            "origin" : "proxy",
            "data" : [i[0] for i in songlist]
        })

    def sendSongInfo(self, song):
        print("Sending song info")
        with open('index.csv', 'r') as csvFile:
            reader = csv.reader(csvFile)
            for row in reader:
                if row[0] == song:
                    print("Sending song info: ")
                    servers = json.loads(row[1]) #server id with filenames in json
                    data = []
                    for s in servers:
                        serverId = s
                        data.append({
                            "id": self.serversDict[serverId]["id"],
                            "ip": self.serversDict[serverId]["ip"],
                            "port": self.serversDict[serverId]["port"],
                            "files": servers[serverId]
                        })
                    self.socket.send_json({
                        "status": "ok",
                        "origin" : "proxy",
                        "data" : data
                    })
                    csvFile.close()
                    return True
        self.socket.send_json(
            {
                "status": "error",
                "origin" : "proxy",
                "data" : {
                    "message" : "Song not found"
                }

            }
        )
        csvFile.close()
        return False

    def processRequest(self, req):
        # print(req)
        if req["origin"] == "server":
            if req["type"] == "announcement":
                self.acceptServer(req)
        if req["origin"] == "client":
            if req["type"] == "listrequest":
                self.listFiles()
            if req["type"] == "songrequest":
                self.sendSongInfo(req["data"])
        
                
   
evHand = EventHandler()
proxy = Proxy() 
proxy.initializeSocket()

evHand.addProxy(proxy)

notifier = pyinotify.ThreadedNotifier(wm, evHand)
# Start the notifier from a new thread, without doing anything as no directory or file are currently monitored yet.
notifier.start()
# Start watching a path
wdd = wm.add_watch(os.getcwd() + "/files", mask, rec=True)             


while True:
    
    proxy.recv_json()
