#!/usr/bin/env python
from csc.corpus.parse.pcfgpattern import *
__test__ = False

def textrepr(rel, matchdict):
    if rel is None: return 'None'
    return "%s(%s, %s)" % (rel, matchdict.get(1), matchdict.get(2))

# A selection of sentences from OMCS that we should be able to parse correctly.
# This test suite does not vouch for the correctness or usefulness of the
# sentences it contains.

tests = [
    ("If you want to impanel a jury then you should ask questions.",
     "HasPrerequisite(impanel a jury, ask questions)"),
    ('"Lucy in the Sky with Diamonds" was a famous Beatles song',
     'IsA("Lucy in the Sky with Diamonds", a famous Beatles song)'),
    ("sound can be recorded",
     "ReceivesAction(sound, recorded)"),
    ("sounds can be soothing",
     "HasProperty(sounds, soothing)"),
    ("music can be recorded with a recording device",
     "ReceivesAction(music, recorded with a recording device)"),
    ("The first thing you do when you buy a shirt is try it on",
     "HasFirstSubevent(buy a shirt, try it on)"),
    ("One of the things you do when you water a plant is pour",
     "HasSubevent(water a plant, pour)"),
    ("A small sister can bug an older brother",
     "CapableOf(A small sister, bug an older brother)"),
    ("McDonald's hamburgers contain mayonnaise",
     "HasA(McDonald's hamburgers, mayonnaise)"),
    ("If you want to stab to death then you should get a knife.",
     "HasPrerequisite(stab to death, get a knife)"),
    ("carbon can cake hard",
     "CapableOf(carbon, cake hard)"),
    ("You would take a walk because your housemates were having sex in your bed.",
     "MotivatedByGoal(take a walk, your housemates were having sex in your bed)"),
    ("police can tail a suspect",
     "CapableOf(police, tail a suspect)"),
    ("people can race horses",
     "CapableOf(people, race horses)"),
    ("computer can mine data",
     "CapableOf(computer, mine data)"),
    ("to use a phone you must dial numbers",
     "HasSubevent(use a phone, dial numbers)"),
    ("People who are depressed are more likely to kill themselves",
     "HasProperty(People who are depressed, more likely to kill themselves)"),
    ("Bird eggs are good with toast and jam",
     "HasProperty(Bird eggs, good with toast and jam)"),
    ("housewife can can fruit",
     "CapableOf(housewife, can fruit)"),
    ("pictures can be showing nudity",
     "CapableOf(pictures, be showing nudity)"),
    ("a large house where the president of the US resides",
     "junk(a large house where the president of the US resides, None)"),
    ("girls are cute when they eat",
     "HasProperty(girls, cute when they eat)"),
    ("When books are on a bookshelf, you see only their spines.",
     "HasSubevent(books are on a bookshelf, you see only their spines)"),
    ("The effect of taking a phone call is finding out who is calling",
     "Causes(taking a phone call, finding out who is calling)"),
    ("There are 60 seconds in a minute",
     "AtLocation(60 seconds, a minute)"),
    ("Two wrongs don't make a right.",
     "CapableOf(Two wrongs, make a right)"),
    ("Somewhere someone can be is an art gallery",
     "AtLocation(someone, an art gallery)"),
    ("A person doesn't want war",
     "Desires(A person, war)"),
    ("That's weird",
     "junk(That's weird, None)"),
]

def run_tests():
    success = 0
    ntests = 0
    for testin, testout in tests:
        ntests += 1
        prob, frame, rel, matches = pattern_parse(testin)
        if textrepr(rel, matches) == testout:
            success += 1
            print "Success:", testin
        else:
            print "Failed:", testin
            print "Got:", textrepr(rel, matches)
            print "Expected:", testout
            pattern_parse(testin, 1)
            
    print "Tests complete: %d/%d" % (success, ntests)

run_tests.__test__ = False

if __name__ == '__main__':
    run_tests()

