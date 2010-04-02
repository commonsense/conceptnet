#python-encoding: UTF-8

try:
    import MeCab
except ImportError:
    raise ImportError("""
You do not have the MeCab library available, so you cannot use the Japanese
NLTools.

See csc/nl/ja/README.TXT for instructions on how to set up MeCab.""")
from csc.nl import NLTools, get_nl
from csc.nl.ja.parser import JaParser
from csc.nl.ja.tree import JaLanguageNode
from csc.nl.ja.util import ja_enc, ja_dec
from csc.nl.ja.word import JaWord
import string
import re

def NL():
    return JaNL('ja')

'''
--- Note ---
    See csc.nl.ja.system for the internal structure of these tools
'''

class JaNL(NLTools):
    def __init__(self, lang):
        self.lang = lang

    def utterance(self, stuff):
        ''' Returns a JaUtterance representing the string
        This should be your primary access if you want to use advanced features.
        '''

        try:
            if   isinstance(stuff, JaLanguageNode): return stuff
            elif isinstance(stuff, str):            return JaParser().parse_string(stuff)
            elif isinstance(stuff, unicode):        return JaParser().parse_string(stuff)

        except KeyboardInterrupt, e:
            raise e

        except:
            raise RuntimeError("Tree construction error based on input: " + ja_dec(stuff))

        raise ValueError("Bad argument to a csc.nl.ja function.")

    def is_stopword(self, word):
        ''' Returns whether or not the given word is a stopword '''

        words = self.utterance(word).words
        if len(words) == 0:
            raise ValueError("Could not find a word to check.")
        elif len(words) > 1:
            raise ValueError("Multiple words found.")

        return words[0].is_stopword

    def stem_word(self, word):
        ''' Returns an inflectionless version of the word '''

        return ja_dec(self.word_split[0])

    def __attached_suffixes(self, positive = True):
        ''' Helper function for normalize and word_split (internal use) '''
        suffix_forms = [ ja_enc('ない'), ja_enc('たい') ]

        if positive == True:
            return lambda x: x in suffix_forms
        elif positive == False:
            return lambda x: not (x in suffix_forms)
        else:
            return lambda x: True

    def __normalize_suffixes(self, word, boolean):
        ''' Returns suffixes of a word seperated by a nyoro (internal use).
        Argument MUST be a JaWord
        '''

        lemma_join    = ja_enc('〜')
        suffix_list   = [ s.lemma_form for s in word.suffixes ]
        annotations   = filter(self.__attached_suffixes(boolean), suffix_list)
        string        = lemma_join.join(annotations)

        return ja_dec( lemma_join + string ) if string else unicode()

    def __normalize_word(self, word, boolean):
        ''' Normalize a word (internal use) '''
        lemma  = ja_dec(word.lemma_form)
        suffix = self.__normalize_suffixes(word, boolean)
        return lemma + suffix

    def __normalize_words(self, words):
        ''' Normalize a list of words (internal use) '''
        return ' '.join( self.__normalize_word(w, True) for w in words )

    def word_split(self, word):
        ''' Splits the word into a base and inflection '''

        words = self.utterance(word).words
        if len(words) == 0:
            raise ValueError("Could not find a word to check.")
        elif len(words) > 1:
            raise ValueError("Multiple words found.")

        word = words[0]

        lemma  = self.__normalize_word(word, True)
        suffix = self.__normalize_suffixes(word, False)

        return ja_dec(lemma), ja_dec(suffix)

    def normalize(self, stuff):
        return ja_dec( self.__normalize_words(self.utterance(stuff).words) )

    def lemma_split(self, stuff, keep_stopwords = False):
        ''' Split the lemmas into two strings with stopwords separated '''

        words = self.utterance(stuff).words

        if keep_stopwords:
            first = ' '.join( [ self.__normalize_word(w, True) for w in words ] )
        else:
            first = ' '.join( [ self.__normalize_word(w, True) for w in filter(lambda w: not w.is_stopword, words) ] )

        second = []
        index  = 0

        for i, w in enumerate(words):
            if not keep_stopwords and w.is_stopword:
                second.append(self.__normalize_word(w, None))
            else:
                index    += 1
                second.append(str(index) + self.__normalize_suffixes(w, False))

        second = ' '.join(second)

        return ja_dec(first), ja_dec(second)

    def lemma_combine(self, lemmas, residue):
        ''' Reverses lemma_split '''

        # TODO: This is reasonably difficult to do with the information provided - future work #
        return lemmas

    def is_blacklisted(self, stuff):
        ''' Returns True if the text is known to be bad '''

        return False

    def tokenize_list(self, stuff):
        ''' Returns a list of token objects
        They all support str() so convert them to strings if you like
        '''

        return self.utterance(stuff).words

    def untokenize_list(self, token_list):
        ''' Reverses tokenize_list '''

        return token_list[0].top

    def tokenize(self, stuff):
        ''' Returns a string of tokens separted by spaces '''

        return ' '.join( [ ja_dec(str(x)) for x in self.tokenize_list(stuff) ] )

    def untokenize(self, stuff):
        ''' Reverses tokenize '''

        if isinstance(stuff, JaLanguageNode):
            return ja_dec(stuff.surface)
        else:
            return re.sub(' ', '', ja_dec(stuff))

    lemma_factor = lemma_split
    normalize4   = normalize

