import nltk
from collections import defaultdict
from nltk.cfg import Nonterminal
from divisi.util import get_picklecached_thing
from csc.corpus.models import Pattern, Sentence, Language
from csc.nl.euro import tokenize, untokenize
from nltk.corpus.reader import BracketParseCorpusReader
from nltk.corpus.util import LazyCorpusLoader
import string

treebank_brown = LazyCorpusLoader(
    'treebank/combined', BracketParseCorpusReader, r'c.*\.mrg')
#treebank_brown = None

en = Language.get('en')

# Patterns are 4-tuples of:
# (relative probability, predtype, polarity, expression)

patterns = [
(1.0, 'HasFirstSubevent', 'the first thing you do when you {VP:1} is {VP:2}'),
(1.0, 'HasLastSubevent', 'the last thing you do when you {VP:1} is {VP:2}'),
(1.0, 'HasPrerequisite', 'something you need to do before you {VP:1} is {VP:2}'),
(1.0, 'MadeOf', '{NP:1} {BE} {ADVP:a} made of {NP:2}'),
(1.0, 'IsA', '{NP:1} {BE} a kind of {NP:2} {POST:0}'),
(1.0, 'IsA', '{NP:1} {BE} a sort of {NP:2} {POST:0}'),
(1.0, 'IsA', '{NP:1} {BE} a type of {NP:2} {POST:0}'),
(1.0, 'AtLocation', 'somewhere {NP:1} can be is {P} {NP:2}'),
(1.0, 'AtLocation', 'somewhere {NP:1} can be is {NP:2}'),
(1.0, 'AtLocation', 'you are likely to find {NP:1} {P} {NP:2}'),
(0.1, 'AtLocation', '{NP:1} can be {P} {NP:2}'),
(1.0, 'UsedFor', '{NP:1} {BE} used for {NP:2}'),
(1.0, 'UsedFor', '{NP:1} {BE} used to {VP:2}'),
(1.0, 'CapableOf', '{NP:1} {BE} capable of {NP:2}'),
(1.0, 'CapableOf', 'an activity {NP:1} can do is {VP:2}'),
(1.0, 'CapableOf', 'an activity {NP:1} can do is {NP:2}'),
(1.0, 'MotivatedByGoal', 'you would {VP:1} because you want to {VP:2}'),
(1.0, 'MotivatedByGoal', 'you would {VP:1} because you want {NP:2}'),
(1.0, 'MotivatedByGoal', 'you would {VP:1} because {S:2}'),
(1.0, 'Desires', '{NP:1} {ADVP:a} wants to {VP:2}'),
(1.0, 'Desires', '{NP:1} {ADVP:a} wants {NP:2}'),
(1.0, 'Desires', '{NP:1} {ADVP:a} want to {VP:2}'),
(1.0, 'Desires', '{NP:1} {ADVP:a} want {NP:2}'),
(1.0, 'Desires', '{NP:1} {ADVP:a} likes to {VP:2}'),
(1.0, 'Desires', '{NP:1} {ADVP:a} like to {VP:2}'),
(1.0, 'DefinedAs', '{NP:1} {BE} defined as {NP:2}'),
(0.1, 'DefinedAs', '{NP:1} {BE} the {NP:2}'),
(0.1, 'DefinedAs', '{NP:2} {BE} called {NP:1}'),
(1.0, 'DefinedAs', 'the common name for {NP:2} is {NP:1}'),
(1.0, 'SymbolOf', '{NP:1} {BE} {DT} symbol of {NP:2}'),
(1.0, 'CausesDesire', '{NP:1} would make you want to {VP:2}'),
(1.0, 'Causes', 'the effect of {XP:1} is that {S:2}'),
(1.0, 'Causes', 'the effect of {XP:1} is {NP:2}'),
(1.0, 'Causes', 'the consequence of {XP:1} is that {XP:2}'),
(1.0, 'Causes', 'something that might happen as a consequence of {XP:1} is that {XP:2}'),
(1.0, 'Causes', 'something that might happen as a consequence of {XP:1} is {XP:2}'),
(1.0, 'Causes', '{ADVP:a} {NP:1} causes you to {VP:2}'),
(1.0, 'Causes', '{ADVP:a} {NP:1} causes {NP:2}'),
(1.0, 'HasSubevent', 'one of the things you do when you {VP:1} is {XP:2}'),
(1.0, 'HasSubevent', 'something that might happen when you {VP:1} is {XP:2}'),
(1.0, 'HasSubevent', 'something that might happen while {XP:1} is {XP:2}'),
(1.0, 'HasSubevent', 'something you might do while {XP:1} is {XP:2}'),
(1.0, 'HasSubevent', 'to {VP:1} you must {VP:2}'),
(0.8, 'HasSubevent', 'when you {VP:1} you {VP:2}'),
(1.0, 'HasSubevent', 'when you {VP:1} , you {VP:2}'),
(0.5, 'HasSubevent', 'when {S:1} , {S:2}'),
(0.1, 'ReceivesAction', '{NP:1} {BE} {PASV:2}'),
(1.0, 'PartOf', '{NP:1} {BE} part of {NP:2}'),
(1.0, 'CreatedBy', 'you make {NP:1} by {NP:2}'),
(1.0, 'CreatedBy', '{NP:1} {BE} created by {NP:2}'),
(1.0, 'CreatedBy', '{NP:1} {BE} made by {NP:2}'),
(1.0, 'CreatedBy', '{NP:1} {BE} created with {NP:2}'),
(1.0, 'CreatedBy', '{NP:1} {BE} made with {NP:2}'),
(1.0, 'CapableOf', "{NP:1} ca {n't:a} {VP:2}"),
(0.01, 'CapableOf', '{NP:1} can {ADVP2:a} {VP:2}'),
(0.001, 'CapableOf', '{NP:1} {ADVP1:a} {VP:2}'),
(1.0, 'UsedFor', 'you can use {NP:1} to {VP:2}'),
(1.0, 'AtLocation', 'something you might find {P} {NP:2} is {NP:1}'),
(1.0, 'AtLocation', 'something you find {P} {NP:2} is {NP:1}'),
(0.1, 'AtLocation', 'there are {NP:1} {P} {NP:2}'),
(1.0, 'HasA', '{NP:1} {ADVP:a} {HAVE} {NP:2}'),
(1.0, 'HasPrerequisite', '{NP:1} requires {NP:2}'),
(1.0, 'HasPrerequisite', 'if you want to {VP:1} then you should {VP:2}'),
(1.0, 'HasPrerequisite', '{VP:1} requires that you {VP:2}'),
(0.002, 'IsA', '{NP:1} {BE} {ADVP:a} {NP:2} {POST:0}'),
(0.02, 'IsA', 'to {VP:1} {BE} to {VP:2}'),
(0.3, 'HasProperty', '{NP:1} {BE} {ADVP:a} {AP:2}'),
(1.0, 'UsedFor', 'people use {NP:1} to {VP:2}'),
(1.0, 'UsedFor', '{NP:1} is for {XP:2}'),
(1.0, 'UsedFor', '{VP:1} is for {XP:2}'),
(1.0, 'junk', 'picture description : {XP:1}'),
(0.001, 'junk', '{NP:1}'),
(1.0, 'junk', 'things that are often found together are : {NP:1}'),
(1.0, 'junk', 'When you {VP:1} you do the following : 1'),
]

def defaultunigram(smoothing):
    x = defaultdict(int)
    x['NN'] = smoothing * 0.9
    x['VB'] = smoothing * 0.1
    return x

def get_lexicon(filename='LEXICON.BROWN.AND.WSJ'):
    f = open(filename)
    for line in f:
        parts = line.strip().split()
        if not parts: continue
        word = parts[0].lower()
        for tag in parts[1:]:
            # Pretend adverbs are a closed class. Otherwise lots of things
            # can inadvertently be adverbs.
            yield word, tag


class UnigramProbDist(object):
    def __init__(self, smoothing=0.01):
        self.counts = defaultdict(int)
        self.probs = defaultdict(lambda: defaultunigram(smoothing))
        self.smoothing = smoothing
        self.total = 0.0
    def inc(self, word, tag, closed_class=True):
        if word not in self.counts: self.total += self.smoothing
        if closed_class and tag in ['RB', 'MD', 'DO']: return
        self.probs[word][tag] += 1
        self.counts[word] += 1
        self.total += 1
    def probabilities(self, word):
        #count = float(self.counts[word]) + self.smoothing
        count = self.total
        if word != "'s":
            for tag, n in self.probs[word].items():
                yield tag, n/count
        else:
            yield "POS", 5000.0/count
    
    @classmethod
    def from_treebank(klass):
        from nltk.corpus import brown, treebank
        probdist = klass()
        for sent in treebank.tagged_sents():
            for word, tag in sent:
                probdist.inc(word.lower(), tag)
        for sent in treebank_brown.tagged_sents():
            for word, tag in sent:
                probdist.inc(word.lower(), tag)
        for word, tag in get_lexicon():
            probdist.inc(word, tag, closed_class=False)
        for i in range(10): probdist.inc('can', 'VB')
        return probdist

def match_production(rhs, start, chart, tokens=None):
    if len(rhs) == 0:
        yield start, 1.0
        return
    symb = str(rhs[0])
    group = None
    if symb[0] == "{":
        parts = symb[1:-1].split(':')
        symb = parts[0]
        if len(parts) > 1: group = parts[1]
    for next, prob in chart[symb][start].items():
        for end, prob2 in match_production(rhs[1:], next, chart):
            yield end, prob*prob2

def match_pattern(rhs, start, chart, tokens):
    if len(rhs) == 0:
        yield start, 1.0, [], {}
        return
    symb = str(rhs[0])
    group = None
    if symb[0] == "{":
        parts = symb[1:-1].split(':')
        symb = parts[0]
        if len(parts) > 1: group = parts[1]
    for next, prob in chart[symb][start].items():
        for end, prob2, frame, matchdict in match_pattern(rhs[1:], next, chart, tokens):
            if group is not None:
                if group in string.digits:    
                    chunk = ["{%s}" % group]
                    groupn = int(group)
                    if groupn == 0: chunk = []
                else:
                    chunk = tokens[start:next]
                    groupn = group
                matchdict[groupn] = untokenize(' '.join(tokens[start:next]))
            else: chunk = tokens[start:next]
            yield end, prob*prob2, chunk + frame, matchdict

def pattern_chart(tokens, grammar, unigrams, trace=0):
    # chart :: symbol -> start -> end -> prob
    chart = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    for i, token in enumerate(tokens):
        token = token.lower()
        chart[token][i][i+1] = 1.0
        if trace > 0:
            print "%s\t%s\t%s" % (token, (i, i+1), 1.0)
        for tag, prob in unigrams.probabilities(token):
            if tag == "''" or tag == "``": tag = "QUOT"
            if tag == 'PRP$': tag = "PRPp"
            chart[tag][i][i+1] = prob
            if trace > 0:
                print "%s\t%s\t%s" % (tag, (i, i+1), prob)
    
    changed = True
    while changed:
        changed = False
        for prod in grammar.productions():
            lhs = str(prod.lhs())
            for start in range(len(tokens)+1):
                for end, prob in match_production(prod.rhs(), start, chart):
                    p = prob * prod.prob()
                    if p > 1e-55 and p > chart[lhs][start][end]:
                        changed = True
                        chart[lhs][start][end] = p
                        if trace > 0:
                            print "%s\t%s\t%s" % (lhs, (start, end), p)
    return chart

thegrammar = nltk.data.load('file:patterns.pcfg')
theunigrams = UnigramProbDist.from_treebank()

def pattern_parse(sentence, trace=0):
    tokens = tokenize(sentence.split(". ")[0].strip("?!.")).split()
    chart = pattern_chart(tokens, thegrammar, theunigrams, trace)
    
    bestprob = 1e-60
    bestframe = None
    bestrel = None
    bestmatches = None
    for pprob, rel, pattern in patterns:
        ptok = pattern.split()
        for end, prob, frame, matchdict in match_pattern(ptok, 0, chart, tokens):
            prob *= pprob
            if end == len(tokens):
                if trace > 0:
                    print prob, pattern
                if prob > bestprob:
                    bestprob = prob
                    bestframe = untokenize(' '.join(frame))
                    bestrel = rel
                    bestmatches = matchdict
        #if bestpattern is not None: break
    return bestprob, bestframe, bestrel, bestmatches

def run_all():
    for sent in Sentence.objects.filter(language=en).order_by('id'):
        if (sentence.text.startswith('Situation:')
            or sentence.text.startswith('The statement')
            or sentence.text.startswith('To understand')
            or sentence.text.startswith('In the event')):
                print "* skipped *"
                continue
        print sent.text
        _, frame, rel, matches = pattern_parse(sent.text)
        print frame
        print rel, matches

if __name__ == '__main__': run_all()
