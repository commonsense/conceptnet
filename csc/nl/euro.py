import string
from csc.nl import NLTools, get_nl, get_wordlist, get_mapping
import re

def doctest_globals():
    en_nl = get_nl('en')
    return locals()

class lazy_property(object):
    def __init__(self, func):
        '''
        A lazy decorator. Runs a function only once to get a
        property's value; after that, the precomputed value is used.

        Replace expensive computations in __init__ with this.
        '''
        self.func = func
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__
        self.__dict__.update(func.__dict__)

    def __get__(self, instance, cls):
        assert self.__name__ not in instance.__dict__
        result = instance.__dict__[self.__name__] = self.func(instance)
        return result

    @staticmethod
    def preset(cls, name, val):
        cls.__dict__[name] = val

# For .all_concepts, only include concepts where we know more than this number of things.
CUTOFF = 1

class EuroNL(NLTools):
    """
    A language that generally follows our assumptions about European languages,
    including:

    - Words are made of uppercase and lowercase letters, which are variant
      forms of each other, and apostrophes, which are kind of special.
    - Words are separated by spaces or punctuation.

    Only the subclasses of EuroNL -- :class:`StemmedEuroNL` and
    :class:`LemmatizedEuroNL` -- implement all of the NLTools operations.
    """
    # TODO: Refactor this so that stemming languages and lemmatizing languages
    # aren't mixed up.

    punctuation = ''.join(c for c in string.punctuation
                          if c not in "'-`")

    def __init__(self, lang, exceptions=None):
        if exceptions is None:
            exceptions = {}
        self.lang = lang
        self.exceptions = exceptions
        self.exceptions_rev = {}
        for key, value in exceptions.items():
            self.exceptions_rev[value] = key
        
    @lazy_property
    def blacklist(self):
        return get_wordlist(self.lang, 'blacklist')

    @lazy_property
    def stopwords(self):
        return get_wordlist(self.lang, 'stop')

    @lazy_property
    def frequencies(self):
        from csc.nl.models import Frequency
        return set([x.text for x in
                    Frequency.objects.filter(language__id=self.lang)])

    @lazy_property
    def all_concepts(self):
        '''Set of all concept text strings (not model objects)'''
        from csc.conceptnet.models import Concept
        return set(Concept.objects.filter(language__id=self.lang, num_assertions__gt=CUTOFF).values_list('text', flat=True))

    @lazy_property
    def swapdict(self):
        return get_mapping(self.lang, 'swap4')

    @lazy_property
    def autocorrect(self):
        return get_mapping(self.lang, 'autocorrect')

    def tokenize(self, text):
        r"""
        Tokenizing a sentence inserts spaces in such a way that it separates
        punctuation from words, splits up contractions, and generally does what
        a lot of natural language tools (especially parsers) expect their
        input to do.

            >>> en_nl.tokenize("Time is an illusion. Lunchtime, doubly so.")
            'Time is an illusion . Lunchtime , doubly so .'
            >>> untok = '''
            ... "Very deep," said Arthur, "you should send that in to the
            ... Reader's Digest. They've got a page for people like you."
            ... '''
            >>> tok = en_nl.tokenize(untok)
            >>> tok
            "`` Very deep , '' said Arthur , `` you should send that in to the Reader 's Digest . They 've got a page for people like you . ''"
            >>> en_nl.untokenize(tok)
            '"Very deep," said Arthur, "you should send that in to the Reader\'s Digest. They\'ve got a page for people like you."'
            >>> en_nl.untokenize(tok) == untok.replace('\n', ' ').strip()
            True

        """
        step0 = text.replace('\r', '').replace('\n', ' ')
        step1 = step0.replace(" '", " ` ").replace("'", " '").replace("n 't", 
        " n't").replace("cannot", "can not")
        step2 = re.sub('"([^"]*)"', r" `` \1 '' ", step1)
        step3 = re.sub(r'([.,:;?!%]+) ', r" \1 ", step2)
        step4 = re.sub(r'([.,:;?!%]+)$', r" \1", step3)
        step5 = re.sub(r'([()])', r" \1 ", step4)
        return re.sub(r'  +', ' ', step5).strip()

    def untokenize(self, text):
        """
        Untokenizing a text undoes the tokenizing operation, restoring
        punctuation and spaces to the places that people expect them to be.

        Ideally, `untokenize(tokenize(text))` should be identical to `text`,
        except for line breaks.
        """
        step1 = text.replace("`` ", '"').replace(" ''", '"')
        step2 = step1.replace(" ( ", " (").replace(" ) ", ") ")
        step3 = re.sub(r' ([.,:;?!%]+)([ \'"`])', r"\1\2", step2)
        step4 = re.sub(r' ([.,:;?!%]+)$', r"\1", step3)
        step5 = step4.replace(" '", "'").replace(" n't", "n't").replace(
          "can not", "cannot")
        step6 = step5.replace(" ` ", " '")
        return step6.strip()

    def canonicalize(self, word):
        """
        Reduce equivalent characters to a canonical form.

        In a EuroNL, by default, this puts those characters in lowercase.
        """
        return word.lower()

    def is_stopword(self, word):
        """
        A *stopword* is a word that contributes little to the semantic meaning
        of a text and should be ignored. These tend to be short, common words
        such as "of", "the", and "you".
        
        Stopwords are often members of closed classes such as articles and
        prepositions.

        Whether a word is a stopword or not is a judgement call that depends on
        the application. In ConceptNet, we began with the stock lists of
        stopwords from NLTK, but we have refined and tweaked the lists
        (especially in English) over the years.

        Examples::

            >>> en_nl.is_stopword('the')
            True
            >>> en_nl.is_stopword('THE')
            True
            >>> en_nl.is_stopword('defenestrate')
            False

            >>> pt_nl = get_nl('pt')      # This time, in Portuguese
            >>> pt_nl.is_stopword('os')
            True
            >>> pt_nl.is_stopword('the')
            False
        """
        return self.canonicalize(word) in self.stopwords

    def is_blacklisted(self, text):
        """
        The blacklist is used to discover and discard particularly unhelpful
        phrases.

        A phrase is considered "blacklisted" if *every* word in it appears on
        the blacklist. The empty string is always blacklisted.

            >>> en_nl.is_blacklisted('x')
            True
            >>> en_nl.is_blacklisted('the')
            False
            >>> en_nl.is_blacklisted('a b c d')
            True
            >>> en_nl.is_blacklisted('a b c d puppies')
            False

        """
        if not isinstance(text, unicode): text = text.decode('utf-8')
        words = self.tokenize(text).split(' ')
        for word in words:
            if self.canonicalize(word) not in self.blacklist: return False
        return True

    def is_frequency(self, word):
        """
        Return whether this word represents a frequency.
            
            >>> en_nl = get_nl('en')
            >>> en_nl.is_frequency('sometimes')
            True
            >>> en_nl.is_frequency('somewhere')
            False

            >>> es_nl = get_nl('es')      # This time, in Spanish
            >>> es_nl.is_frequency('nunca')
            True
            >>> es_nl.is_frequency('never')
            False

        """
        return self.canonicalize(word) in self.frequencies

    def get_frequency(self, text):
        """
        If the text contains a frequency, return it. The first frequency that
        occurs takes precedence, if there are multiple.

            >>> en_nl.get_frequency('Never trust a skinny chef.')
            u'never'
            >>> en_nl.get_frequency('This statement is true.')
            >>> en_nl.get_frequency('This statement is not always true.')
            u'not'

        """
        if not isinstance(text, unicode): text = text.decode('utf-8')
        words = self.tokenize(text).split(' ')
        for word in words:
            if self.canonicalize(word) in self.frequencies:
                return self.canonicalize(word)
        return None

    def get_words(self, text, strip_stopwords=False):
        '''
        Given a sentence, split it into words, stripping punctuation etc.
        '''
        text = self.tokenize(text)
        punct = self.punctuation
        words = text.replace('/', ' ').split()
        words = (w.strip(punct).lower() for w in words)
        words = (self.autocorrect.get(word, word) for word in words if word)
        if strip_stopwords:
            words = (word for word in words if not self.is_stopword(word))
        return list(words)

    def get_windows(self, words, window_size=2, join_words=True):
        """
        Extract windows from the list of words.

            >>> en_nl.get_windows(['sit', 'on', 'couches'], window_size=1)
            ['sit', 'on', 'couches']
            >>> en_nl.get_windows(['sit', 'on', 'couches'], window_size=2)
            ['sit on', 'sit', 'on couches', 'on', 'couches']
            >>> en_nl.get_windows(['sit', 'on', 'couches'], window_size=3)
            ['sit on couches', 'sit on', 'sit', 'on couches', 'on', 'couches']
            >>> en_nl.get_windows(['sit', 'on', 'couches'], window_size=2, join_words=False)
            [['sit', 'on'], ['sit'], ['on', 'couches'], ['on'], ['couches']]
        """
        nwords = len(words)
        windows = (words[i:i+wsize]
                   for i in xrange(nwords)
                   for wsize in xrange(min(window_size, nwords-i), 0, -1))
        if join_words:
            return [' '.join(window) for window in windows]
        else:
            return list(windows)
                
    def extract_concepts(self, text, max_words=2, check_conceptnet=False, also_allow=[]):
        """
        Extract a list of the concepts that are directly present in ``text``.

        ``max_words`` specifies the maximum number of words in the concept.
        
        If ``check_conceptnet`` is True, only concepts that are in
        ConceptNet for this language will be returned. ``also_allow``
        is a list or set of concepts that are additionally allowed.

            >>> en_nl.extract_concepts('People can be eating glimlings.', max_words=1, check_conceptnet=False)
            [u'person', u'eat', u'glimling']
            >>> en_nl.extract_concepts('People can be eating glimlings.', max_words=1, check_conceptnet=True)
            [u'person', u'eat']
            >>> en_nl.extract_concepts('People can be eating rice.', max_words=2, check_conceptnet=True)
            [u'person eat', u'person', u'eat rice', u'eat', u'rice']
        """
        words = self.normalize(text).split()
        windows = self.get_windows(words, window_size=max_words)
        if check_conceptnet:
            return [concept for concept in windows
                    if concept in self.all_concepts
                    or concept in also_allow]
        else:
            return windows
    

class LemmatizedEuroNL(EuroNL):
    @property
    def lemmatizer(self):
        """
        The `.lemmatizer` property lazily loads an MBLEM lemmatizer from the
        disk. The resulting object is an instance of
        :class:`csc.nl.mblem.trie.Trie`.
        """
        if not hasattr(self, '_lemmatizer'):
            from csc.nl.mblem import get_mblem
            self._lemmatizer = get_mblem(self.lang)
        return self._lemmatizer

    @property
    def unlemmatizer(self):
        """
        The `.unlemmatizer` property lazily loads an MBLEM unlemmatizer from
        the disk. The resulting object is a dictionary of tries, one for each
        possible combination of part-of-speech and inflection that can be
        added.
        """
        if not hasattr(self, '_unlemmatizer'):
            from csc.nl.mblem import get_unlem
            self._unlemmatizer = get_unlem(self.lang)
        return self._unlemmatizer

    def word_split(self, word):
        """
        Divide a single word into a string representing its *lemma form* (its
        base form without inflections), and a second string representing the
        inflections that were removed.

        Instead of abstract symbols for the inflection, we currently represent
        inflections as their most common natural language string. For example,
        the inflection string 's' represents both "plural" and "third-person
        singular".

        This odd representation basically makes the assumption that, when two
        inflections look the same, they will act the same on any word. Thus, we
        can avoid trying to disambiguate different inflections when they will
        never make a difference. (There are cases where this is not technically
        correct, such as "leafs/leaves" in "there were leaves on the ground"
        versus "he leafs through the pages", but we don't lose sleep over it.)

        >>> en_nl.word_split(u'lemmatizing')
        (u'lemmatize', u'ing')
        >>> en_nl.word_split(u'cow')
        (u'cow', u'')
        >>> en_nl.word_split(u'went')
        (u'go', u'ed')
        >>> en_nl.word_split(u'people')
        (u'person', u's')
        """
        if word in self.exceptions:
            return self.exceptions[word]
        try:
            lemma, pos, infl = self.lemmatizer.mblem(word)[0]
            residue = self.unlemmatizer[pos, infl].leaves()[0].add
            return (lemma, residue)
        except IndexError:
            return (word, u'')
        
    def lemma_split(self, text, keep_stopwords=False):
        """
        When you *lemma split* or *lemma factor* a string, you get two strings
        back:

        1. The *normal form*, a string containing all the lemmas of the
           non-stopwords in the string.
        2. The *residue*, a string containing all the stopwords and the
           inflections that were removed.

        These two strings can be recombined with :meth:`lemma_combine`.

            >>> en_nl.lemma_split("This is the testiest test that ever was tested")
            (u'testy test ever test', u'this is the 1iest 2 that 3 was 4ed')

        If ``keep_stopwords`` is set, or if all words are stopwords,
        then stopword removal is skipped.
        """
        if not isinstance(text, unicode): text = text.decode('utf-8')
        text = self.tokenize(text)
        punct = string.punctuation.replace("'", "").replace('-', '').replace("`", "")
        
        words = text.replace('/', ' ').split()
        words = [w.strip(punct).lower() for w in words]
        words = [self.autocorrect.get(word, word) for word in words if word]
        lemma_tuples = [self.word_split(word) for word in words]
        lemmas_pre = []
        residue_pre = []
        lemma_index = 0
        for i in range(len(words)):
            if not keep_stopwords and words[i] in self.stopwords:
                residue_pre.append((None, words[i]))
            else:
                lemmas_pre.append((lemma_tuples[i][0], lemma_index))
                residue_pre.append((lemma_index, lemma_tuples[i][1]))
                lemma_index += 1
        #lemmas_pre.sort()
        permute = [l[1] for l in lemmas_pre]
        invpermute = [permute.index(i) for i in range(len(permute))]
        lemmas = [l[0] for l in lemmas_pre]
        lemmas = [self.swapdict.get(lemma, lemma) for lemma in lemmas]

        residue = []
        for lemma_index, ltext in residue_pre:
            if lemma_index is None: residue.append(ltext)
            else: residue.append(str(invpermute[lemma_index]+1) + ltext)
        if len(lemmas) == 0 and not keep_stopwords:
            return self.lemma_split(text, keep_stopwords=True)
        return (u' '.join(lemmas), u' '.join(residue))
    lemma_factor = lemma_split

    def normalize(self, text):
        """
        When you *normalize* a string (no relation to the operation of
        normalizing a vector), you remove its stopwords and inflections so that
        it becomes equivalent to similar strings.

        Normalizing involves running :meth:`lemma_split` and keeping only the
        first factor, thus discarding the information that would be used to
        reconstruct the full string.

            >>> en_nl.normalize("This is the testiest test that ever was tested")
            u'testy test ever test'
        """
        return self.lemma_split(text)[0]
    normalize4 = normalize

    def lemma_combine(self, lemmas, residue):
        """
        This is the inverse of :meth:`lemma_factor` -- it takes in a normal
        form and a residue, and re-assembles them into a phrase that is
        hopefully comprehensible.

            >>> en_nl.lemma_combine(u'testy test ever test',
            ... u'this is the 1iest 2 that 3 was 4ed')
            u'this is the testiest test that ever was tested'
            >>> en_nl.lemma_combine(u'person', u'1s')
            u'people'
        """
        words = []
        lemmas = lemmas.split(' ')
        for res in residue.split(' '):
            if res and res[0] in '0123456789':
                numstr, pos, infl = self.lemmatizer.mblem(res)[0]
                while numstr[-1] not in '0123456789': numstr = numstr[:-1]
                rest = res[len(numstr):]
                num = int(numstr)
                lemma = lemmas[num-1]
                if (lemma, rest) in self.exceptions_rev:
                    words.append(self.exceptions_rev[(lemma, rest)])
                else:
                    inflected = self.unlemmatizer[pos, infl].unlem(lemma)[0]
                    words.append(inflected)
            else:
                words.append(res)
        return self.untokenize(' '.join(words))

class StemmedEuroNL(EuroNL):
    @property
    def stemmer(self):
        if not hasattr(self, '_stemmer'):
            from Stemmer import Stemmer
            self._stemmer = Stemmer(self.lang)
        return self._stemmer

    def stem_word(self, word):
        return self.stemmer.stemWord(word)

    def word_split(self, word):
        stem = self.stem_word(word)
        residue = word[len(stem):]
        return (stem, residue)
    
    def is_stopword(self, word):
        return word in self.stopwords

    def normalize(self, text):
        if not isinstance(text, unicode): text = text.decode('utf-8')
        punct = string.punctuation.replace("'", "")
        words = text.replace('/', ' ').replace('-', ' ').split()
        words = [w.strip(punct).lower() for w in words]
        words = [w for w in words if not self.is_stopword(w)]
        words = [self.stem_word(w) for w in words]
        words.sort()
        return u" ".join(words)

