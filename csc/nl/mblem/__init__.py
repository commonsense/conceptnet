import cPickle as pickle
import os

mblem_base = os.path.dirname(__file__)

def get_mblem(lcode):
    filename = mblem_base+'/'+lcode+'.mblem.pickle'
    f = open(filename, 'rb')
    trie = pickle.load(f)
    f.close()
    return trie

def get_unlem(lcode):
    filename = mblem_base+'/'+lcode+'.unlem.pickle'
    f = open(filename, 'rb')
    unlem = pickle.load(f)
    f.close()
    return unlem

