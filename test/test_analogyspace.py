from nose.tools import *
from csc.conceptnet4.analogyspace import *

def test_basic_analogyspace():
    mat = conceptnet_2d_from_db('en', cutoff=15)
    item = mat.iteritems().next()
    key, value = item
    concept1, feature = key
    filled_side, relation, concept2 = feature
    assert filled_side in ['left', 'right']
    assert relation[0] == relation[0].upper()
    
