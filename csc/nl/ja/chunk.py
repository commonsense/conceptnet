from csc.nl.ja.debug import *
from csc.nl.ja.util  import *
from csc.nl.ja.tree  import *

import MeCab
import CaboCha
import re

class JaChunk(JaTreeBranch, JaLanguageNode):
    ''' Represents a single chunk inside an utterance
    A chunk contains one or more words, each of which contain one or more tokens.
    This should only be called from JaUtterance, as it assumes that the text given has been cleaned properly.
    Right now, this class is essentially a tree parser for CaboCha with some extra functionality.
    '''

    def __init__(self, cabocha_chunk, children):
        JaTreeBranch.__init__(self)

        self.score = cabocha_chunk.score # No need for this...? #

        self.children = children
        for child in self.children:
            child.parent = self

    def __str__(self):
        return self.surface

    dump_lines = JaDebug.dump_lines_chunk

    @shared_property
    def is_chunk(self):
        ''' Always True '''
        return True

