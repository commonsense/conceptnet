from csc.conceptnet.models import en
from csc.nl.models import FunctionClass, AutoreplaceRule
import codecs

black = FunctionClass.objects.get(name='blacklist')
for language in ('en',):
    blacklist = sorted(black.function_word_set(language))
    out = codecs.open(language+'/blacklist.txt', 'w', encoding='utf-8')
    for word in blacklist:
        print >> out, word
    out.close()

stop = FunctionClass.objects.get(name='stop')
for language in ('en', 'hu', 'es', 'pt', 'nl'):
    stopwords = sorted(stop.function_word_set(language))
    out = codecs.open(language+'/stop.txt', 'w', encoding='utf-8')
    for word in stopwords:
        print >> out, word
    out.close()

for swaplist in ('swap4', 'autocorrect'):
    out = codecs.open('en/%s.txt' % swaplist, 'w', encoding='utf-8')
    for replacerule in AutoreplaceRule.objects.filter(language__id='en',
                                                      family=swaplist):
        print >> out, "%s => %s" % (replacerule.match, replacerule.replace_with)
    out.close()

