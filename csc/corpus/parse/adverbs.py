import yaml
from corpus.models import Language
from conceptnet4.models import Frequency
frequencies = {
    'never': -10,
    "n't": -5,
    "doesn't": -5,
    "not": -5,
    "no": -5,
    "can't": -5,
    "won't": -5,
    "don't": -5,
    "couldn't": -5,
    "wouldn't": -5,
    "didn't": -5,
    "shouldn't": -5,
    "cannot": -5,
    "isn't": -5,
    "wasn't": -5,
    "aren't": -5,
    "weren't": -5,
    'rarely': -2,
    'infrequently': -2,
    'few': -2,
    'seldom': -2,
    'hardly': -2,
    'occasionally': 2,
    'sometimes': 4,
    'possibly': 4,
    'some': 4,
    'generally': 6,
    'typically': 6,
    'likely': 6,
    'probably': 6,
    'often': 6,
    'oftentimes': 6,
    'frequently': 6,
    'usually': 8,
    'most': 8,
    'mostly': 8,
    'almost': 9,
    'always': 10,
    'every': 10,
    'all': 10,
}
en = Language.get('en')
dbfreqs = {
    -10: Frequency.objects.get(language=en, text=u"never"),
    -5: Frequency.objects.get(language=en, text=u"not"),
    -2: Frequency.objects.get(language=en, text=u"rarely"),
    2: Frequency.objects.get(language=en, text=u"occasionally"),
    4: Frequency.objects.get(language=en, text=u"sometimes"),
    5: Frequency.objects.get(language=en, text=u""),
    6: Frequency.objects.get(language=en, text=u"generally"),
    8: Frequency.objects.get(language=en, text=u"usually"),
    9: Frequency.objects.get(language=en, text=u"almost always"),
    10: Frequency.objects.get(language=en, text=u"always"),
}

def map_adverb(adv):
    words = [w.lower() for w in adv.split()]
    minfreq = 11
    for word in words:
        if word in frequencies:
            minfreq = min(minfreq, frequencies[word])
    if minfreq == 11: minfreq = 5
    return dbfreqs[minfreq]

def demo():
    adverbs = set()
    for entry in yaml.load_all(open('delayed_sentences.yaml')):
        if entry is None: continue
        matches = entry.get('matches', {})
        adv = matches.get('a')
        if adv and adv not in adverbs:
            print adv,
            print map_adverb(adv)
            adverbs.add(adv)

