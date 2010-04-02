from csc.nl.ja.debug import *
from csc.nl.ja.util  import *
from csc.nl.ja.tree  import *

import MeCab
import CaboCha
import re

class JaUtterance(JaTreeBranch, JaLanguageNode):
    ''' Represents an entire utterance '''

    def __init__(self, children):
        JaTreeBranch.__init__(self)
        self.children  = children

        for child in self.children:
            child.parent = self

    dump_lines = JaDebug.dump_lines_utterance

    def __str__(self):
        return self.surface

    @shared_property
    def is_utterance(self):
        return True

from csc.nl.ja.chunk  import *
from csc.nl.ja.cabocha_token  import *
from csc.nl.ja.parser import *

