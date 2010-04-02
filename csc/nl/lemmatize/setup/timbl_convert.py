#!/usr/bin/env python
from amara import binderytools
import pickle, yaml
# English permutation:
# 20, 19, 1, 18, 2, 3, 17, 4, 5, 6, 7, 16, 8, 9, 15, 10, 14, 11, 13, 12
# Dutch permutation:
# 20, 19, 18, 17, 16, 15, 1, 2, 14, 3, 4, 5, 6, 13, 7, 8, 9, 12, 10, 11

good_indices = [0, 1, 2, 3, 4, 5, 8, 13, 17, 19]

def dictionarify(node, prefix, depth):
    dic = {}
    if prefix.endswith('='): prefix = prefix[:-1]
    dic["*"] = str(node.target)
    print prefix, dic["*"]
    passthrough = None
    for childNode in node.childNodes:
        if hasattr(childNode, 'nodeName') and childNode.nodeName == 'nodes':
            for child in childNode.node:
                letter = str(child.feature)
                entry = prefix + letter
                dic[letter] = dictionarify(child, entry, depth+1)
                if letter == '=': passthrough = dic[letter]
    if depth in good_indices: return dic
    else:
        if passthrough is not None: return passthrough
        else: return {'*': dic['*']}

doc = binderytools.bind_file('dm.xml')
dic = dictionarify(doc.root, '', 0)
pickle.dump(dic, open("dm.pickle", 'w'))
yaml.dump(dic, open("dm.yaml", 'w'))
