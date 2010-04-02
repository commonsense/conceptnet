#!/usr/bin/env python
import cPickle as pickle
import yaml

f = open('em.yaml')
trie = yaml.load(f)
f.close()

def trie_lookup(trie, s):
    if not s: char = '='
    else: char = s[0]
    if char in trie: return trie_lookup(trie[char], s[1:])
    else:
        return trie['*']

def lemmatize(word):
    key = word[::-1]
    responses = trie_lookup(trie, key)
    results = []
    for response in responses.split('|'):
        parts = response.split('+')
        pos = parts[0]
        lemma = word
        for part in parts:
            if part.startswith('D'):
                delete = part[1:]
                lemma = lemma[:len(lemma)-len(delete)]
            elif part.startswith('I'):
                insert = part[1:]
                lemma += insert
        results.append((lemma, pos))
    return results

print lemmatize("theses")
print lemmatize("scissors")
print lemmatize("data")
print lemmatize("being")
print lemmatize("linux")
print lemmatize("kindly")
print lemmatize("ordinarily")
print lemmatize("idly")
print lemmatize("indubitably")