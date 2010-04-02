#python-encoding: UTF-8

from csc.nl.ja.debug import *
from csc.nl.ja.util  import *
from csc.nl.ja.tree  import *

import MeCab
import CaboCha
import re

class JaWord(JaTreeBranch, JaLanguageNode):
    ''' Represents a single word inside a chunk/utterance
    This should only be called from JaUtterance, as it assumes that the text given has been cleaned properly.
    '''

    def __init__(self, args):
        JaTreeBranch.__init__(self)

        self.children = args
        for child in self.children:
            child.parent = self

    @property
    def stem(self):
        ''' Returns the stem of this word as a string
            This is a default, AND SHOULD BE OVERRIDEN IN THE CHILD CLASS.
        '''
        return self.children[0].stem

    @property
    def inflection(self):
        ''' Returns the inflection of this word as a string
            This is a default, AND SHOULD BE OVERRIDEN IN THE CHILD CLASS.
        '''
        return ""

    def __str__(self):
        return self.surface

    dump_lines = JaDebug.dump_lines_word

    @shared_property
    def is_stopword(self):
        ''' True if this word is a stopword
            This is a default, AND SHOULD BE OVERRIDEN IN THE CHILD CLASS.
        '''
        return self.children[0].is_stopword

    @shared_property
    def is_word(self):
        ''' Always true '''
        return True

    @property
    def lemma_form(self):
        ''' Returns the lemma form of this word as a string
            This is a default, AND SHOULD BE OVERRIDEN IN THE CHILD CLASS.
        '''
        return str().join([ x.lemma_form for x in self.children ])

    @property
    def root(self):
        ''' Returns the root portion of the word as a list
            This is a default, AND SHOULD BE OVERRIDEN IN THE CHILD CLASS.
        '''
        return self.children[:]

    @property
    def suffixes(self):
        ''' Returns the suffix portion of the word as a list
            This is a default, AND SHOULD BE OVERRIDEN IN THE CHILD CLASS.
        '''
        return []

class JaDependantKoto(JaWord):
    ''' Dependant koto instance '''

    def __init__(self, args):
        # Argument is a single JaWord object wrapped in a list #
        JaWord.__init__(self, args[0].children)

    def is_stopword(self):
        return True

class JaDependantMono(JaWord):
    ''' Dependant mono instance '''

    def __init__(self, args):
        # Argument is a single JaWord object wrapped in a list #
        JaWord.__init__(self, args[0].children)

    def is_stopword(self):
        return True

class JaVerb(JaWord):
    ''' Basic verb '''

    def __init__(self, args):
        JaWord.__init__(self, args)

    @property
    def lemma_form(self):
        ''' Returns the lemma form of this verb '''
        return self.children[0].lemma_form

    @shared_property
    def is_verb(self):
        ''' Always true '''
        return True

    @property
    def stem(self):
        ''' Returns the stem of this word as a string '''
        return str().join([ x.stem for x in self.root ])

    @property
    def inflection(self):
        ''' Returns the inflection of this word as a string '''
        return str().join([ x.inflection for x in self.suffixes ])

    @property
    def root(self):
        ''' Returns the root portion of the verb as a list '''
        return self.children[0:1]

    @property
    def suffixes(self):
        ''' Returns the root portion of the verb as an object '''
        return self.children[1:]

    @shared_property
    def is_stopword(self):
        ''' Always false '''
        return False

class JaNominalVerb(JaVerb):
    ''' A verb composed of a noun + verb '''

    def __init__(self, args):
        JaVerb.__init__(self, args)

    @property
    def noun(self):
        ''' Returns the noun portion '''
        return self.children[0]

    @property
    def verb(self):
        ''' Returns the verb portion '''
        return self.children[1]

    @property
    def stem(self):
        ''' Returns the stem of this word as a string '''
        return self.noun.stem + self.verb.stem

    @property
    def inflection(self):
        ''' Returns the inflection of this word as a string '''
        return self.verb.inflection

    @property
    def lemma_form(self):
        ''' Returns the lemma form of this verb '''
        return self.noun.lemma_form + self.verb.lemma_form

    @shared_property
    def is_nominal_verb(self):
        ''' Always true '''
        return True

    @property
    def root(self):
        ''' Returns the root portion of the verb as a list '''
        return [ self.noun ] + self.verb.root

    @property
    def suffixes(self):
        ''' Returns the root portion of the verb as an object '''
        return self.verb.suffixes

class JaAdjectivalVerb(JaVerb):
    ''' A verb composed of an adjective + verb '''

    def __init__(self, args):
        JaVerb.__init__(self, args)

    @property
    def adjective(self):
        ''' Returns the adjective portion '''
        return self.children[0]

    @property
    def verb(self):
        ''' Returns the verb portion '''
        return self.children[1]

    @property
    def stem(self):
        ''' Returns the stem of this word as a string '''
        return self.adjective.stem + self.verb.stem

    @property
    def inflection(self):
        ''' Returns the inflection of this word as a string '''
        return self.verb.inflection

    @property
    def lemma_form(self):
        ''' Returns the lemma form of this verb '''
        return self.adjective.surface + self.verb.lemma_form

    @shared_property
    def is_adjectival_verb(self):
        ''' Always true '''
        return True

    @property
    def root(self):
        ''' Returns the root portion of the verb as a list '''
        return self.adjective + self.verb.root

    @property
    def suffixes(self):
        ''' Returns the root portion of the verb as an object '''
        return self.verb.suffixes

class JaDeAru(JaVerb):
    ''' A verb form of de aru (de-aru, de-atta, da, desu, datta, desu, deshita)
        This class takes care of the infamous rare-yet-common irregular verb in Japanese.
    '''

    def __init__(self, args):
        JaVerb.__init__(self, args)

    @shared_property
    def is_de_aru(self):
        ''' This is a form of the de-aru verb '''
        return True

    @property
    def lemma_form(self):
        ''' Returns the lemma form of this verb
            Returns deAru for all cases, regardless of actual form.
        '''
        return 'である'

    @property
    def inflection(self):
        ''' Returns the inflection of this word as a string '''
        return str().join([ x.inflection for x in self.suffixes ])

    @property
    def root(self):
        ''' Returns the root portion of the verb as a list '''

        if len(self.children) == 1:
            return self.children[:]

        if self.children[0].is_particle:
              if self.children[1].base_form == ja_enc('ある'):
                  return self.children[0:2]
              else:
                  return self.children[0:1]

        if self.children[0].base_form == ja_enc('だ'):
           if self.children[1].base_form == ja_enc('ある'):
               return self.children[0:2]
           else:
               return self.children[0:1]

        if self.children[0].base_form == ja_enc('です'):
            return self.children[0:1]

        if self.children[0].base_form == ja_enc('です'):
            return self.children[0:1]

        # Should never get here #
        return self.children[0:1]

    @property
    def suffixes(self):
        ''' Returns the root portion of the verb as an object '''
        return self.children[ len(self.root) : ]

    @shared_property
    def is_stopword(self):
        ''' Always true '''
        return True

class JaDeNai(JaVerb):
    ''' A verb form of negative de aru (denai, dewa nai, dewa arimasen, dewa nakatta, dewa arimasendeshita, jya nai, jya arimasen, jya nakatta, jya arimasendeshita)
        This class takes care of the infamous rare-yet-common irregular verb in Japanese.
    '''

    def __init__(self, args):
        JaVerb.__init__(self, args)

    @property
    def root(self):
        ''' Returns the root portion of the verb as a list '''
        if self.children[0].is_particle:
              if self.children[1].base_form == ja_enc('ある'):
                  return self.children[0:2]
              else:
                  return self.children[0:1]

        if self.children[0].is_token \
          and self.children[0].base_form == ja_enc('だ'):
              if self.children[1].base_form == ja_enc('ある'):
                  return self.children[0:2]
              else:
                  return self.children[0:1]

        assert(False)

    @property
    def lemma_form(self):
        ''' Returns the lemma form of this verb
            Returns deAru for all cases, regardless of actual form.
        '''
        return 'である'

    @property
    def suffixes(self):
        ''' Returns the root portion of the verb as an object '''
        return self.children[ len(self.root) : ]

    @property
    def inflection(self):
        ''' Returns the inflection of this word as a string '''
        return str().join([ x.inflection for x in self.suffixes ])

    @shared_property
    def is_stopword(self):
        ''' Always true '''
        return True

class JaNoun(JaWord):
    ''' Basic verb '''

    def __init__(self, args):
        JaWord.__init__(self, args)

    @shared_property
    def is_noun(self):
        ''' Always true '''
        return True

    @property
    def stem(self):
        ''' Returns the stem of this word as a string '''
        return str().join([ x.stem for x in self.children ])

    @property
    def lemma_form(self):
        ''' Returns the lemma form of this word as a string '''
        return str().join([ x.lemma_form for x in self.children ])

    @shared_property
    def is_suru_conjunctive(self):
        ''' True if this is in conjuctive noun-suru form '''
        return self.children[0].is_suru_conjunctive

class JaAdjective(JaWord):
    ''' Basic Adjective '''

    def __init__(self, args):
        JaWord.__init__(self, args)

    @shared_property
    def is_adjective(self):
        ''' Always true '''
        return True

    @shared_property
    def is_negative(self):
        return len( filter(lambda x: x.is_verb and x.is_negative, self.children) )

    @property
    def lemma_form(self):
        ''' Returns the lemma form of this adjective '''
        return str().join([ x.lemma_form for x in filter(lambda x: x.is_adjective, self.children) ])

    @property
    def inflection(self):
        ''' Returns the inflection of this word as a string '''
        return str().join([ x.inflection for x in self.children[1:] ])

    @shared_property
    def is_te_conjunctive(self):
        ''' True if this is te-conjuctive (adjective-suru or adjective-naru mostly) '''
        return self.children[0].is_te_conjunctive

class JaAdverb(JaWord):
    ''' Basic Adverb '''

    def __init__(self, args):
        JaWord.__init__(self, args)

    @shared_property
    def is_adverb(self):
        ''' Always true '''
        return True

    @shared_property
    def is_stopword(self):
        ''' Always true '''
        return True

class JaParticle(JaWord):
    ''' Basic particle '''

    def __init__(self, args):
        JaWord.__init__(self, args)

    @shared_property
    def is_particle(self):
        ''' Always true '''
        return True

    @property
    def lemma_form(self):
        ''' Returns the lemma form of this verb '''
        return str().join([ x.lemma_form for x in self.children ])

    @shared_property
    def is_stopword(self):
        ''' Always true '''
        return True

    @property
    def stem(self):
        ''' Returns the stem of this word as a string '''
        return str().join([ x.stem for x in self.children ])

class JaPunctuation(JaWord):
    ''' Basic punctuation '''

    def __init__(self, args):
        JaWord.__init__(self, args)

    @shared_property
    def is_punctuation(self):
        ''' Always true '''
        return True

class JaUnknown(JaWord):
    ''' An unknown part-of-speech '''

    def __init__(self, args):
        JaWord.__init__(self, args)

    @shared_property
    def is_unknown(self):
        ''' Always true '''
        return True

from csc.nl.ja.cabocha_token import *

