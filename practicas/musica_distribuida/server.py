import argparse
import zmq
import socket
import os.path
import hashlib
import random as rnd
# CONSTANTS
port = 5555

chunksize = (1024**2)*3  #3 MB
proxy = "localhost:5535"
ctx = zmq.Context()


# ARGS PARSER
parser = argparse.ArgumentParser()
parser.add_argument("-p", "--port", type=int, help="Socket running port")
parser.add_argument("-c", "--chunksize", type=int,
                    help="Amount of bytes to send, default 3MB")
parser.add_argument("-x", "--proxy", help="ip and port of proxy")
args = parser.parse_args()
if args.port:
    port = args.port
if args.chunksize:
    chunksize = mb *args.chunksize
if args.proxy:
    proxy = args.proxy

# FUNCTIONS


def getIp():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ans = s.getsockname()[0]
        s.close()
        return str(ans)
    except Exception as e:
        print(e)


def printSocketsInfo():
    print("..Socket inicializado correctamente... {}".format("tcp://*:" + str(port)))
    print("..Proxy inicializado correctamente... {}".format("tcp://...:5555"))


# CLASSES
class Server():
    def __init__(self):
        if not os.path.exists('songs'):
            os.makedirs('songs')
        self.port = port
        self.ip = "localhost"
        self.initializeSocket()
        self.printServerInfo()
        self.getServerId()
        self.announceServer()

    def getServerId(self):
        if os.path.exists("serverId.txt"):
            f = open("serverId.txt", "r")
            self.id = f.read()
        else:
            f = open("serverId.txt", "w")
            id = str(rnd.randint(1, 100000000000000))
            f.write(id)
            self.id = id

    def printServerInfo(self):
        print("...Servidor inicializado...")
        print("Port:", port)
        print("Chunksize: {} MB".format(int(chunksize/1000000)))
        print("IP: {}".format(self.ip))

    def initializeSocket(self):
        try:
            self.socket = ctx.socket(zmq.REP)
            connection = "tcp://*:" + str(port)
            self.socket.bind(connection)
            ip = getIp()
            print(ip)
            if ip != "":
                self.ip = ip 
            self.announceSocket = ctx.socket(zmq.REQ)
            self.announceSocket.connect("tcp://" + proxy)
            printSocketsInfo()
        except Exception as e:
            print(e)

    def receiveRequest(self):
        resp = self.socket.recv_json()
        print("..Receiving..")
        return resp

    def reply(self, req):
        rep = server.processRequest(req)
        server.socket.send_json(rep)

    def readfile(self, filename):
        try:
            with open("songs/"+filename, "rb") as f:
                ans = {
                    "status" : "ok",
                    "origin" : "server",
                    "data" : {
                        "bytes": f.read().decode('iso8859-15')
                    }
                }
            f.close()
            return ans
        except Exception as e:
            print(e)
            return {
                "status" : "error",
                "origin" : "server",
                "data"  : {
                    "message" : str(e)
                }
            }


    def processRequest(self, req):
        print("..Procesing...")
        if req["origin"] == "proxy":
            print("...From proxy...")
            if req["type"] == "upload":
                print("...Upload request...")
                print("Receiving file: ", req["data"]["filename"])
                return server.writeFile(req["data"])
        elif req["origin"] == "client":
            print("...From client...")
            if req["type"] == "download":
                print("...Download request...")
                print("Download file: ", req["data"]["filename"])
                return self.readfile(req["data"]["filename"])

    def writeFile(self, data):
        with open("songs/" + data["filename"], "wb") as f:
            f.write(data["bytes"].encode('iso8859-15')) #Reconversion from string to bytes
        print("File {} saved succesfully".format(data["filename"]))
        return {
            "origin": "server",
            "type": "announce",
            "data": "File saved succesfully"
        }

    def announceServer(self):
        print("..Announcing server..")
        print("Sending data: Id: {}, ip: {}, port: {}".format(self.id, self.ip, self.port))
        self.announceSocket.send_json({
            "origin": "server",
            "type": "announcement",
            "id": self.id,
            "data": {
                "ip": self.ip,
                "port": self.port
            }
        })
        print(self.announceSocket.recv_json())


server = Server()

while True:
    try:
        req = server.receiveRequest()
        server.reply(req)
    except Exception as e:
        print(e)
        break
