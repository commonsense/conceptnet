from collections import defaultdict

class Leaf(object):
    existing = {}
    count = 0
    def __init__(self, add, delete, pos, inflections):
        self.add = add
        self.delete = delete
        self.pos = pos
        self.inflections = inflections
        Leaf.existing[add, delete, pos, inflections] = self
        Leaf.count += 1
    
    @staticmethod
    def make(add, delete, pos, inflections):
        if Leaf.existing.has_key((add, delete, pos, inflections)):
            return Leaf.existing[add, delete, pos, inflections]
        else:
            return Leaf(add, delete, pos, inflections)
    
    @staticmethod
    def list_from_string(string):
        got = []
        responses = string.split('|')
        for response in responses:
            insert = ''
            delete = ''
            parts = response.split('+')
            try:
                pos, infl = parts[0].split('-')
                for part in parts[1:]:
                    if part.startswith('D'):
                        delete = part[1:]
                    elif part.startswith('I'):
                        insert = part[1:]
            except ValueError:
                if len(parts) == 2: # unlemmatizing format
                    delete, insert = parts
                    pos = infl = None
                else: raise
            got.append(Leaf.make(insert, delete, pos, infl))
        return got
        
    def apply(self, string):
        if len(self.delete) == 0:
            stem = string
        #elif string.endswith(self.delete):
        else:
            stem = string[:-len(self.delete)]
        #else:
        #    stem = string+'?'
        return (stem + self.add, self.pos, self.inflections)
    
    def __repr__(self):
        if self.add: addstr = " +%s" % self.add
        else: addstr = ''
        if self.delete: delstr = " -%s" % self.delete
        else: delstr = ''
        return "<Leaf%s%s (%s.%s)>" % (addstr, delstr, self.pos,
        self.inflections)

    def symbol(self):
        return u"%s.%s.%s.%s" % (self.pos, self.inflections, self.add, self.delete)

POS_ORDER = ['TO', 'ART', 'V', 'N', 'A', 'ADV', 'PREP', 'PRON', 'C', 'ABB']

def pos_order(pos):
    if pos in POS_ORDER: return POS_ORDER.index(pos)
    else: return 100

def israre(infl):
    # Ignore 'rare' inflections, which accomplish nothing but
    # anachronistic hilarity.

    # Also, ignore past participles, because they confuse everything.
    # Oh well.
    return isinstance(infl, basestring) and (infl.endswith('r') or infl == 'pa')

class Node(object):
    def __init__(self, trie=None, leaves=None):
        self.trie = trie or {}
        self.leaf_index = defaultdict(list)
        if leaves is not None:
            for leaf in leaves:
                self.leaf_index[leaf.pos, leaf.inflections].append(leaf)
    
    def add_leaf(self, leaf):
        self.leaf_index[leaf.pos, leaf.inflections].append(leaf)

    def leaves(self):
        result = []
        for leaflist in self.leaf_index.values():
            result.extend(leaflist)
        # ignore rare/archaic inflections
        result = [leaf for leaf in result if not israre(leaf.inflections)]
        result.sort(key=lambda leaf: (pos_order(leaf.pos),
          -10*len(leaf.delete)+len(leaf.add)))
        return result
        
    def add(self, key, leaf):
        if len(key) == 0: self.add_leaf(leaf)
        else:
            start = key[0]
            trie = self.trie.setdefault(start, Node())
            trie.add(key[1:], leaf)

    def lookup(self, seq, pos=None, infl=None):
        if len(seq) == 0: key = '='
        else: key = seq[0]
        
        if key in self.trie:
            return self.trie[key].lookup(seq[1:], pos, infl)
        else:
            return self.leaves()

    def permute(self, string):
        padded = '='*(20-len(string)) + string
        if hasattr(self, 'permutation'):
            return [padded[i] for i in self.permutation]
        else:
            return list(string[::-1])

    def mblem(self, string, pos=None, infl=None):
        seq = self.permute(string)
        leaves = self.lookup(seq, pos, infl)
        return [leaf.apply(string) for leaf in leaves]

    def unlem(self, string):
        leaves = self.lookup(string[::-1])
        return [leaf.apply(string)[0] for leaf in leaves]

    def walk(self, suffix):
        out = [(self, suffix)]
        for key in self.trie:
            out.extend(self.trie[key].walk(key+suffix))
        return out
    
    def __repr__(self):
        return "<Trie node: [%s]>" % (''.join(sorted(self.trie.keys())))

def default_trie():
    return Node(leaves=[Leaf('', '', None, None)])


