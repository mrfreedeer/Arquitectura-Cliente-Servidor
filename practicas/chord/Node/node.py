import zmq
import socket
import hashlib
import uuid 
import argparse
import random
import time
import threading
import os
import ntpath

def getIp():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ans = s.getsockname()[0]
        s.close()
        return str(ans)
    except Exception as e:
        print(e)


context = zmq.Context()
tcpstr = "tcp://"


# A node needs an address where to find the Root Node, if it's not the root
# The client address (port where client requests are processed), predecessor
# address (same concept as client address). The rest is optional 

# A node is the root if it helps other nodes join the circle


parser = argparse.ArgumentParser()
parser.add_argument("-r", "--root", type=bool, help="Start node as root")
parser.add_argument("-ra","--rootaddress", type=str, help="Root address if Node is not Root")
parser.add_argument("-c", "--client", type=str, help="Client address")
parser.add_argument("-pr", "--predecessor", type=str, help="Predecessor address")
parser.add_argument("-d", "--debugger", help="Debugger address")
parser.add_argument("-id", "--id", type=int, help="Force Node to take an id")
parser.add_argument("-b", "--bits", type=int, help="Number of bits to create ids with")
parser.add_argument("-ch", "--chunksize", help="Chunksize for file storage")

args = parser.parse_args()
root = args.root if args.root else False

chunksize = (args.chunksize * (1024 ** 2))if args.chunksize else (1024**2 * 3)
bits = args.bits if args.bits else 6
if args.id:
    id = args.id
else:
    mac = hex(uuid.getnode())
    hexstring = '0a1b2c3d4e5f6789'
    b = int(bits/4) if int(bits/4) > 6 else 6
    ranstring = ''.join(random.choice(hexstring) for i in range(b))
    id = int(mac + ranstring,16) % (2**b)


debugger = args.debugger if args.debugger else None
client = args.client if args.client else None
predecessor = args.predecessor if args.predecessor else None
if not root:
    rootaddress = args.rootaddress
    if args.debugger:
        debugger = args.debugger
   


class Node:
    def __init__(self, id, root, client_address, debug, prev_address ,
     next_address = ""):
        if not os.path.exists('files'):
                os.makedirs('files')
        # Sockets are created but not initialized, as well as the poller
        print(id)
        self.lastfingerupdate = time.time() 
        self.id = id
        self.prev = {"id": None, "sok": None}
        self.fingertable = []   
        self.next = {"id": None, "sok": None}
        self.client =  context.socket(zmq.REP)
        ip = getIp()

        if client_address == None:
            port = self.client.bind_to_random_port(tcpstr + "*")
            self.address = ip + ":" + str(port)
        else:
            self.client.bind(tcpstr + "*" + client_address)
            self.address = ip + client_address
        
        self.query = context.socket(zmq.REQ)
        self.prev["sok"] = context.socket(zmq.PAIR)
        if prev_address == None:
            port = self.prev["sok"].bind_to_random_port(tcpstr + "*")
            self.prev["address"] = self.nodeAddress =  ip + ":" + str(port)
        else:
            self.prev["address"] = self.nodeAddress =  ip + prev_address
            self.prev["sok"].bind(tcpstr + "*" + prev_address)

        print(tcpstr + self.prev["address"])
        self.next["sok"] =  context.socket(zmq.PAIR)
        self.errormessage = "¿De que me hablas viejo?"
        self.claimnextmessage = "Successor successfully updated"
        self.claimprevmessage = "Predecessor sucessfully updated"
        self.fatalerrormessage = "Sorry, a fatal error occurred. Try again later"
        self.uploadmessage = "Part uploaded successfully"
        self.opcodes = ["infoRequest", "infoSuccessor", "infoPredecessor",
         "claimSuccession", "claimPredecessor", "update", "updateFingers",
         "responsible", "upload", "download", "transfer"]
        self.poller = zmq.Poller()
        self.poller.register(self.client, zmq.POLLIN)
        self.poller.register(self.prev["sok"], zmq.POLLIN)
        self.poller.register(self.next["sok"], zmq.POLLIN)
        self.debugger = None
        if debug != None:
                self.debugger = context.socket(zmq.PUSH)
                self.debugger.connect(tcpstr + debug)

    def ping(self):
        next_call = time.time()
        while True:
            print("PING")
            next_call = next_call+30
            self.debugger.send_json({
                "op" : "ping",
                "id" : self.id
            })
            time.sleep(next_call - time.time())
    def joinRingCommunity(self, rootaddress):
        # Procedure needed to join the ring
        # The responsible for the local id must be found and contacted
        # A message is sent to the responsible, for it to change its predecessor
        # an implied message is sent when the responsible receives the message
        # The predecessor changes its succesor to the current node
        # Connections are then established
        # Address = Client Address 
        # NodeAddress = Predecessor socket address. 
        if self.debugger != None:
            self.debugger.send_json({
                "op" : "++"
            })
        self.query = context.socket(zmq.REQ)
        self.query.connect(tcpstr+rootaddress)
        self.query.send_json({
            "op" : "responsible",
            "id" : self.id
        })
        msg = self.query.recv_json()

        self.query.disconnect(tcpstr+rootaddress)
        while not msg["found"]:
            print("IDK MAN: NEXT => ", msg["id"])
            tempaddress = msg["address"]
            self.query.connect(tcpstr+tempaddress)
            self.query.send_json({
            "op" : "responsible",
            "id" : self.id
              })
            print("sent")
            msg = self.query.recv_json()
            self.query.disconnect(tcpstr+tempaddress)
        address = msg["address"]
        print("RESPONSIBLE")
        print(msg)
        print("_______________")
        self.query.connect(tcpstr+address)
        self.query.send_json({
            "op" : "infoPredecessor"
        })
        msg = self.query.recv_json()
        self.prev["id"] = msg["id"]

        self.query.send_json({
            "op" : "claimPredecessor",
            "id": self.id,
            "address": self.address,
            "nodeAddress" : self.nodeAddress
        })
        print(self.query.recv_json())
        self.query.send_json({
            "op" : "infoRequest"
        })
        
        msg = self.query.recv_json()
        print(msg)
        self.next["sok"].connect(tcpstr + msg["nodeAddress"])
        self.next["sok"].send_json({"op" : "update", "message": "test"})
        self.next["address"] = msg["address"]
        self.next["id"] = msg["id"]
        self.next["nodeAddress"] = msg["nodeAddress"]
        sock = context.socket(zmq.REQ)
        sock.connect(tcpstr + msg["address"])
        self.fingertable.append({
            "prev" : msg["prev"],
            "id" : msg["id"],
            "address" : msg["address"],
            "nodeAddress" : msg["nodeAddress"],
            "sok" : sock
            })
        self.query.send_json({
            "op" : "infoSuccessor"
        })
        msg = self.query.recv_json()
        print(msg)
        print(msg["trueNext"])
        if not msg["trueNext"]:
            self.query.send_json({
            "op" : "claimSuccession",
            "id": self.id,
            "address": self.address,
            "nodeAddress" : self.nodeAddress
            })
            # self.prev["id"] = msg["id"]
            print(self.query.recv_json())
        print(self)
        
        self.poller.register(self.next["sok"], zmq.POLLIN)
        self.next["sok"].send_json({
            "op" : "transfer",
            "id" : self.id
        })
        self.query.disconnect(tcpstr+address)
        self.computeFingerTable()
        self.next["sok"].send_json({
            "op" : "updateFingers"
        })
        print("**************** NOT BLOCKED || JOIN ****************")

    def poll(self):
        return dict(self.poller.poll())
        
    def clientsock(self):
        return self.client

    def predsock(self):
        return self.prev["sok"]

    def succsock(self):
        return self.next["sok"]

    def responsible(self, key):
        # print("--------------RESPONSIBLE CHECK------------------")
        # print("KEY: ", key)
        # print("PREV: ", self.prev["id"])
        # print("NEXT: ", self.next["id"])
        # print("NODEID: ", self.id)
        # print("FINGERTABLE:  ", self.fingertable)
        # print("--------------------------------------------------")
        # print("NEXT: ", self.next["id"])
        # print("KEY: ", key)
        # print("ID: ", self.id)
        if self.next["id"]:
            print(self.next["id"] >= key > self.id)
        if not (self.prev["id"]  and self.next["id"]) or (self.id >= key > self.prev["id"]):
            print("A")
            return {"found" : True,
                    "prev" : self.prev["id"],
                    "id" : self.id,
                    "key" : key,
                    "address" : self.address,
                    "nodeAddress" : self.nodeAddress}
        elif self.prev["id"] > self.id:
            if self.prev["id"] < key or key <= self.id:
                print("B")
                {"found" : True,
                    "prev" : self.prev["id"],
                    "id" : self.id,
                    "key" : key,
                    "address" : self.address,
                    "nodeAddress" : self.nodeAddress}
        else:
            for node in self.fingertable:
                print(key > node["prev"] > node["id"])
                if (key > node["prev"] > node["id"]) or (key <= node["id"] < node["prev"]):
                    print("D")
                    return {"found" : True,
                    "prev" : node["prev"],
                    "id" : node["id"],
                    "key" : key,
                    "address" : node["address"],
                    "nodeAddress" : node["nodeAddress"]}
                if node["id"]>= key > node["prev"]:
                    print("E")
                    return {"found" : True,
                    "prev" : node["prev"],
                    "id" : node["id"],
                    "key" : key,
                    "address" : node["address"],
                    "nodeAddress" : node["nodeAddress"]}
       
        print("F")
        found = self.next["id"] >= key > self.id
        return {
                    "found" : found,
                    "prev" : self.id,
                    "id" : self.next["id"],
                    "key" : key,
                    "address" : self.next["address"],
                    "nodeAddress" : self.next["nodeAddress"]
                }
        
    def computeFingerTable(self):
        # By finding the node responsible for the fingertable entry,
        # a node can build its fingertable
        print("\n---------------------BUILDING FINGER TABLE--------------------")
        print("NODEID: ", self.id)
        print("SUCCESSOR: ", self.next["id"])
        nextinfo = self.responsible(self.id+1)
        print("NEXTINFO: ", nextinfo)
        self.fingertable = []
        sock = context.socket(zmq.REQ)
        sock.connect(tcpstr + nextinfo["address"])
        self.fingertable.append({
            "prev" : nextinfo["prev"],
            "id" : nextinfo["id"],
            "address" : nextinfo["address"],
            "nodeAddress" : nextinfo["nodeAddress"],
            "sok" : sock
            })
        for bit in range(bits):
            entry = (self.id + 2**bit) % (2**bits) 
            print("Checking: ", entry)
            entryresp = self.responsible(entry)
            print(entryresp)
            while not entryresp["found"]:
                print("CONNECTING")
                self.query.connect(tcpstr + entryresp["address"])
                prevaddress = tcpstr + entryresp["address"]
                print("CONNECTED")
                self.query.send_json({
                "op" : "responsible",
                "id" : entry
                })
                # print("FT SENT")
                entryresp = self.query.recv_json()
                self.query.disconnect(prevaddress)  
                print(entryresp)


            print("RESP ID: ", entryresp["id"])
            sock = context.socket(zmq.REQ)
            sock.connect(tcpstr + entryresp["address"])
            newentry = {"prev" : entryresp["prev"],
            "id" : entryresp["id"],
            "address" : entryresp["address"],
            "nodeAddress" : entryresp["nodeAddress"],
            "sok" : sock
            }
            notintable = True 
            for nodeentry in self.fingertable:
                if nodeentry["id"] == newentry["id"]:
                    notintable = False
            if notintable and entryresp["found"] and entryresp["id"] != self.id:
                self.fingertable.append(newentry)
        self.lastfingerupdate = time.time()
        print("---------------------------FINGERTABLE---------------------------")
        print(self.fingertable)
        print("\n-------------------------BUILD FINISHED-------------------------")

    def predecessor(self):
        return {"id": self.prev["id"], "address": self.prev["address"]}
    def successor(self):
        return {"id": self.next["id"], "address": self.next["address"]}
    def __str__(self):  
        if self.id < (1024**10):
            id = self.id 
            prev = self.prev["id"]
        else:
            id = self.id // (1024**10)
            if  self.prev["id"] != None: 
                prev = self.prev["id"] // (1024**10)
            else:
                prev = None

        #str overwrite so printing the object prints interval
        if self.prev["id"] and self.prev["id"] > self.id:
            return "({}, {}] U [{}, {}]".format(
                prev, 0,0, id)
        else:
            return "({}, {}]".format(prev, id)

    def debugTemplate(self):
        info = {
            "id": self.id,
            "predecessor" : self.prev["id"],
            "successor" : self.next["id"],
            "interval" : str(self)
        }
        return info

    def upload(self, request, querysocket):
        try:
            with open("files/" + request["filename"], "wb") as f:
                f.write(request["bytes"].encode('iso8859-15')) #Reconversion from string to bytes
            f.close()
            print("File {} saved succesfully".format(request["filename"]))
            querysocket.send_json({
                "op" : "update",
                "message" : self.uploadmessage
            })
            if self.debugger != None:
                self.debugger.send_json({
                "op" : "update",
                "message" : self.uploadmessage,
                "info" : self.debugTemplate(),
                "key" : request["filename"]
                })
        except Exception as e:
            print("Something went wrong: ")
            print(e)
            querysocket.send_json({
                "op" : "update",
                "message" : self.fatalerrormessage,
                "exception" : str(e)
            })
            if self.debugger != None:
                self.debugger.send_json({
                "op" : "update",
                "message" : self.fatalerrormessage,
                "exception" : str(e),
                "info" : self.debugTemplate()
            })
    def download(self, request, querysocket):
        try:
            with open("files/" + request["filename"], "rb") as f:
                reply = {
                    "op" : "download",
                    "bytes" : f.read().decode('iso8859-15')
                }
            f.close()
            querysocket.send_json(reply)
            if self.debugger != None:
                self.debugger.send_json({
                    "op" : "download",
                    "message" : "Successful download",
                    "info" : self.debugTemplate()
                }) 
        except Exception as e:
            print("Something went wrong: ")
            print(e)
            querysocket.send_json({
                "op" : "error",
                "message" : self.fatalerrormessage,
                "exception" : str(e)
            })
            if self.debugger != None:
                self.debugger.send_json({
                "op" : "error",
                "message" : self.fatalerrormessage,
                "exception" : str(e),
                "info" : self.debugTemplate()
            })

    def transfer(self, request, querysocket):
        try:
            files = os.listdir("files")
            for filename in files:
                key = ntpath.splitext(filename)[0]
                if bits == 512:
                    key = int(key,16) 
                else:
                    key = int(key)
                if key < request["id"]:
                    with open("files/" + filename, "rb") as f:
                        querysocket.send_json({
                            "op" : "upload",
                            "filename" : filename,
                            "bytes": f.read().decode('iso8859-15')
                        })
                    f.close()
                    if self.debugger != None:
                        self.debugger.send_json({
                            "op" : "update",
                            "message":"File transferred succesfully",
                            "info" : self.debugTemplate()
                        })
                    os.remove("files/"+filename)
        except Exception as e:
            print("Something went wrong: ")
            print(e)
            if self.debugger != None:
                self.debugger.send_json({
                "op" : "update File transfer",
                "message" : self.fatalerrormessage,
                "exception" : str(e),
                "info" : self.debugTemplate()
            })
    
    def handleRequests(self, request, querysocket):
        print(request)
        if self.debugger:
            self.debugger.send_json({
                "request" : request,
                "recipient" : self.id
            })
    
        # Facade for handling message requests.
        # Opcodes are:
        # infoRequest => Request basic info from recipient Node
        # infoSuccesor => Request info of recipient Node's succesor
        # infoPredecessor => Request info of recipient Node's predecessor 
        # claimSuccession => Message to notify a Node to change succession to
        #                    the sender Node's address
        # claimPredecessor => Message to notify a Node to change predecessor to
        #                    the sender Node's address
        # update => An update message
        # responsible => Request to find responsible for an id

        if request["op"] not in self.opcodes:
            querysocket.send_json({
                "op": "Error",
                "message" : self.errormessage
            })
            if self.debugger != None:
                self.debugger.send_json({
                    "op": "Error",
                    "message" : self.errormessage,
                    "info" : self.debugTemplate()
                })
        elif request["op"] == "transfer":
            self.transfer(request, querysocket)
        elif request["op"] == "upload":
            self.upload(request, querysocket)
        elif request["op"] == "download":
            self.download(request, querysocket)
        elif request["op"] == "responsible":
            querysocket.send_json(self.responsible(request["id"]))
        elif request["op"] == "infoRequest":
            querysocket.send_json({
                "prev" : self.prev["id"],
                "id" : self.id,
                "address": self.address,
                "nodeAddress": self.nodeAddress
            })
            if self.debugger:
                self.debugger.send_json({
                    "info" : self.debugTemplate()
                })
        elif request["op"] == "infoSuccessor":
            if self.next["id"]:
                querysocket.send_json({
                    "id" : self.next["id"],
                    "trueNext" : True,
                    "address": self.next["address"],
                    "nodeAddress": self.next["nodeAddress"]
                })
            else: 
                querysocket.send_json({
                "trueNext" : False,
                "id" : self.id,
                "address": self.address,
                "nodeAddress": self.nodeAddress
                })
            if self.debugger:
                self.debugger.send_json({
                    "info" : self.debugTemplate()
                })
        elif request["op"] == "infoPredecessor":
            print("PRED: ", self.prev)
            if self.prev["id"]:
                querysocket.send_json({
                    "id" : self.prev["id"],
                    "address": self.prev["address"],
                })
            else:
                querysocket.send_json({
                "id" : self.id,
                "address": self.address,
                "nodeAddress": self.nodeAddress
                })
            if self.debugger:
                self.debugger.send_json({
                    "info" : self.debugTemplate()
                })
        elif request["op"] == "claimSuccession":
            if self.next["id"]:
                try:
                    self.next["sok"].disconnect(tcpstr+self.next["nodeAddress"])
                    print("SUCC DISCONNECTED")
                except Exception as e:
                    print("EXCEPTION: ", e)
             
            self.next["id"] = request["id"]
            self.next["address"] = request["address"]
            self.next["nodeAddress"] = request["nodeAddress"]
            print("CONNECTING TO NEW SUCCESSOR")
            self.next["sok"].connect(tcpstr+self.next["nodeAddress"])
            # print("SUCCESSOR CHECK")

            # self.next["sok"].send_json({"op" : "update", "message" : "SUCCESSOR CHECK"})
            if querysocket == self.client:
                querysocket.send_json({
                    "op" : "update",
                    "message" : self.claimnextmessage
                })
            print(self)
            if self.debugger != None:
                self.debugger.send_json({
                    "op" : "update",
                    "message" : self.claimnextmessage,
                    "Queryid" : request["id"],
                    "info" : self.debugTemplate()
                })
            if not self.fingertable:
                sock = context.socket(zmq.REQ)
                sock.connect(tcpstr + self.next["address"])
                self.fingertable.append({
                    "prev" : self.id,
                    "id" : self.next["id"],
                    "address" : self.next["address"],
                    "nodeAddress" : self.next["nodeAddress"],
                    "sok" : sock
                })
        elif request["op"] == "claimPredecessor":
            print("PREV_ID => ", self.prev["id"])
            if self.prev["id"]:
                print("CP SENDING - 1")
                self.prev["sok"].send_json({
                    "op" : "claimSuccession",
                    "id" : request["id"],
                    "nodeAddress": request["nodeAddress"],
                    "address" : request["address"]
                })
                print("CP SENDING - 2")

                self.prev["sok"].send_json({"op": "updateFingers"})    
                
            
            self.prev["id"] = request["id"]
            self.prev["address"] = request["address"]
            querysocket.send_json({
                "op" : "update",
                "message" : self.claimprevmessage
            })
            print(self)
            if self.debugger != None:
                self.debugger.send_json({
                    "op" : "update",
                    "message" : self.claimprevmessage,
                    "Queryid" : request["id"],
                    "info" : self.debugTemplate()
                })
        elif request["op"] == "updateFingers":
            if querysocket == self.client:
                querysocket.send_json({"op" : "update", "message" : "Updating Fingertable"})
            if self.debugger:
                inf = self.debugTemplate()
                # self.debugger.send({
                #     "op" : "updateFingers",
                #     "info" : inf
                # })
            now = time.time()
            print("DIFF: TIME", now - self.lastfingerupdate,(now - self.lastfingerupdate) >= 0.1 )
            if (now - self.lastfingerupdate) >= 1: 
                self.lastfingerupdate = now
                print("Computing FingerTable")
                self.computeFingerTable()
                if self.fingertable:
                    print("BROADCASTING: ",self.fingertable)
                    print("________________________")
                    for node in self.fingertable:
                        if node["id"] != self.prev["id"]:
                            print(node)
                            node["sok"].send_json({"op" : "updateFingers"})
                            node["sok"].recv_json()

n = Node(id, root, client, debugger, predecessor)
if not root:
    n.joinRingCommunity(rootaddress)
else:
    if n.debugger != None: 
        n.debugger.send_json({
            "op" : "++"
        })
if n.debugger != None:
    pingThread = threading.Thread(target=n.ping)
    pingThread.daemon = True
    pingThread.start()
while True:
    try:
        socks = n.poll()
    except KeyboardInterrupt:
        break
    if n.clientsock() in socks:
        print("**************** CLIENT ****************")
        msg = n.clientsock().recv_json()
        n.handleRequests(msg, n.clientsock()) 
        print(n)
        print(n.id // (1024 ** 10))
        print("**************** NOT BLOCKED || CLIENT ****************")
    if n.predsock() in socks:
        print("**************** PREDECESSOR ****************")

        msg = n.predsock().recv_json()
        n.handleRequests(msg, n.predsock())
        print(n)
        print(n.id // (1024 ** 10))

        print("**************** NOT BLOCKED || PRED ****************")

    if n.succsock() in socks:
        print("**************** SUCCESSOR ****************")

        msg = n.succsock().recv_json()
        n.handleRequests(msg, n.succsock())
        print(n)
        print(n.id // (1024 ** 10))

        print("**************** NOT BLOCKED || SUCC ****************")
