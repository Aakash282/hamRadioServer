import os
import os.path as path
import numpy as np

#from hamRadioServer import echonest_dictionary_functions as edf

batch_size = 2
seq_length = 10
num_attr = 9

class PlayList(object):
    """ PlayList dataset for training a RNN on a set of playlists for 
        playlist generation """

    # Directory with file for each user containing playlist per line
    dataDir = path.dirname(path.dirname(path.dirname(path.realpath(__file__)))) + '/userData/'
    user_paths = os.listdir(dataDir)

    def __init__(self):
        self.attributes = loadEchonestAttributes()

    def load_split(self, split):
        seqs = self.create_sequences(self.load_user_playlists('mzubia315'))
        X = np.zeros((seq_length * num_attr, len(seqs)))
        Y = np.zeros(X.shape)
        for i, seq in enumerate(seqs):
            X[:, i] = np.asarray([self.attributes[song_id] for song_id in seq])
        Y[:-1, :] = X[1:, :]
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
        playlists = [filter(lambda x: x != '<nil>' and x in self.attributes, playlist) for playlist in playlists]
        # Filter out short playlists
        playlists = [playlist for playlist in playlists if len(playlist) >= seq_length]
        if len(playlists) == 0:
            print "No valid playlists for user file %s" %user_file
        return playlists

    def load_user_playlistss(self):
        return [self.load_user_playlists(user_file) for user_file in self.user_paths]

def loadEchonestAttributes():
    # Filename of database
    database_file = path.dirname(path.dirname(path.dirname(path.realpath(__file__)))) + '/data/track_ids60_atts.csv'

    # Dictionary structure to be filled and returned
    echonest_attributes = {}
    database = open(database_file, 'r')
    for line in database:
        row = line.rstrip().split(',') # Removes \n character and splits on ','
        values = [] # List that will contain all 8 attributes for a given track_id
        for i in range (1, 14):
            # If echonest has a valid attribute
            if row[i] != 'None':
                values.append(float(row[i]))

            # If no parameter received from echnoest, set to inf
        else: 
            values.append(float('inf')) 
        echonest_attributes[row[0]] = values # Add track_id : attributes to dictionary
        database.close()
        return echonest_attributes

# For testing purposes
if __name__ == '__main__':
    pl = PlayList()
    print "Loading users from ", pl.dataDir
    print "Users are ", pl.user_paths
    #playlist = pl.load_user_playlists('2013ssahu')[0]
    # print playlist
    # print pl.create_sequences([playlist])
    print pl.load_split('train')
