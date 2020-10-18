import argparse
import zmq
import socket
import os.path
import hashlib
import random as rnd
import menupy
import time
import json
import io
from pygame import mixer # Load the required library

# CONSTANTS
port = 5545
chunksize = (1024**2) * 3 #1 MB
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
    chunksize = mb * args.chunksize
if args.proxy:
    proxy = args.proxy

# FUNCTIONS
mixer.init()


def getSongBytes(server):
    try:
        socket = ctx.socket(zmq.REQ)
        ip = server["ip"]
        port = server["port"]
        socket.connect("tcp://" + ip + ":" + str(port))
        filenames = server["files"]
        files = {}
        for f in filenames:
            print("apending bytes")
            socket.send_json({
                "origin": "client",
                "type": "download",
                "data": {"filename": f}
            })
            ans = socket.recv_json()
            if ans["status"] == "ok":
                files[f] = ans["data"]["bytes"].encode('iso8859-15')
            else:
                print("Error, ", ans)
        return files
    except Exception as e:
        print("Ocurrió un error al obtener la parte de la canción, ", e)

# CLASSES
class Client():
    def __init__(self):
        self.port = port
        self.ip = "localhost"
        self.printClientInfo()

    def printClientInfo(self):
        print("...Cliente inicializado...")
        print("Port:", port)
        print("Chunksize: {} MB".format(int(chunksize/1000000)))
        print("IP: {}".format(self.ip))

    def initializeProxySocket(self):
        try:
            self.proxySocket = ctx.socket(zmq.REQ)
            self.proxySocket.connect("tcp://" + proxy)
            print("..Proxy inicializado correctamente... {}".format("tcp://"+proxy))
        except Exception as e:
            print(e)

    def listSongs(self):
        print("..Listing..")
        self.proxySocket.send_json({
            "origin": "client",
            "type": "listrequest",
            "data": ""
        })
        rep = self.proxySocket.recv_json()
        if rep["status"] == "ok":
            return rep["data"]
        else:
            print("Ocurrio un error en el proxy", rep)
        return []

    def getSong(self, song):
        print("..Getting song..", song)
        self.proxySocket.send_json({
            "origin": "client",
            "type": "songrequest",
            "data": song
        })
        rep = self.proxySocket.recv_json()
        if rep["status"] == "ok":
            servers = rep["data"]
            songData = {}
            self.song = bytearray()
            for s in servers:
                songData.update(getSongBytes(s))
            for songpart in sorted(songData.keys()):
                self.song.extend(songData[songpart])
        else:
            print("Ocurrio un error en el proxy", rep)
            print(rep["data"]["message"])
            return False
        return True   

    def play(self, song):
        print("playing " + song)
        with open(".test.mp3", "wb") as f:
            f.write(self.song)
            f.close()
        
        mixer.music.load(".test.mp3")
        mixer.music.play()


client = Client()
client.initializeProxySocket()

mainMenu = menupy.OptionMenu("Reproductor", title_color="cyan")
mainMenu.add_option("Listar canciones")
mainMenu.add_option("Salir", color="red")

songsMenu = menupy.OptionMenu("Canciones disponibles", title_color="cyan")

playMenu = menupy.OptionMenu("Opciones de reproduccion", title_color="cyan")
playMenu.add_option("Continuar", color="green")
playMenu.add_option("Salir", color="red")
pauseMenu = menupy.OptionMenu("Opciones de reproduccion", title_color="cyan")
pauseMenu.add_option("Pausar")
pauseMenu.add_option("Salir", color="red")

result = mainMenu.run()

while result != "Salir":
    if result == "Listar canciones":
        for song in client.listSongs():
            songsMenu.add_option(song)
        songsMenu.add_option("Salir", color="red")
        pickedSong = songsMenu.run()
        if pickedSong != "Salir":
            ready=client.getSong(pickedSong)
            if ready:
                client.play(pickedSong)
                playOpt = pauseMenu.run()
                while playOpt != "Salir":
                    if playOpt == "Pausar":
                        print("Pausing")
                        mixer.music.pause()
                        opt = playMenu.run()
                        if opt != "Salir":
                            mixer.music.unpause()
                            playOpt = pauseMenu.run()
                        else:
                            playOpt = "Salir"


            else:
                print("Song not playable")
                result = "Salir"
        else:
            result = "Salir"
