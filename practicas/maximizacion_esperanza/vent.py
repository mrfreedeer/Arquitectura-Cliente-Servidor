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
import pandas as pd
import math

minNorm = 1
maxNorm = 3
deltaNorm = maxNorm-minNorm
# random.seed(0)
cols = [
            "imdbRating",
            "ratingCount",
            "duration",
            "year",
            "nrOfWins",
            "nrOfNominations",
            "nrOfPhotos",
            "nrOfNewsArticles",
            "nrOfUserReviews",
            "nrOfGenre",
            # "Action",
            # "Adult",
            # "Adventure",
            # "Animation",
            # "Biography",
            # "Comedy",
            # "Crime",
            # "Documentary",
            # "Drama",
            # "Family",
            # "Fantasy",
            # "FilmNoir",
            # "GameShow",
            # "History",
            # "Horror",
            # "Music",
            # "Musical",
            # "Mystery",
            # "News",
            # "RealityTV",
            # "Romance",
            # "SciFi",
            # "Short",
            # "Sport",
            # "TalkShow",
            # "Thriller",
            # "War",
            # "Western",
        ]
# np.random.seed(200)

'''
    El ventilador debe tomar/generar datos y repartilos a los trabajadores con mu, cov y pi aleatorios, 
    luego esperar las variables mu, cov y pi de los reducers y repetir este proceso hasta que exista
    una convergencia 
'''
# Init context
context = zmq.Context()

class Vent:
    def __init__(self, X, number_of_sources, iterations):
        self.iterations = iterations
        self.number_of_sources = number_of_sources
        self.X = X
        self.numpyX = np.array(X)
        self.mu = None
        self.pi = None
        self.cov = None
        self.XY = None
        self.mapperDataSize = 100
        self.mappers = context.socket(zmq.PUSH)
        self.mappers.bind("tcp://*:5557")

        self.sinkSocket = context.socket(zmq.PULL)
        self.sinkSocket.connect("tcp://localhost:5559")
    def identityMatrix(self, size, number=1):
        ident = [[0 if (i!=j) else number for i in range(size)] for j in range(size)]
        return ident
    def setRandomVariables(self):
        # print("BEFORE: ", self.X)
        for dim in range(len(self.X[0])):
            subSet = list(map(itemgetter(dim),self.X))
            minSet = min(subSet)
            # minSet = min(self.X[:,dim])
            maxSet = max(subSet)
            # maxSet = max(self.X[:,dim])
            for i in range(len(subSet)):
                if (maxSet != minNorm):
                    self.X[i][dim] = (((self.X[i][dim] - minSet) /(maxSet-minSet))*deltaNorm) + minNorm
                else:
                    self.X[i][dim] = maxNorm

        # print("AFTER: ", self.X)
        self.reg_cov = self.identityMatrix(len(self.X[0]), 1e-6)
        # print(self.reg_cov)
        # self.reg_cov = 1e-6*np.identity(len(self.X[0]))
        
        x,y = np.meshgrid(np.sort(self.numpyX[:,0]),np.sort(self.numpyX[:,1]))
        self.XY = np.array([x.flatten(),y.flatten()]).T

        self.mu = [[random.random()*maxNorm for i in range(len(self.X[0]))] for i in range(self.number_of_sources)]
        # print(self.mu)
        # print(np.random.randint(1,3,size=(self.number_of_sources,len(self.X[0])))) # This is a nxm matrix since we assume n sources (n Gaussians) where each has m dimensions
        self.cov = [self.identityMatrix(len(self.X[0]), .5) for i in range(self.number_of_sources)]
        # self.cov = np.zeros((self.number_of_sources,len(X[0]),len(X[0]))) # We need a nxmxm covariance matrix for each source since we have m features --> We create symmetric covariance matrices with ones on the digonal
        # for dim in range(len(self.cov)):
        #     np.fill_diagonal(self.cov[dim],5)
        self.pi = [(1/self.number_of_sources) for i in range(self.number_of_sources)]
        # self.pi = np.ones(self.number_of_sources)/self.number_of_sources # Are "Fractions"
        log_likelihoods = [] # In this list we store the log likehoods per iteration and plot them in the end to check if
                             # if we have converged
    def plotState(self):
        """Plot the initial state"""    
        print('..ploting state..')
        fig = plt.figure(figsize=(10,10))
        ax0 = fig.add_subplot(111)
        mu = np.array(self.mu)
        cov = np.array(self.cov)
        self.numpyX = np.array(self.X)
        reg_cov = np.array(self.reg_cov)
        print(cov)
        ax0.scatter(self.numpyX[:,0],self.numpyX[:,1])
        ax0.set_title('Initial state')
        for m,c in zip(mu,cov):
            c += reg_cov
            multi_normal = multivariate_normal(mean=m,cov=c)
            ax0.contour(np.sort(self.numpyX[:,0]),np.sort(self.numpyX[:,1]),multi_normal.pdf(self.XY).reshape(len(self.X),len(self.X)),colors='black',alpha=0.3)
            ax0.scatter(m[0],m[1],c='grey',zorder=10,s=100)
        plt.show()

    def toLists(self):
        if isinstance(self.mu, tuple):
            self.mu = self.mu[0]
        n_mu = [[float(j) for j in i] for i in self.mu]
        if isinstance(self.pi, tuple):
            self.pi = self.pi[0]
        n_pi = [float(i) for i in self.pi]
        # input("pi")
        if isinstance(self.cov, tuple):
            self.cov = self.cov[0]
        n_cov = []
        for x in self.cov:
            subset = []
            for number in x:
                subset.append([float(fck) for fck in number])
            n_cov.append(subset)
        
        n_regcov = []
        for x in self.reg_cov:
            subset = []
            for number in x:
                subset.append(float(number))
            n_regcov.append(subset)
            
        return n_mu, n_pi, n_cov, n_regcov
        
    
    def sendToMappers(self):
        print('..sending data to mappers..')
        ran = range(0, len(self.X), self.mapperDataSize)
        steps = int(len(self.X)/self.mapperDataSize)
        for i in range(steps):
            # Sends 100 elements to each mapper, for the whole dataset
            # Xtosendnumpy = self.X[ran[i]:ran[i+1]]
            # Xtosend = []
            Xtosend =  self.X[ran[i]:ran[i+1]]
            # for x in Xtosendnumpy:
            #     subset = []
            #     for number in x:
            #         subset.append(float(number))
            #     Xtosend.append(subset)
            # mu, pi, cov, regcov = self.toLists()
            # print("mu", mu, 
            # # "regcov", regcov, 
            # # "pi", pi, 
            # # "cov", cov,
            # # "xtosend", Xtosend
            # )
            print("x", Xtosend[0])
            print(type(self.mu), type(self.reg_cov), type(self.pi), type(Xtosend), type(self.cov))
            self.mappers.send_json({
                'mu': self.mu,
                'regcov' : self.reg_cov,
                'pi': self.pi,
                'x' : Xtosend,
                'cov': self.cov,
            })
            
    def receiveParams(self, params):
        print('..receiving params..')
        print("params mu", params["mu"])
        self.mu = params['mu']
        print("smu", vent.mu)
        self.pi = params['pi'] 
        self.cov = params['cov'] 
        self.reg_cov = params['reg_cov']

    def predict(self,Y):
        # PLot the point onto the fittet gaussians
        fig3 = plt.figure(figsize=(10,10))
        ax2 = fig3.add_subplot(111)
        ax2.scatter(self.X[:,0],self.X[:,1])
        for m,c in zip(self.mu,self.cov):
            multi_normal = multivariate_normal(mean=m,cov=c)
            ax2.contour(np.sort(self.X[:,0]),np.sort(self.X[:,1]),multi_normal.pdf(self.XY).reshape(len(self.X),len(self.X)),colors='black',alpha=0.3)
            ax2.scatter(m[0],m[1],c='grey',zorder=10,s=100)
            ax2.set_title('Final state')
            for y in Y:
                ax2.scatter(y[0],y[1],c='orange',zorder=10,s=100)
        prediction = []        
        for m,c in zip(self.mu,self.cov):  
            # print(c)
            prediction.append(multivariate_normal(mean=m,cov=c).pdf(Y)/np.sum([multivariate_normal(mean=mean,cov=cov).pdf(Y) for mean,cov in zip(self.mu,self.cov)]))
        plt.show()
        return prediction
    def plotLog(self, log_likelihoods, iterations):
        fig2 = plt.figure(figsize=(10,10))
        ax1 = fig2.add_subplot(111) 
        ax1.set_title('Log-Likelihood')
        ax1.plot(range(0,iterations,1),log_likelihoods)
        plt.show()

iterations = 30
clusters = 3

def initializeDataSet(src = 'blobs', dimensions = 3, cluster_std = 0.4, n_samples = 501, clusters = 3):
    print('...initializing data set...')
    print('from csv: ', src)
    if (src == 'blobs'):
        print('from blobs')
        # Create dataset
        X,Y = make_blobs(cluster_std = cluster_std, n_features=dimensions, n_samples = n_samples , centers = clusters)
        data = []
        for i in X:
            data.append(list(i))
        # Stratch dataset to get ellipsoid data
        # X = np.dot(X, np.random.RandomState(0).randn(2,2))
    if (src == 'csv'):
        df = pd.read_csv('datasets/imdb.csv', usecols = cols, nrows=n_samples)
        data = []
        for i in range(df.shape[0]):
            obj = df.iloc[i, :]
            tmp = []
            for v in obj.values:
                n = 1
                if isinstance(v, str) and v.isdigit():
                    n = float(v)
                tmp.append(n)
            data.append(tmp)

        # print(data) 
        # X = np.array(data)
        # X = X[0:501]
        # print(X)
        # input()
    return data



X = initializeDataSet(src = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != None else 'blobs',
    dimensions = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] != None else 2,
    n_samples=int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3] != None else 501
)


vent = Vent(X, clusters, iterations)
vent.setRandomVariables()
# vent.plotState()
# print("vent X shape: ", vent.X.shape)
tstart = time.time()
vent.sendToMappers()

log_likelihoods = []
converged = False
i = 0

while(not converged):
    print('..iteration: ', i, '..')
    print("smu", vent.mu)             
    vent.receiveParams(vent.sinkSocket.recv_json())
    print("smu", vent.mu)             
    
    """Log likelihood"""
    if isinstance(vent.mu, tuple):
        vent.mu = vent.mu[0]
    if isinstance(vent.pi, tuple):
        vent.pi = vent.pi[0]
    if isinstance(vent.cov, tuple):
        vent.cov = vent.cov[0]
    print(len(vent.mu[0]))
    print(len(vent.cov[0]))
    print(len(X[0]))
    print(len(vent.pi))
    log_likelihoods.append(np.log(np.sum([k*multivariate_normal(vent.mu[i],vent.cov[j]).pdf(X) for k,i,j in zip(vent.pi,range(len(vent.mu)),range(len(vent.cov)))])))
    print("log_likelihoods delta")
    if len(log_likelihoods)> 1:
        if (log_likelihoods[-1] - log_likelihoods[-2]) < 0.000000000000000000009:
            converged = True
    vent.sendToMappers()
    if i == 100:
        converged = True
    i+=1
vent.receiveParams(vent.sinkSocket.recv_json())
tend = time.time()
print("TRAINING TIME:", tend-tstart)
print("log likelihood", log_likelihoods)
vent.plotLog(log_likelihoods, i)
if isinstance(vent.mu, tuple):
        vent.mu = vent.mu[0]
if isinstance(vent.pi, tuple):
    vent.pi = vent.pi[0]
if isinstance(vent.cov, tuple):
    vent.cov = vent.cov[0]
# vent.plotState()
# print(vent.predict([[10,15]]))