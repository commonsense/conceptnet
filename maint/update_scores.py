from csc_utils.batch import queryset_foreach
from conceptnet.models import Sentence, Assertion, RawAssertion


def update_scores():
    queryset_foreach(Assertion, lambda x: x.update_score(),
    batch_size=100)
    queryset_foreach(RawAssertion, lambda x: x.update_score(),
    batch_size=100)
    # queryset_foreach(Sentence.objects.exclude(language__id='en'), lambda x: x.update_score(), batch_size=100)

def fix_raw_assertion_vote(raw):
    for vote in raw.votes.all():
        raw.assertion.set_rating(vote.user, vote.vote)

def update_votes():
    queryset_foreach(RawAssertion, lambda x: fix_raw_assertion_vote(x), batch_size=100)

