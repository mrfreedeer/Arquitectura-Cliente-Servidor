import zmq
import pyaudio
import wave
import time


ctx = zmq.Context()
s = ctx.socket(zmq.REQ)

s.connect("tcp://localhost:5555")

chunk = 1024  # Record in chunks of 1024 samples
sample_format = pyaudio.paInt16  # 16 bits per sample
channels = 2
fs = 44100  # Record at 44100 samples per second

p = pyaudio.PyAudio()  # Create an interface to PortAudio

print('Recording')

stream = p.open(format=sample_format,
                channels=channels,
                rate=fs,
                frames_per_buffer=chunk,
                input=True)

frames = []  # Initialize array to store frames
cont = 0

while True:
    cont = cont + 1
    data = stream.read(chunk)
    s.send(data)
    stream.close()
    s.recv()
