import codecs
import os

cached_nl = {}
nl_base = os.path.dirname(__file__)

def get_wordlist(lang, listname):
    try:
        wordfile = codecs.open("%s/%s/%s.txt" % (nl_base, lang, listname))
        words = [line.strip() for line in wordfile.readlines() if line.strip()]
        wordfile.close()
        return words
    except IOError:
        return []

def get_mapping(lang, listname):
    try:
        wordfile = codecs.open("%s/%s/%s.txt" % (nl_base, lang, listname))
        thedict = {}
        for line in wordfile:
            line = line.strip()
            if line:
                find, replace = line.split('=>')
                thedict[find.strip()] = replace.strip()
        wordfile.close()
        return thedict
    except IOError:
        return {}

def get_nl(lang_code):
    """
    Get an object that handles natural language operations for a given
    language, and remember it so that it doesn't have to be looked up again.
    """
    if lang_code in cached_nl: return cached_nl[lang_code]
    # ignore variants when looking up the nl object
    lang_code = lang_code.split('-')[0]
    name = 'csc.nl.'+lang_code
    result = __import__(name, [], [], 'NL').NL()
    cached_nl[lang_code] = result
    return result

class NLTools(object):
    """
    An NLTools object provides methods for dealing with natural language text
    in a particular language.

    So far, we have three classes of languages:
    
    * "Lemmatized" languages are languages where we have an MBLEM lemmatizer
      for removing or adding inflections to words. So far, this is just
      English, but it could easily include Dutch or German as well.
    * "Stemmed" languages are languages where we rely on a Snowball (Porter)
      stemmer to remove inflections from words. As there is a Snowball stemmer
      for most European languages, we treat most of them as stemmed languages.
    * "Default" languages are ones where we don't really know how to implement
      any NLP tools yet. All the methods perform trivial operations. Japanese,
      Korean, Chinese, and Arabic are currently "default" languages.
    
    With an NLTools object, you can perform these operations:
    
    * Detecting stopwords, or other words that we want to handle specially
    * Tokenizing a sentence by adding spaces and manipulating punctuation
    * Stemming/lemmatizing a phrase (which replaces inflected words with a
      single base form)
    * Synthesizing a phrase from a lemmatized form and a set of inflections

    The subclasses of NLTools define how these operations actually work.
    """
    def __init__(self):
        raise NotImplementedError, "NLTools is an abstract class"

class DefaultNL(NLTools):
    """
    DefaultNL is a stub class for languages we don't know how to process. It
    implements all the NLTools methods in ways that do nothing in particular.
    """
    def __init__(self): pass
    def is_stopword(self): return False
    def stem_word(self, stuff): return stuff
    def normalize(self, stuff): return stuff
    normalize4 = normalize
    def lemma_split(self, text, keep_stopwords=False):
        return text, u'*'
    def word_split(self, word):
        return (word, '')
    def is_blacklisted(self, text):
        return False
    def lemma_factor(self, text):
        return text, u'*'
    def lemma_combine(self, lemmas, residue):
        return lemmas
    def tokenize(self, text):
        return text

