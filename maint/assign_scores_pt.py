from csc.util import queryset_foreach
from csc.conceptnet4.models import Sentence, Assertion, RawAssertion, Language, Vote

pt = Language.get('pt')
def process(raw):
    if pt.nl.is_blacklisted(raw.surface1.text) or pt.nl.is_blacklisted(raw.surface2.text):
        raw.votes.delete()
    else:
        Vote.objects.record_vote(raw, raw.sentence.creator, 1)

queryset_foreach(RawAssertion.objects.filter(language=pt), process, batch_size=100)

