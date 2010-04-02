#!/usr/bin/env python
from amara import binderytools
import pickle, os
from collections import defaultdict
from csc.nl.mblem.trie import Leaf, Node, default_trie

# English permutation:
# 20, 19, 1, 18, 2, 3, 17, 4, 5, 6, 7, 16, 8, 9, 15, 10, 14, 11, 13, 12
# Dutch permutation:
# 20, 19, 18, 17, 16, 15, 1, 2, 14, 3, 4, 5, 6, 13, 7, 8, 9, 12, 10, 11

dutch_indices = [0, 1, 2, 3, 4, 5, 8, 13, 17, 19]
english_indices = [0, 1, 3, 6, 11, 14, 16, 18, 19]

def make_node(xmlnode, prefix, depth, indices):
    node = Node()
    if prefix.endswith('='): prefix = prefix[:-1]
    for leaf in Leaf.list_from_string(unicode(xmlnode.target)):
        node.add_leaf(leaf)
    
    for childNode in xmlnode.childNodes:
        if (hasattr(childNode, 'nodeName') and childNode.nodeName == 'nodes'
        and hasattr(childNode, 'node')):
            for child in childNode.node:
                letter = unicode(child.feature)
                entry = prefix + letter
                assert (letter not in node.trie), letter
                node.trie[letter] = make_node(child, entry, depth+1, indices)
    if depth in indices:
        print prefix[::-1], node, node.leaves()
        return node
    else:
        if '=' in node.trie:
            next = node.trie['='].trie
            del node.trie['=']
            node.trie.update(next)
            print prefix[::-1], node, node.leaves()
            return node
        else:
            print prefix[::-1], node, node.leaves()
            return node

def make_mblem():
    doc = binderytools.bind_file('em.xml')
    trie = make_node(doc.root, '', 0, range(20))
    trie.permutation = [x-21 for x in 
    [20, 19, 1, 18, 2, 3, 17, 4, 5, 6, 7, 16, 8, 9, 15, 10, 14, 11, 13, 12]]
    
    # these appear not to work.
    
    #programming = trie.lookup(trie.permute('programming'))
    #programming.append(Leaf.make('', 'ming', 'V', 'pe'))

    #people = trie.lookup(trie.permute('people'))
    #people.append(Leaf.make('rson', 'ople', 'N', 'P'))

    out = open('en.mblem.pickle', 'w')
    pickle.dump(trie, out, -1)
    out.close()

def make_unlem(dir='en_unlem'):
    unlems = defaultdict(default_trie)
    for filename in os.listdir(dir):
        if filename.endswith('.xml'):
            print filename
            pos, infl, _ = filename.split('.', 2)
            doc = binderytools.bind_file(dir+'/'+filename)
            trie = make_node(doc.root, '', 0, range(20))
            unlems[pos, infl] = trie
    out = open('en.unlem.pickle', 'w')
    pickle.dump(unlems, out, -1)
    out.close()
    
if __name__ == '__main__':
    make_mblem()
    make_unlem()
