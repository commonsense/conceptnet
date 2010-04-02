#!/usr/bin/env python
from corpus.models import *
import yaml

lang = 'nl'

f = open('dm.yaml')
trie = yaml.load(f)
f.close()

def handle_trie(trie, prefix):
    entry = trie['*']
    word = prefix[::-1]
    word = word.replace('=', '^')
    
    responses = entry.split('|')
    for response in responses:
        parts = response.split('+')
        pos, infl = parts[0].split('-')
        lemma = word
        for part in parts[1:]:
            if part.startswith('D'):
                delete = part[1:]
                if len(delete) > len(lemma): lemma = delete
                lemma = lemma[:len(lemma)-len(delete)]
            elif part.startswith('I'):
                insert = part[1:]
                lemma += insert
        print word, lemma, pos, infl
        the_pos, created = PartOfSpeech.objects.get_or_create(symbol=pos)
        the_lang = Language.objects.get(id=lang)
        the_infl, created = Inflection.objects.get_or_create(symbol=infl, language=the_lang)
        lemma_obj = Lemma(word=word, lemma=lemma, pos=the_pos,
        inflection=the_infl, language=the_lang)
        lemma_obj.save()

    for next in trie:
        if next == '*': continue
        handle_trie(trie[next], prefix+next)

handle_trie(trie, '')
