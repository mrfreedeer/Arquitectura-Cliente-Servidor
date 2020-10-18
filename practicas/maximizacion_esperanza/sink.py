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
workerSocket = context.socket(zmq.PULL)
workerSocket.bind("tcp://*:5558")

ventSocket = context.socket(zmq.PUSH)
ventSocket.bind("tcp://*:5559")
class Sink:
    def __init__(self, X, r_ic):
        # print('..initializing sink..')
        self.X = X
        self.mu = None
        self.pi = None
        self.cov = None
        self.reg_cov = 1e-6*np.identity(len(self.X[0]))
        self.r_ic = r_ic
        self.XY = None
        self.mapperDataSize = 101

    def Mstep(self):
        """M Step"""
        self.mu = []
        self.cov = []
        self.pi = []
        log_likelihood = []
        for c in range(len(self.r_ic[0])):
            m_c = np.sum(self.r_ic[:,c],axis=0)
            mu_c = (1/m_c)*np.sum(self.X*self.r_ic[:,c].reshape(len(self.X),1),axis=0)
            self.mu.append(mu_c)
            # Calculate the covariance matrix per source based on the new mean
            self.cov.append(((1/m_c)*np.dot((np.array(self.r_ic[:,c]).reshape(len(self.X),1)*(self.X-mu_c)).T,(self.X-mu_c)))+self.reg_cov)
            # Calculate pi_new which is the "fraction of points" respectively the fraction of the probability assigned to each source 
            self.pi.append(m_c/np.sum(self.r_ic)) # Here np.sum(r_ic) gives as result the number of instances. This is logical since we know 
                                            # that the columns of each row of r_ic adds up to 1. Since we add up all elements, we sum up all
                                            # columns per row which gives 1 and then all rows which gives then the number of instances (rows) 
                                            # in X --> Since pi_new contains the fractions of datapoints, assigned to the sources c,
                                            # The elements in pi_new must add up to 1
        mu, pi, cov, regcov = self.toLists()
        print(mu)
        return {
            'mu': mu,
            'cov': cov,
            'pi': pi,
            'reg_cov': regcov
        }
        
    def sendToVent(self, params):
        # print('..sending data to vent..')
        ventSocket.send_json(params)
    
    def toLists(self):
        n_mu = []
        for x in self.mu:
            n_mu.append(list(map(float, x)))
        # print("type of n_mu", type(n_mu[0]))

        n_pi = [i for i in self.pi]
        print(n_pi)
        # input("pi")
        n_cov = []
        for c in self.cov:
            k = []
            for subset in c:
                x = list(subset)
                k.append(x)
            n_cov.append(k)
        n_regcov = []
        for x in self.reg_cov:
            n_regcov.append(list(x))

        return n_mu, n_pi, n_cov, n_regcov




n_samples = 5 # Number of samples took from the data
n_samples = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] != None else 1
samples_received = 0
ric = np.empty((101,3))
X = np.empty((101,2))
while True:
    msg = workerSocket.recv_json()
    # print(msg)
    # print('..Ric Received.. Samples received: ', samples_received+1, 'expecting: ', n_samples)
    if samples_received+1 == n_samples:
        # print('..start m step..')
        sink = Sink(X,ric)
        sink.sendToVent(sink.Mstep())
        samples_received = 0
    else:
        samples_received += 1
        if samples_received == 1:
            X = msg['X']
            ric = msg['ric']
        else:
            X = np.concatenate((X, msg['X']))
            ric = np.concatenate((ric,  msg['ric']))
