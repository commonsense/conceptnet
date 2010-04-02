#python-encoding: UTF-8

from csc.nl.ja.debug import *
from csc.nl.ja.util  import *
from csc.nl.ja.tree  import *

import MeCab
import CaboCha
import re

'''
--- Notes ---

- JaUtterance is the basic tree structure used in NLP processing
Structure:
  JaUtterance:
      Represents:
          The top level of a tree representing an utterance.

      Contains:
          - JaChunk list (self.children)
          - JaToken list (self.tokens) [Original, unparsed token list]

  JaChunk:
      Represents:
          A parsed section of an utterance (gramattical in nature).

      Contains:
          - Mixed tree of JaWord/JaToken/other objects (self.children)

  JaWord:
      Represents:
          A single gramatical object.

      Contains:
          - Mixed tree of JaWord/JaToken/other objects (self.children)

- word tokens do not cross chunk boundaries, making this a strict tree.
- Each token/words/chunk object in each list are shared references.
  (that is, only one object reperesenting a particular token/word/chunk exists per utterance.
However, the lists themselves are unique.
- All objects implment __str__ such that they can be converted to their string representations
  by str(obj)
  - All string conversions are guaranteed to have piecemeal equality.  (That is, the string
    of any higher representation (utterance, chunk, word) is guaranteed to be equal to the
    join of the strings of its ordered component objects (chunk, word, token).
- Each class has a .dump() function that is useful for getting information about them.
  - .dump(True) returns vt100 colorized output <-- highly recommended
'''

'''
--- A word on properties ---

- The properties of JaToken do their best to identify token properties as well as distinguish
   part-of-speach.  However, in some cases, like in the case of na-adjectives used as nouns, 
   such as in the following, it is difficult:
       彼女の帽子が素敵だった。 (kanojyo no boushi ga suteki datta.)
  In this case, I try to wrangle it as best I can, and choose to prevent it from being classified
  as a noun, and push it into a na-adjective only category.
  Any formal grammar based off this data will have to either account for this, or add your own
  checks on token.pos_string, where you can query the actual data returned.
'''

from csc.nl.ja.parser import *
from csc.nl.ja.utterance import *
from csc.nl.ja.cabocha_token import *
from csc.nl.ja.word import *
from csc.nl.ja.chunk import *

