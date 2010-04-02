#python-encoding: utf-8

from csc.nl.ja.debug import *
from csc.nl.ja.util  import *
from csc.nl.ja.tree  import *

import MeCab
import CaboCha
import re

class JaToken(JaTreeLeaf, JaLanguageNode):
    ''' Represents a single token inside a word/chunk/utterance
    This should only be called from JaUtterance, as it assumes that the text given has been cleaned properly.
    Right now, this class is essentially a tree parser for CaboCha
    '''

    def __init__(self, cabocha_token):
        JaTreeLeaf.__init__(self)

        pos = [None, None, None, None]

        if cabocha_token.feature_list_size == 9:
            (
                pos[0],            # 品詞 #
                pos[1],            # 品詞細分類1 #
                pos[2],            # 品詞細分類2 #
                pos[3],            # 品詞細分類3 #
                self.conj_form,    # 活用形 #
                self.infl_type,    # 活用型 #
                self.base_form,    # 原形 #
                self.reading,      # 読み #
                self.prounciation  # 発音 #
            ) = [ cabocha_token.feature_list(i) for i in range(0, cabocha_token.feature_list_size) ]

        elif cabocha_token.feature_list_size == 7:
            (
                pos[0],            # 品詞 #
                pos[1],            # 品詞細分類1 #
                pos[2],            # 品詞細分類2 #
                pos[3],            # 品詞細分類3 #
                self.base_form,    # 原形 #
                self.infl_type,    # 活用型 #
                self.reading       # 読み #
            ) = [ cabocha_token.feature_list(i) for i in range(0, cabocha_token.feature_list_size) ]

            self.conj_form    = '*'
            self.prounciation = '*'

        self.surface = clean_input(cabocha_token.normalized_surface) # Do NOT use .surface or CaboCha WILL crash #

        # Cleanup input #
        self.pos        = pos[0]
        self.pos_string = ':'.join(filter(lambda x: x != '*', pos))

        if self.base_form    == '*': self.base_form    = None
        if self.conj_form    == '*': self.conj_form    = None
        if self.infl_type    == '*': self.infl_type    = None
        if self.prounciation == '*': self.prounciation = None
        if self.reading      == '*': self.reading      = None

    def __str__(self):
        return self.surface

    def query_pos(self, string):
        ''' Internally used to search for terms in the original PoS string '''
        string = ja_enc(string)
        return len(filter(None, [string == x for x in re.split(':', self.pos_string)])) > 0

    dump_lines = JaDebug.dump_lines_token

    @shared_property
    def is_verb(self):
        ''' True if this is a verb, or any part of a verb
        Note: Will report true for any verb, aux. verb, or certain types of verb conjunctions
        Additionally check is_independant() and is_auxilliary_verb() for verb stems
        '''
        return self.query_pos('動詞') or self.is_auxilliary_verb

    @shared_property
    def is_noun(self):
        ''' True if this is any kind of noun or noun affix
        Note: na adjectives will NOT return true for this test despite being classified as nouns by CaboCha
        '''
        return self.query_pos('名詞') and not self.is_na_adjective

    @shared_property
    def is_adverb(self):
        ''' True if this is any kind of adverb or adverb affix '''
        return self.query_pos('副詞')

    @shared_property
    def is_nai_adjective_stem(self):
        ''' True if this is a nai adjective stem ''' 

        return self.is_noun and self.query_pos('ナイ形容詞語幹')

    @shared_property
    def is_auxilliary_verb(self):
        ''' True if this is a na adjective stem '''
        return self.query_pos('助動詞')

    @shared_property
    def is_na_adjective(self):
        ''' True If this is a na adjective
        Note: All na adjectives are nouns, and the 'na' affix is not guaranteed
        '''
        return self.query_pos('形容動詞語幹')

    @shared_property
    def is_i_adjective(self):
        ''' True if this is an i adjective '''
        return self.query_pos('形容詞')

    @shared_property
    def is_adjective(self):
        ''' True if this is either na or i adjective or is a determinative '''
        return self.is_i_adjective or self.is_na_adjective or self.is_determinative

    @shared_property
    def is_irregular(self):
        ''' True if this is a verb root or suffix with an irregular conjugation '''
        return re.search('特殊', self.conj_form or '') != None

    @shared_property
    def is_determinative(self):
        ''' True if this word is a determinative (kono, sono, etc.) '''
        return self.query_pos('連体詞')

    @shared_property
    def is_particle(self):
        ''' True if this is a particle.
            That is: ha (wa), ga, he (e), wo (o), ni, etc.
            Without context, sometimes these are misclassified (example: ha (wa) -> ha (leaf))
        '''
        return self.query_pos('助詞')

    @shared_property
    def is_number(self):
        ''' True if this is a number '''
        return self.query_pos('数')

    @shared_property
    def is_counter(self):
        ''' True if this is an object counter '''
        return self.query_pos('助数詞')

    @shared_property
    def is_unknown(self):
        ''' True if this word was classifed by MeCab '''
        return self.query_pos('未知語')

    @shared_property
    def is_punctuation(self):
        ''' True if this word is punctuation '''
        return self.query_pos('記号')

    @shared_property
    def is_stopword(self):
        ''' True if this word is a stopword '''

        # Particle #
        if self.is_particle:    return True
        if self.is_punctuation: return True
        if self.is_adverb:      return True

        return False

    @shared_property
    def is_suffix(self):
        ''' True if this is a suffix '''
        return self.query_pos('接尾')

    @shared_property
    def is_independant(self):
        ''' True if this is independant.
        This is NOT the same thing as not self.is_dependant()
        (usually occurs in conjunctive clauses)
        '''
        return self.query_pos('自立')

    @shared_property
    def is_dependant(self):
        ''' True if this is dependant.
        This is NOT the same thing as not self.is_independant() '''
        return self.query_pos('非自立')

    @shared_property
    def is_imperitive(self):
        ''' True if this is in imperitive (-na[kere]) form (most likely a verb root) '''
        return self.query_pos('未然形')

    @shared_property
    def is_hypothetical(self):
        ''' True if this is in hypothetical (-kere) form (most likely a verb conjugate) '''
        return self.query_pos('仮定形')

    @shared_property
    def is_conjunctive(self):
        ''' True if this is in conjuctive (-te) form (most likely a verb root) '''
        return self.is_suru_conjunctive or self.is_te_conjunctive or self.infl_type == ja_enc('連用形')

    @shared_property
    def is_te_conjunctive(self):
        ''' True if this is te-conjuctive (adjective-suru or adjective-naru mostly) '''
        return re.match(ja_enc('連用テ接続'), self.infl_type or '') != None

    @shared_property
    def is_suru_conjunctive(self):
        ''' True if this is in conjuctive noun-suru form '''
        return self.query_pos('サ変接続')

    @shared_property
    def is_base_inflection(self):
        ''' True if this is in in base inflective form.  '''
        return self.infl_type == ja_enc('基本形')

    @shared_property
    def is_token(self):
        ''' Always True '''
        return True

    @property
    def stem(self):
        ''' The stem of the word we're in (here to allow elegant recursion - real work is done in words) '''
        return self.base_form or self.surface
    
    lemma_form = stem
    inflection = stem

    @shared_property
    def is_negative(self):
        return False

