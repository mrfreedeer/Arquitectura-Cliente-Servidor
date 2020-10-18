import simpleaudio as sp
import zmq
import io
import io
import pyaudio, wave, sys, time
BUFFER_SIZE = 1024
ctx = zmq.Context()
s = ctx.socket(zmq.REP)
s.bind("tcp://*:5555")

chunk = 1024  # Record in chunks of 1024 samples
sample_format = pyaudio.paInt16  # 16 bits per sample
channels = 2
fs = 44100  # Record at 44100 samples per second

# create an audio object
p = pyaudio.PyAudio()

# open stream based on the wave object which has been input.
stream = p.open(format=sample_format,
                channels=channels,
                rate=fs,
                frames_per_buffer=chunk,
                output=True)

while True:
    req = s.recv()
    time.sleep(2)
    if req:
        stream.write(req)
    s.send(b'')