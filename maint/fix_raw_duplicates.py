from csc.util import queryset_foreach
from csc.conceptnet4.models import Sentence, Assertion, RawAssertion, Vote

def sort_and_check():
    all_raw = RawAssertion.objects.filter(language__id='zh-Hant').order_by('language', 'surface1__text', 'surface2__text', 'frame__id')
    print "Checking for duplicates."
    prev = None
    for raw in all_raw:
        print raw.id
        if equivalent(prev, raw):
            print (u"%s[%s] == %s[%s]" % (prev, prev.creator.username, raw, raw.creator.username)).encode('utf-8')
            prev = switch_raw(raw, prev)
        else:
            prev = raw

def equivalent(raw1, raw2):
    if raw1 is None: return False
    return (raw1.language.id == raw2.language.id
            and raw1.surface1.text == raw2.surface1.text
            and raw1.surface2.text == raw2.surface2.text
            and raw1.frame.id == raw2.frame.id)

def switch_raw(oldraw, newraw):
    # avoid the generic username when possible
    if newraw.creator.username == 'openmind':
        oldraw, newraw = newraw, oldraw
    for vote in oldraw.votes.all():
        nvotes = Vote.objects.filter(user=vote.user, object_id=newraw.id).count()
        if nvotes == 0:
            vote.object = newraw
            vote.save()
        else:
            vote.delete()
    oldraw.delete()
    newraw.update_score()
    newraw.save()
    return newraw

if __name__ == '__main__':
    sort_and_check()

