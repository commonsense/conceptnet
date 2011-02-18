from pymeta.grammar import OMeta, ParseError
from csc.corpus.models import Sentence, TaggedSentence
from itertools import chain
import sys

class PatternParserBase(OMeta):
    def __init__(self, string, globals=None):
        OMeta.__init__(self, string, globals)
        self.assertion_patterns = []
        
    def text(self, string):
        for c in string:
            if c == ' ':
                self.rule_tag()
            else:
                head = self.input.head()
                if c.lower() == head.lower():
                    self.input = self.input.tail()
                else: raise ParseError
        self.rule_tag()
        return string
    rule_text = text
    
    def hastag(self, tag):
        word = self.rule_aword()
        tags = self.rule_tags()
        print word, tags
        if tag in tags: return word
        else: raise ParseError
    rule_hastag = hastag
        

def words(*lst):
    return ' '.join(str(x) for x in lst if x)

SLOT1 = '{1}'
SLOT2 = '{2}'

metapatterns = """
space ::= <spaces> | <end>
wordchar ::= ~'_' ~' ' <letter>:c  => c
aword ::= <wordchar>+:cs           => ''.join(cs)
tag ::= '_' (<letter> | '$')+ <space>
tag1 ::= '_' (<letter> | '$')+:t   => ''.join(t)
tags ::= <tag1>+:ts <space>        => ts

CD ::= <hastag "CD">
DT ::= <hastag "DT">
IN ::= <hastag "IN">
JJ ::= <hastag "JJ">
JJR ::= <hastag "DT">
JJS ::= <hastag "JJS">
MD ::= <hastag "MD">
NN ::= <hastag "NN">
NNS ::= <hastag "NNS">
NNP ::= <hastag "NNP">
POS ::= <hastag "POS">
PRP ::= <hastag "PRP">
PRPp ::= <hastag "PRP$">
RB ::= <hastag "RB">
RP ::= <hastag "RP">
RPR ::= <hastag "RPR">
TO ::= <hastag "TO">
VB ::= <hastag "VB">
VBG ::= <hastag "VBG">
VBN ::= <hastag "VBN">
VBP ::= <hastag "VBP">
VBZ ::= <hastag "VBZ">
WDT ::= <hastag "WDT">

N1  ::= (<NN> | <NNS>)+:ns                      => ' '.join(ns)
Npr ::= <NNP>+:ns                               => ' '.join(ns)
join ::= (<text ","> | <text "and">):w          => w
AP  ::= ( (<JJ> | <VBN> | <PRPp> | <JJR> | <JJS> | <CD>):w => w 
        | <AP>:a1 <join>:c <AP>:a2              => words(a1, c, a2)
        | <AP>:a1 <AP>:a2                       => words(a1, a2)
        )
NP  ::= ( <DT>?:d <AP>?:a <N1>:n                => words(d, a, n)
        | <Npr> | <PRP>
        | <VBG>:v <RB>:r                        => words(v, r)
        | <VBG>:v <NP>?:n <P>?:p                => words(v, n, p)
        | <NP>:n <PP>:p                         => words(n, p)
        | <NP>:n1 "and":c <tag> <NP>:n2         => words(n1, c, n2)
        )
P   ::= (<IN>|<TO>)
PP  ::= ( <P>:p <NP>:np                         => words(p, np)
        | <TO>:t <VP>:v                         => words(t, v)
        )
V   ::= ( (<VB> | <VBZ> | <VBP>):v              => v
        | <text "go">:g <text "and">?:a <VB>:v  => words(g, a, v)
        )
VP  ::= ( <ADVP>:ap <V>:v <NP>?:np <PP>?:pp     => words(ap, v, np, pp)
        | <ADVP>:a (<BE> | <CHANGE>):v (<NP> | <AP>):o  => words(a, v, o)
        | <V>:v <ADV>:rb                        => words(v, rb)
        )
POST ::= ( <VBN> <PP> | <WDT> <VP> | <WDT> <S> ) => ''
S   ::= <NP>:n <VP>:v                           => words(n, v)
XP  ::= <NP> | <VP> | <S>
PASV ::= <VBN>:v <PP>+:ps                       => words(*([v]+ps))
be_word ::= (<token "be"> | <token "is"> | <token "are"> | <token "was">
            | <token "being"> | <token "been"> | <token "'s">
            | <token "'re"> | <token "'m">):w   => w
BE  ::= (<be_word>:w <tag>                      => w
        |<MD>:m <RB>?:r <BE>:b                  => words(m, r, b)
        )
DO ::= (<text "do"> | <text "does"> | <text "did">):w => w

CHANGE ::= ( <text "get"> | <text "gets"> | <text "become">
           | <text "becomes"> )
ADV    ::= <RB> | <RP> | <RBR>
ADVP   ::= (<MD> | <DO>)?:m <RB>*:rs            => words(*([m]+rs))

assertion ::= (
  <text "The first thing you do when you"> <VP>:t1 <text "is"> <VP>:t2
    => dict(frame="The first thing you do when you {1} is {2}",
            relation="HasFirstSubevent",
            text1=t1, text2=t2)

| <text "The last thing you do when you"> <VP>:t1 <text "is"> <VP>:t2
    => dict(frame="The last thing you do when you {1} is {2}",
            relation="HasLastSubevent",
            text1=t1, text2=t2)

| <text "Something you need to do before you"> <VP>:t1 <text "is"> <VP>:t2
    => dict(frame="Something you need to do before you {1} is {2}",
            relation="HasPrerequisite",
            text1=t1, text2=t2)
| <NP>:t1 <text "requires"> <NP>:t2
    => dict(frame="{1} requires {2}",
            relation="HasPrerequisite",
            text1=t1, text2=t2)

| <text "If you want to"> <VP>:t1 <text "then you should"> <VP>:t2
    => dict(frame="If you want to {1} then you should {2}",
            relation="HasPrerequisite",
            text1=t1, text2=t2)

| <NP>:t1 <BE>:x1 <ADVP>?:adv <text "made of">:x2 <NP>:t2
    => dict(frame=words(SLOT1, x1, adv, x2, SLOT2),
            relation="MadeOf", text1=t1, text2=t2, adv=adv)

| <NP>:t1 <BE>:x1 (<text "a kind of"> | <text "a sort of">):x2 <NP>:t2 <POST>
    => dict(frame=words(SLOT1, x1, x2, SLOT2),
            relation="IsA", text1=t1, text2=t2)

| <text "Somewhere">:x1 <NP>:t1 <text "can be is">:x2 <P>:x3 <NP>:t2
    => dict(frame=words(x1, SLOT1, x2, x3, SLOT2),
            relation="AtLocation", text1=t1, text2=t2)

| <text "Something you might find">:x1 <P>:x2 <NP>:t2 <text "is">:x3 <NP>:t1
    => dict(frame=words(x1, x2, SLOT2, x3, SLOT1),
            relation="AtLocation", text1=t1, text2=t2)

| <text "Something you find">:x1 <P>:x2 <NP>:t2 <text "is">:x3 <NP>:t1
    => dict(frame=words(x1, x2, SLOT2, x3, SLOT1),
            relation="AtLocation", text1=t1, text2=t2)

| <text "Somewhere">:x1 <NP>:t1 <text "can be is">:x2 <P>:x3 <NP>:t2
    => dict(frame=words(x1, SLOT1, x2, x3, SLOT2),
            relation="AtLocation", text1=t1, text2=t2)

| <text "You are likely to find">:x1 <NP>:t1 <P>:x2 <NP>:t2
    => dict(frame=words(x1, SLOT1, x2, SLOT2),
            relation="AtLocation", text1=t1, text2=t2)

| <NP>:t1 <BE>:x1 <text "used for">:x2 <NP>:t2
    => dict(frame=words(SLOT1, x1, x2, t2),
            relation="UsedFor", text1=t1, text2=t2)

| <NP>:t1 <BE>:x1 <text "used to">:x2 <VP>:t2
    => dict(frame=words(SLOT1, x1, x2, t2),
            relation="UsedFor", text1=t1, text2=t2)

| (<text "You"> | <text "People">):x1 <text "can">?:x2 <text "use">:x3
  <NP>:t1 <text "for">:x4 <NP>:t2
    => dict(frame=words(x1, x2, x3, SLOT1, x4, SLOT2),
            relation="UsedFor", text1=t1, text2=t2)

| (<text "You"> | <text "People">):x1 <text "can">?:x2 <text "use">:x3
  <NP>:t1 <text "to">:x4 <VP>:t2
    => dict(frame=words(x1, x2, x3, SLOT1, x4, SLOT2),
            relation="UsedFor", text1=t1, text2=t2)

| <NP>:t1 <BE>:x1 <ADVP>?:adv <text "for">:x2 <VP>:t2
    => dict(frame=words(SLOT1, x1, adv, x2, SLOT2),
            relation="UsedFor", text1=t1, text2=t2, adv=adv)

| <NP>:t1 <BE>:x1 <text "capable of">:x2 <VP>:t2
    => dict(frame=words(SLOT1, x1, x2, SLOT2),
            relation="CapableOf", text1=t1, text2=t2)

| <text "An activity"> <NP>:t1 <text "can do is"> (<NP>|<VP>):t2
    => dict(frame="An activity {1} can do is {2}",
            relation="CapableOf", text1=t1, text2=t2)

| <text "You would"> <NP>:t1 <text "because you want to"> <VP>:t2
    => dict(frame="You would {1} because you want to {2}",
            relation="MotivatedByGoal", text1=t1, text2=t2)

| <text "You would"> <NP>:t1 <text "because you want"> <NP>:t2
    => dict(frame="You would {1} because you want {2}",
            relation="MotivatedByGoal", text1=t1, text2=t2)

| <NP>:t1 <ADVP>:adv (<text "wants to"> | <text "want to">):x1 <VP>:t2
    => dict(frame=words(SLOT1, adv, x1, SLOT2),
            relation="Desires", text1=t1, text2=t2)

| <NP>:t1 <ADVP>:adv (<text "wants"> | <text "want">):x1 <NP>:t2
    => dict(frame=words(SLOT1, adv, x1, SLOT2),
            relation="Desires", text1=t1, text2=t2)
| <NP>:t1 <BE>:x1 <text "defined as">:x2 <VP>:t2
    => dict(frame=words(SLOT1, x1, x2, SLOT2),
            relation="DefinedAs", text1=t1, text2=t2)

| <NP>:t1 <BE>:x1 <text "the">:x2 <NP>:t2
    => dict(frame=words(SLOT1, x1, x2, SLOT2),
            relation="DefinedAs", text1=t1, text2=t2)

| <NP>:t1 <BE>:x1 <DT>:x2 <text "symbol of">:x3 <NP>:t2
    => dict(frame=words(SLOT1, x1, x2, x3, SLOT2),
            relation="SymbolOf", text1=t1, text2=t2)

| <NP>:t1 <text "represents"> <NP>:t2
    => dict(frame="{1} represents {2}",
            relation="SymbolOf", text1=t1, text2=t2)

| <NP>:t1 <text "would make you want to"> <VP>:t2
    => dict(frame="{1} would make you want to {2}",
            relation="CausesDesire",
            text1=t1, text2=t2)

| <text "You would"> <VP>:t1 <text "because"> <XP>:t2
    => dict(frame="You would {1} because {2}",
            relation="CausesDesire",
            text1=t1, text2=t2)

| <text "The effect of"> <XP>:t1 <text "is that"> <S>:t2
    => dict(frame="The effect of {1} is that {2}",
            relation="Causes", text1=t1, text2=t2)

| <text "The effect of"> <XP>:t1 <text "is"> <NP>:t2
    => dict(frame="The effect of {1} is {2}",
            relation="Causes", text1=t1, text2=t2)

| <text "The consequence of"> <XP>:t1 <text "is that"> <S>:t2
    => dict(frame="The consequence of {1} is that {2}",
            relation="Causes", text1=t1, text2=t2)

| <text "The consequence of"> <XP>:t1 <text "is"> <NP>:t2
    => dict(frame="The consequence of {1} is {2}",
            relation="Causes", text1=t1, text2=t2)

| <text "Something that might happen as a consequence of">:x1
  <XP>:t1 <text "is">:x2 <text "that">?:x3 <XP>:t2
    => dict(frame=words(x1, SLOT1, x2, x3, SLOT2),
            relation="Causes", text1=t1, text2=t2)

| <ADVP>:adv <NP>:t1 <text "causes">:x1 <text "you to">?:x2 <XP>:t2
    => dict(frame=words(adv, SLOT1, x1, x2, SLOT2),
            relation="Causes", text1=t1, text2=t2, adv=adv)

| (<text "Something"> | <text "One of the things">):x1
  <text "that">?:x2
  (<text "you might do"> | <text "you do"> | <text "might happen">):x3
  (<text "while"> | <text "when you"> | <text "when">):x4
  <XP>:t1 <text "is">:x5 <XP>:t2
    => dict(frame=words(x1, x2, x3, x4, SLOT1, x5, SLOT2),
            relation="HasSubevent", text1=t1, text2=t2)

| <NP>:t1 <BE>:x1 <ADVP>?:adv <text "part of">:x2 <NP>:t2
    => dict(frame=words(SLOT1, x1, adv, x2, SLOT2),
            relation="PartOf", text1=t1, text2=t2, adv=adv)

| <text "You make"> <NP>:t1 <text "by"> <XP>:t2
    => dict(frame="You make {1} by {2}",
            relation="CreatedBy", text1=t1, text2=t2)

| <NP>:t1 <text "is created by"> <XP>:t2
    => dict(frame="{1} is created by {2}",
            relation="CreatedBy", text1=t1, text2=t2)

| <text "There">:x1 <BE>:x2 <NP>:t1 <P>:x3 <NP>:t2
    => dict(frame=words(x1, x2, SLOT1, x3, SLOT2),
            relation="AtLocation", text1=t1, text2=t2)

| <NP>:t1 <BE>:x1 <PASV>:t2
    => dict(frame=words(SLOT1, x1, SLOT2),
            relation="ReceivesAction", text1=t1, text2=t2)

| (<text "You can"> | <text "Someone can"> | <text "People can">):x1
  <ADVP>:adv <V>:t1 <NP>:t2
    => dict(frame=words(x1, adv, SLOT1, SLOT2),
            relation="ReceivesAction", text1=t1, text2=t2, adv=adv)

| <NP>:t1 <BE>:x1 <ADVP>:adv <P>:x2 <NP>:t2
    => dict(frame=words(SLOT1, x1, adv, x2, SLOT2),
            relation="AtLocation", text1=t1, text2=t2, adv=adv)
| <NP>:t1 <BE>:x1 <ADVP>:adv <AP>:t2
    => dict(frame=words(SLOT1, x1, adv, SLOT2),
            relation="AtLocation", text1=t1, text2=t2, adv=adv)

| <NP>:t1 <ADVP>:adv (<text "has"> | <text "have">):x1 <NP>:t2
    => dict(frame=words(SLOT1, adv, x1, SLOT2),
            relation="HasA", text1=t1, text2=t2, adv=adv)

| <NP>:t1 <ADVP>:adv (<text "contain"> | <text "contains">):x1 <NP>:t2
    => dict(frame=words(SLOT1, adv, x1, SLOT2),
            relation="HasA", text1=t1, text2=t2, adv=adv)

| <NP>:t1 <BE>:x1 <ADVP>:adv <NP>:t2 <POST>
    => dict(frame=words(SLOT1, x1, adv, SLOT2),
            relation="IsA", text1=t1, text2=t2, adv=adv)

| <NP>:t1 <text "can">:x2 <ADVP>:adv <VP>:t2
    => dict(frame=words(SLOT1, x2, adv, t2),
            relation="CapableOf", text1=t1, text2=t2)

| <NP>:t1 (<text "ca n't"> | <text "cannot">):x2 <VP>:t2
    => dict(frame=words(SLOT1, x2, t2),
            relation="CapableOf", text1=t1, text2=t2, adv="not")

| <NP>:t1 <ADVP>:adv <VP>:t2
    => dict(frame=words(SLOT1, adv, SLOT2),
            relation="CapableOf", text1=t1, text2=t2, adv=adv)
)
"""

parser = PatternParserBase.makeGrammar(metapatterns, globals(), name="Metachunker")
def parse(tagged_sent):
    try:
        return parser(tagged_sent).apply("assertion")
    except ParseError:
        return None
print parser("ball_NN").apply("NN")
print parser("Sometimes_RB ball_NN causes_VBZ competition_NN").apply("assertion")
for sent in TaggedSentence.objects.all():
    print sent.text
    print "=>", parse(sent.text)
