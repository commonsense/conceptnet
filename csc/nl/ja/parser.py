#python-encoding: utf-8
from csc.nl.ja.debug import *
from csc.nl.ja.util  import *
from csc.nl.ja.tree  import *

import MeCab
import CaboCha
import re

class JaParser():
    ''' Parses Japanese Grammar Trees into words '''

    def __init__(self):
        pass

    def parse_string(self, string):
        ''' Returns a JaUtterance object with a fully parsed tree '''

        string         = clean_input(string)
        cabocha        = CaboCha.Parser("-f1 -n1")
        tree           = cabocha.parse(string)
        cabocha_chunks = [ tree.chunk(i) for i in range(0, tree.chunk_size()) ]
        cabocha_tokens = [ tree.token(i) for i in range(0, tree.token_size()) ]
        tokens         = [ JaToken(i) for i in cabocha_tokens ]
        chunks         = [ JaChunk(i, tokens[ i.token_pos : i.token_pos + i.token_size ]) for i in cabocha_chunks ]
        utterance      = JaUtterance(chunks)

        JaParser().parse_tree(utterance)

        return utterance

    def parse_tree(self, top):
        ''' Internal parsing function '''

        # Operate on chunks to create words #
        chunk_transforms = \
        [
            # The order of these is important - don't change these unless you know what you're doing #

            self.combine_noun_suffixes,
            self.combine_nai_adjective_stem,
            self.combine_na_adjectives,

            self.combine_dewa_nai,
            self.combine_dewa_arimasu,

            # Must happen before deAru or dewa gets messed up in some cases#
            self.combine_particles,

            # These three have to appear first to take care of deAru forms before general verb conjugation#
            self.combine_irregular_desu,
            self.combine_irregular_da,
            self.combine_irregular_de_aru,

            self.combine_verb_conjugates,
            self.combine_adjective_conjugates,

            # Should always be last #
            self.make_everything_word,
        ]

        chunk_access = lambda n: not n.is_word
        chunk_return = lambda n: n.is_chunk
        chunk_search = top.depth_first(access_filter = chunk_access, return_filter = chunk_return)

        # Operate on words to create more specialized types #
        word_transforms = \
        [
            self.find_dependant_koto,
            self.find_dependant_mono,
            self.find_nominal_verb,
            self.find_adjectival_verb,
        ]

        word_access = lambda n: not n.is_word
        word_return = lambda n: n.is_branch and not n.is_utterance
        word_search = top.depth_first(access_filter = word_access, return_filter = word_return)

        # Any tokens we want to modify after the fact #
        token_post_transforms = \
        [
            self.find_masu_n,
            self.find_da_particle,
        ]

        token_post_access = lambda n: True
        token_post_return = lambda n: n.is_token
        token_post_search = top.depth_first(access_filter = token_post_access, return_filter = token_post_return)

        self.__parse(chunk_search,      chunk_transforms)
        self.__parse(word_search,       word_transforms)
        self.__parse(token_post_search, token_post_transforms)

    def __parse(self, search, transforms):
        ''' Helper function for parse_tree '''

        for transform in transforms:
            search.reset()

            for node in search:
                if transform(node):
                    search.redo()

    ####################################################################################################
    ## Token level parsing #############################################################################
    ####################################################################################################
    def overlay_word(self, class_obj, node, start, length):
        ''' Used by word transform functions to overlay a word into a chunk '''

        word        = class_obj(node.children[start : start + length])
        word.parent = node

        for i in range(0, length):
            node.children.pop(start)
        node.children.insert(start, word)

        return word

    def combine_na_adjectives(self, node):
        ''' Combines adjective-na into a single word '''

        for i in range(0, len(node.children) - 1):
            if not node.children[i].is_na_adjective:       continue
            if node.children[i+1].surface != ja_enc('な'): continue

            return self.overlay_word(JaAdjective, node, i, 2)

    def combine_nai_adjective_stem(self, node):
        ''' Combines adjective-nai into full words (nai counts as a verb otherwise) '''

        for i in range(0, len(node.children) - 1):
            if not node.children[i].is_nai_adjective_stem: continue
            if not node.children[i+1].is_auxilliary_verb:  continue

            return self.overlay_word(JaAdjective, node, i, 2)

    def combine_noun_suffixes(self, node):
        ''' Combines any number of adjacent nouns into whole words appropriately. '''

        for i in range(0, len(node.children) - 1):
            if not node.children[i].is_noun: continue
            if node.children[i].is_suffix:   continue

            children = [ node.children[i] ]
            for v in node.children[i+1:]:
                if not v.is_noun:   break
                if not v.is_suffix: break
                children.append(v)

            if len(children) == 1: continue

            return self.overlay_word(JaNoun, node, i, len(children))

    def combine_verb_conjugates(self, node):
        ''' Combines inflections and other things on verbs to form a full word. '''

        for i in range(0, len(node.children) - 1):
            if not node.children[i].is_verb:  continue
            if node.children[i].is_suffix:    continue
            if node.children[i].is_irregular: continue

            if not (node.children[i].is_independant or node.children[i].is_dependant): continue

            children = [ node.children[i] ]
            for v in node.children[i+1:]:
                if not v.is_token:   break
                if not v.is_verb:    break
                if v.is_independant: break
                if v.is_irregular and v.is_auxilliary_verb and v.base_form == ja_enc('です'): break

                children.append(v)

            if len(children) == 1: continue

            return self.overlay_word(JaVerb, node, i, len(children))

    def combine_adjective_conjugates(self, node):
        ''' Combines inflections and other things on adjectives to form a full word. '''

        for i in range(0, len(node.children) - 1):
            if not node.children[i].is_i_adjective: continue
            if not node.children[i].is_conjunctive: continue
            if node.children[i].is_suffix:          continue

            children = [ node.children[i] ]
            for v in node.children[i+1:]:
                if v.is_auxilliary_verb and \
                   v.base_form == ja_enc('た'):
                    children.append(v)

                elif v.is_auxilliary_verb and \
                     v.base_form == ja_enc('ない'):
                    children.append(v)

            if len(children) == 1: continue

            return self.overlay_word(JaAdjective, node, i, len(children))

    def combine_irregular_desu(self, node):
        ''' Handles the special desu case in verbs '''

        for i in range(0, len(node.children)):
            # Check for desu #
            if not node.children[i].is_auxilliary_verb:      continue
            if node.children[i].base_form != ja_enc('です'): continue

            # Check for desu+ta --> deshita #
            if i + 1 < len(node.children) \
              and node.children[i].is_conjunctive \
              and node.children[i+1].is_auxilliary_verb \
              and node.children[i+1].is_base_inflection \
              and node.children[i+1].base_form == ja_enc('た'):
                return self.overlay_word(JaDeAru, node, i, 2)
            else:
                return self.overlay_word(JaDeAru, node, i, 1)

    def combine_irregular_da(self, node):
        ''' Handles the special da case in verbs '''

        for i in range(0, len(node.children) - 1):

            # Check for da #
            if not node.children[i].is_auxilliary_verb:    continue
            if node.children[i].base_form != ja_enc('だ'): continue

            # Check for da+ta --> datta #
            if node.children[i].surface == ja_enc('だっ') \
              and node.children[i+1].is_auxilliary_verb \
              and node.children[i+1].is_base_inflection \
              and node.children[i+1].base_form == ja_enc('た'):
                return self.overlay_word(JaDeAru, node, i, 2)

            if node.children[i].surface == 'だ':
                return self.overlay_word(JaDeAru, node, i, 1)

    def combine_irregular_de_aru(self, node):
        ''' Handles the special de aru case in verbs '''

        for i in range(0, len(node.children) - 1):
            # Check for da #
            if not node.children[i].is_auxilliary_verb:    continue
            if node.children[i].base_form != ja_enc('だ'): continue
            if not node.children[i].is_conjunctive:        continue

            # Check for da+ta --> datta #
            if not node.children[i+1].is_auxilliary_verb: continue
            if    node.children[i+1].base_form != ja_enc('ある') \
              and node.children[i+1].base_form != ja_enc('ない') : continue

            children = node.children[i:i+2]
            for v in node.children[i+2:]:
                if not v.is_verb:    break
                if v.is_independant: break
                children.append(v)

            if node.children[i+1].base_form == ja_enc('ある'):
                return self.overlay_word(JaDeAru, node, i, len(children))
            else:
                return self.overlay_word(JaDeNai, node, i, len(children))

    def combine_dewa_nai(self, node):
        def de(i):
            return ( node.children[i].is_token and node.children[i].base_form == ja_enc('で') and node.children[i].is_particle ) or \
                   ( node.children[i].is_token and node.children[i].base_form == ja_enc('だ') and node.children[i].is_auxilliary_verb and node.children[i].is_conjunctive )

        def wa(i):
            return node.children[i].is_token and node.children[i].base_form == ja_enc('は') and node.children[i].is_particle

        def jya(i):
            return node.children[i].is_token and node.children[i].base_form == ja_enc('じゃ') and node.children[i].is_particle

        particle_len = \
        {
            'dewa': 2,
            'jya':  1,
        }

        for i in range(0, len(node.children) - 2):
            # Make sure we start with a particle #
            if   de(i) and wa(i+1): particle_type = 'dewa'
            elif jya(i):            particle_type = 'jya'
            else:                   particle_type = None
            if not particle_type: continue

            # Followed by 'nai'... #
            if node.children[i+particle_len[particle_type]].base_form != ja_enc('ない'): continue

            # Create the particle here #
            self.overlay_word(JaParticle, node, i, particle_len[particle_type])

            # Get the rest of the verb #
            children = node.children[i:i+2]
            for v in node.children[i+2:]:
                if not v.is_token:   break
                if not v.is_verb:    break
                if v.is_independant: break
                children.append(v)

            return self.overlay_word(JaDeNai, node, i, len(children))

    def combine_dewa_arimasu(self, node):
        def de(i):
            return ( node.children[i].is_token and node.children[i].base_form == ja_enc('で') and node.children[i].is_particle ) or \
                   ( node.children[i].is_token and node.children[i].base_form == ja_enc('だ') and node.children[i].is_auxilliary_verb and node.children[i].is_conjunctive )

        def wa(i):
            return node.children[i].is_token and node.children[i].base_form == ja_enc('は') and node.children[i].is_particle

        def jya(i):
            return node.children[i].is_token and node.children[i].base_form == ja_enc('じゃ') and node.children[i].is_particle

        particle_len = \
        {
            'dewa': 2,
            'jya':  1,
        }

        for i in range(0, len(node.children) - 2):
            # Make sure we start with a particle #
            if   de(i) and wa(i+1): particle_type = 'dewa'
            elif jya(i):            particle_type = 'jya'
            else:                   particle_type = None
            if not particle_type: continue

            # Followed by 'aru'... #
            if not node.children[i+particle_len[particle_type]].is_verb:                 continue
            if node.children[i+particle_len[particle_type]].base_form != ja_enc('ある'): continue

            # Create the particle here #
            self.overlay_word(JaParticle, node, i, particle_len[particle_type])

            # Get the rest of the verb #
            polarity = True
            children = node.children[i:i+2]
            for v in node.children[i+2:]:
                if not v.is_token:   break
                if not v.is_verb:    break
                if v.is_independant: break

                if v.base_form == ja_enc('ん') or v.base_form == ja_enc('ない'):
                    polarity = False
                children.append(v)

            return self.overlay_word(JaDeAru if polarity else JaDeNai, node, i, len(children))

    def combine_particles(self, node):
        ''' Combines adjacent particles such as ni wa -> niwa '''

        def de(i):
            return ( node.children[i].is_token and node.children[i].base_form == ja_enc('で') and node.children[i].is_particle ) or \
                   ( node.children[i].is_token and node.children[i].base_form == ja_enc('だ') and node.children[i].is_auxilliary_verb and node.children[i].is_conjunctive )

        def wa(i):
            return node.children[i].is_token and node.children[i].base_form == ja_enc('は') and node.children[i].is_particle

        def no(i):
            return node.children[i].is_token and node.children[i].base_form == ja_enc('の') and node.children[i].is_particle

        def he(i):
            return node.children[i].is_token and node.children[i].base_form == ja_enc('へ') and node.children[i].is_particle

        def ni(i):
            return node.children[i].is_token and node.children[i].base_form == ja_enc('に') and node.children[i].is_particle

        def to(i):
            return node.children[i].is_token and node.children[i].base_form == ja_enc('と') and node.children[i].is_particle

        def te(i):
            return node.children[i].is_token and node.children[i].base_form == ja_enc('て') and node.children[i].is_particle

        def mo(i):
            return node.children[i].is_token and node.children[i].base_form == ja_enc('も') and node.children[i].is_particle

        particle_combinations = \
        {
            de: [ wa, no ],
            he: [ no ],
            ni: [ wa ],
            no: [ wa, de ],
            to: [ wa, no ],
            te: [ mo, wa ],
        }

        for i in range(0, len(node.children) - 1):
            for p1, array in particle_combinations.items():
                if not p1(i): continue

                for p2 in array:
                    if not p2(i+1): continue

                    return self.overlay_word(JaParticle, node, i, 2)

    def make_everything_word(self, node):
        ''' This is a last catch-all.  All remaining tokens are forced into word-hood. '''

        for i in range(0, len(node.children)):
            if not node.children[i].is_token: continue

            if node.children[i].is_noun:        return self.overlay_word(JaNoun,        node, i, 1)
            if node.children[i].is_verb:        return self.overlay_word(JaVerb,        node, i, 1)
            if node.children[i].is_adjective:   return self.overlay_word(JaAdjective,   node, i, 1)
            if node.children[i].is_particle:    return self.overlay_word(JaParticle,    node, i, 1)
            if node.children[i].is_adverb:      return self.overlay_word(JaAdverb,      node, i, 1)
            if node.children[i].is_punctuation: return self.overlay_word(JaPunctuation, node, i, 1)

            # All things MUST become words at this point - this is a definite error or unhandled case #
#            prop = filter(lambda v: re.match('is_', v[0]) and v[1], node.children[i].get_properties().items())
#            prop.sort()
#            prop_str = ', '.join([ x[0][3:].upper() for x in prop ])
#            raise TypeError("Unknown token type: " + str(node.children[i]) + ": " + prop_str)

            # This is the elegant solution.  Use the above to make sure JaUnknown objects cannot occur #
            return self.overlay_word(JaUnknown, node, i, 1)

    ####################################################################################################
    ## Word-level parsing ##############################################################################
    ####################################################################################################
    def find_nominal_verb(self, node):
        ''' Searches for noun/verb combinations that are likely nominal verbs '''
        for i in range(0, len(node.children) - 1):
            noun = node.children[i]
            verb = node.children[i+1]

            if not noun.is_noun: continue
            if not verb.is_verb: continue

            if noun.is_suru_conjunctive and \
               len(verb.root) == 1 and \
               verb.root[0].stem == ja_enc('する'):
                   return self.overlay_word(JaNominalVerb, node, i, 2)

    def find_adjectival_verb(self, node):
        ''' Searches for adjective/verb combinations that are likely nominal verbs '''

        for i in range(0, len(node.children) - 1):
            adj  = node.children[i]
            verb = node.children[i+1]

            if not adj.is_adjective: continue
            if not verb.is_verb:     continue

            if not adj.is_te_conjunctive: continue

            root = verb.root
            if len(verb.root) != 1: continue
            root = verb.root[0]

            if root.stem == ja_enc('する'):
                return self.overlay_word(JaAdjectivalVerb, node, i, 2)

            if root.stem == ja_enc('なる'):
                return self.overlay_word(JaAdjectivalVerb, node, i, 2)

    def find_dependant_koto(self, node):
        ''' Searches for dependant koto nouns and makes them into special objects '''
        for i in range(0, len(node.children)):
            koto = node.children[i]

            if not koto.is_noun: continue
            if len(koto.children) != 1: continue

            token = koto.children[0]

            if not token.is_dependant: continue
            if token.reading != ja_enc('コト'): continue
            if token.base_form != ja_enc('こと') and token.base_form != ja_enc('事'): continue

            return self.overlay_word(JaDependantKoto, node, i, 1)

    def find_dependant_mono(self, node):
        ''' Searches for dependant mono nouns and makes them into special objects '''
        for i in range(0, len(node.children)):
            mono = node.children[i]

            if not mono.is_noun: continue
            if len(mono.children) != 1: continue

            token = mono.children[0]

            if not token.is_dependant: continue
            if token.reading != ja_enc('モノ'): continue
            if token.base_form != ja_enc('もの') and token.base_form != ja_enc('物'): continue

            return self.overlay_word(JaDependantMono, node, i, 1)

    ####################################################################################################
    ## Token-level parsing #############################################################################
    ####################################################################################################
    def find_masu_n(self, node):
        ''' Searches for mase-n conjunctions and hacks the base form of 'n' to being 'nai' '''

        # Check for 'n' #
        if not node.base_form == ja_enc('ん'): return

        # Make sure the parent is a verb #
        parent = node.parent
        if not parent.is_verb: return

        # Find our index #
        index = parent.find_child(node)
        if type(index) != int: return
        if index == 0:         return

        # Make sure we are preceeded by 'mase' #
        preceeding = parent.children[index-1]
        if not preceeding.is_token:                return
        if preceeding.surface   != ja_enc('ませ'): return
        if preceeding.base_form != ja_enc('ます'): return

        # Modify the base form -> nai #
        node.base_form = ja_enc('ない')

    def find_da_particle(self, node):
        ''' Searches for 'de' that has been classified as 'da' by CaboCha and corrects it '''

        # Check for 'da' #
        if not node.base_form == ja_enc('だ'): return

        # Make sure the parent is a verb #
        parent = node.parent
        if not parent.is_particle: return

        # Find our index #
        index = parent.find_child(node)
        if type(index) != int:                return
        if index == len(parent.children) - 1: return

        # Make sure we are followed by 'wa' #
        following = parent.children[index+1]
        if not following.is_token:              return
        if not following.is_particle:           return
        if following.surface   != ja_enc('は'): return
        if following.base_form != ja_enc('は'): return

        # Modify the base form -> nai #
        node.base_form  = ja_enc('で')
        node.pos        = following.pos
        node.pos_string = following.pos_string
        node.conj_form  = None
        node.infl_type  = None

from csc.nl.ja.cabocha_token import *
from csc.nl.ja.word          import *
from csc.nl.ja.chunk         import *
from csc.nl.ja.utterance     import *

