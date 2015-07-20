import os
import os.path as path
import numpy as np
import logging
from sklearn import preprocessing

from rnn import RNN
from lstm import LSTM
from affine import Affine
from softmax import Softmax
from crossentropy import Crossentropy
from rms_prop import RMSProp
from neon.params.val_init import UniformValGen
from neon.backends import CPU

# Initialize GPU backend
from pycuda import autoinit
from nervanagpu import NervanaGPU
backend = NervanaGPU()
#backend = CPU(rng_seed=0)

logger = logging.getLogger('char-rnn')

init = lambda size: np.random.uniform(low=-0.08, high=0.08, size=size)

batch_size = 32
seq_length = 10
num_attr = 13
hidden_size = 128

class PlayList(object):
    """ PlayList dataset for training a RNN on a set of playlists for 
        playlist generation """

    # Directory with file for each user containing playlist per line
    dataDir = path.dirname(path.dirname(path.dirname(path.realpath(__file__)))) + '/userData/'
    user_paths = os.listdir(dataDir)

    def __init__(self):
        self.attributes, self.song_index = loadEchonestAttributes()
        self.attributes = self.normalize(self.attributes)
        splits = ('train', 'test')
        self.inputs = {split:None for split in (splits)}
        self.targets = {split:None for split in (splits)}
        self.batch_idx = 0
        self.dtype = np.float32

    def find_normalize_constants(self):
        scaler = preprocessing.StandardScaler()
        scaler.fit(self.attributes)
        np.savetxt('means.txt', scaler.mean_)
        np.savetxt('std.txt', scaler.std_)

    def normalize(self, X):
        try:
            scaler = preprocessing.StandardScaler()
            scaler.mean_ = np.loadtxt('means.txt')
            scaler.std_ = np.loadtxt('std.txt')
        except IOError:
            print "Normalizing constants not found."
            print "Finding constants now. Run script again."
            self.find_normalize_constants()
        return scaler.transform(X)

    def next(self):
        start = self.batch_idx * batch_size
        end = (self.batch_idx+1) * batch_size
        self.batch_idx += 1
        if self.batch_idx == self.num_batches:
            self.batch_idx = 0
        return self.inputs['train'][:, start:end], self.targets['train'][:, start:end]

    def load_split(self, split):
        seqs = self.create_sequences(self.load_user_playlists('spotify'))
        if len(seqs) == 0:
            print "No seqs found"
            return
        print "Loading %d sequences and %d songs" %(len(seqs), sum([len(seq) for seq in seqs]))
        # Each col of X is a sequence of 10 songs
        X = np.zeros((seq_length * num_attr, len(seqs)))
        Y = np.zeros(X.shape)
        for i, seq in enumerate(seqs):
            X[:, i] = np.hstack([val for song_id in seq for val in self.attributes[self.song_index[song_id], :]])
        Y[:-1, :] = X[1:, :]
        # TODO Deal with end of Y
        self.num_batches = len(seqs) // batch_size
        #devX = backend.zeros(X.shape, dtype=self.dtype)
        self.inputs[split] = backend.array(X, dtype=self.dtype)
        self.targets[split] = backend.array(Y, dtype=self.dtype)
        return X, Y 

    def create_sequences(self, playlists):
        """ Create list of sequence of songs from playlists """
        num_seqs = [len(playlist) // seq_length for playlist in playlists]
        seqs = []
        for playlist, seq in zip(playlists, num_seqs):
            for i in range(seq):
                seqs.append(playlist[i*seq_length:(i+1)*seq_length])
        #seqs = [playlist[i*seq_length:(i+1)*seq_length] for (playlist, seq) in zip(playlists, num_seqs) for i in range(seq)]
        return seqs

    def load_user_playlists(self, user_file):
        """ Loads in a user's playlists and returns list of lists of playlists"""
        with open(self.dataDir + user_file, 'r') as f:
            playlists = [line[line.find('[')+1:line.find(']')].split() for line in f]
        # Filter out nil songs or songs not in attributes
        playlists = [filter(lambda x: x != '<nil>' and x in self.song_index, playlist) for playlist in playlists]
        # Filter out short playlists
        playlists = [playlist for playlist in playlists if len(playlist) >= seq_length]
        if len(playlists) == 0:
            print "No valid playlists for user file %s" %user_file
        return playlists

    def load_user_playlistss(self):
        return [self.load_user_playlists(user_file) for user_file in self.user_paths]

def loadEchonestAttributes():
    # Filename of database
    database_file = path.dirname(path.dirname(path.dirname(path.realpath(__file__)))) + '/data/attributes.txt'

    # Dictionary structure to be filled and returned
    attributes = []
    song_index = {}
    database = open(database_file, 'r')
    for index, line in enumerate(database):
        row = line.rstrip().split(',')
        # TODO Deal with None's
        attributes.append([float(row[i]) if row[i] != 'None' else 0 for i in range(1, num_attr+1)])
        song_index[row[0]] = index
    database.close()
    return np.asarray(attributes), song_index

def construct_model():

    lstm1 = LSTM(num_attr, hidden_size, batch_size, seq_length, init, backend)
    lstm2 = LSTM(hidden_size, hidden_size, batch_size, seq_length, init, backend)
    affine = Affine(hidden_size, num_attr, batch_size, seq_length, init, backend)
    softmax = Softmax(num_attr, batch_size, seq_length, backend)
    layers = [lstm1, lstm2, affine, softmax]
    cost = Crossentropy(num_attr, batch_size, seq_length, backend)

    update = RMSProp(backend)

    model = RNN(layers, cost, update)

    return model

def train():
    dataset = PlayList()
    dataset.load_split('train')
    model = construct_model()
    model.fit(dataset, 10)

if __name__ == '__main__':
    train()
