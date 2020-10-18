import string
import random
import hashlib
import zmq
import time
import sys
from random import sample
from operator import itemgetter
import matplotlib.pyplot as plt
from matplotlib import style
style.use('fivethirtyeight')
from sklearn.datasets.samples_generator import make_blobs
import numpy as np
from scipy.stats import multivariate_normal
import json
from io import StringIO
import pickle
# np.random.seed(200)

'''
    El ventilador debe tomar/generar datos y repartilos a los trabajadores con mu, cov y pi aleatorios, 
    luego esperar las variables mu, cov y pi de los reducers y repetir este proceso hasta que exista
    una convergencia 
'''
# Init context
context = zmq.Context()
ventSocket = context.socket(zmq.PULL)
ventSocket.connect("tcp://localhost:5557")
sinkSocket = context.socket(zmq.PUSH)
sinkSocket.connect("tcp://localhost:5558")
class Worker:
    def __init__(self, X, mu, pi, cov, reg_cov):        
        self.X = np.array(X)
        self.mu = np.array(mu)
        self.pi = np.array(pi)
        self.cov = np.array(cov)
        self.reg_cov = np.array(reg_cov)
        self.XY = None
        self.mapperDataSize = 101

    def Estep(self):
        """E Step"""
        r_ic = np.zeros((len(self.X),len(self.cov)))
        for m,co,p,r in zip(self.mu,self.cov,self.pi,range(len(r_ic[0]))):
            print('x: ', self.X)
            print('m: ', m)
            co+= self.reg_cov
            print('co: ', co)
            mn = multivariate_normal(mean=m,cov=co)
            r_ic[:,r] = p*mn.pdf(self.X)/np.sum([pi_c*multivariate_normal(mean=mu_c,cov=cov_c).pdf(self.X) for pi_c,mu_c,cov_c in zip(self.pi,self.mu,self.cov+self.reg_cov)],axis=0)
        print(r_ic)
        return r_ic
        



    def sendToSink(self, ric):
        print('Sending ric to sink (reducer)')
        print('..ric shape..', ric.shape)
        X = self.X
        print("x",type(list(X[0])))
        print("ric",type(list(ric[0])))
        sinkSocket.send_json({
            'ric': [list(i) for i in ric],
            'X': [list(i) for i in X]
        })


while True:
    msg = ventSocket.recv_json()
    print('...data received...')
    worker = Worker(
        msg['x'], 
        msg['mu'], 
        msg['pi'], 
        msg['cov'], 
        msg['regcov']
        )
    ric = worker.Estep()
    worker.sendToSink(ric)