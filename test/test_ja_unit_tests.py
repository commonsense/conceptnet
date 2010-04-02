#python-encoding: UTF-8

from csc.conceptnet4.models import Concept
from csc.nl.ja.system import *
from csc.nl.ja.debug  import *
from csc.corpus.models import *
import operator

# Import the data for our test #
from test_ja_unit_tests_data import *

####################################################################################################
## Options #########################################################################################
####################################################################################################
assert_on_fail = True
use_color      = True

## Variables #######################################################################################
ja           = get_lang('ja')
ja_nl        = ja.nl
d            = JaDebug(use_color)
i            = "\t"
db_parsed    = 0
db_successes = 0
db_failures  = 0
successes    = 0
failures     = 0

class JaUnitTest():
    def __init__(self, text):
        self.text      = text
        self.utterance = ja_nl.utterance(text)

    def do_test(self, name, control):
        return operator.attrgetter(k)(self)(k, v)

    def default_test(self, name, control, to_str = None, test_fun = None):
        if not to_str:
            to_str = lambda x: ja_dec(ja_enc(x))

        control = ja_dec(control)

        output  = i + d.hl1(name) + "... " + "\n"
        output += i + i + ja_dec(d.hl4("Control: " + to_str(control))) + "\n"

        if test_fun:
            result = test_fun()
        else:
            result = operator.attrgetter(name)(ja_nl)(self.text)

        output += i + i + "Output:  " + to_str(result)
        print(ja_enc(output))

        ok = control == result
        if not ok and assert_on_fail:
            self.utterance.dump(use_color)
            raise ValueError("Unit Test Failed!")

        return ok

    tokenize    = default_test
    normalize   = default_test
    untokenize  = default_test
    stem_word   = default_test
    is_stopword = default_test

    def lemma_split(self, name, control):
        return self.default_test( \
            name    = name,
            control = (ja_dec(control[0]), ja_dec(control[1])),
            to_str  = lambda t: ja_dec('"' + ja_enc(t[0]) + '", "' + ja_enc(t[1]) + '"')
        )

    def lemma_split_keep(self, name, control):
        return self.default_test( \
            name     = 'lemma_split',
            control  = (ja_dec(control[0]), ja_dec(control[1])),
            to_str  = lambda t: ja_dec('"' + ja_enc(t[0]) + '", "' + ja_enc(t[1]) + '"'),
            test_fun = lambda: ja_nl.lemma_split(self.text, True)
        )

    def word_split(self, name, control):
        return self.default_test( \
            name    = name,
            control = (ja_dec(control[0]), ja_dec(control[1])),
            to_str  = lambda t: ja_dec('"' + ja_enc(t[0]) + '", "' + ja_enc(t[1]) + '"')
        )

print("\n")
print(d.header("---------------------------------------------"))
print(d.header("-- Sentence Tests ---------------------------"))
print(d.header("---------------------------------------------"))
try:
    for text, data in sentences.items():
        print(d.header("\nTesting sentence... ") + d.hl3(text))

        unit_test = JaUnitTest(text)

        for k, v in data.items():
            if unit_test.do_test(k, v):
                successes += 1
                print('\t[' + d.hl2('OK') + ']')
            else:
                failures += 1
                print('\t[' + d.error('FAIL') + ']')

except KeyboardInterrupt:
    print("Skipping Sentence Tests...")

print("\n")
print(d.header("---------------------------------------------"))
print(d.header("-- Word Tests -------------------------------"))
print(d.header("---------------------------------------------"))
try:
    for text, data in words.items():
        print(d.header("\nTesting word... ") + d.hl3(text))

        unit_test = JaUnitTest(text)

        for k, v in data.items():
            if unit_test.do_test(k, v):
                successes += 1
                print('\t[' + d.hl2('OK') + ']')
            else:
                failures += 1
                print('\t[' + d.error('FAIL') + ']')

except KeyboardInterrupt:
    print("Skipping Word Tests...")

print("\n")
print(d.header("---------------------------------------------"))
print(d.header("-- Database Tests ---------------------------"))
print(d.header("---------------------------------------------"))
try:
    count    = ja.sentence_count
    percent  = 0.05
    interval = int(count * percent)

    print(d.header("\nParsing all database sentences... " + str(count)))
    for s in Sentence.objects.filter(language = 'ja'):
        try:
            u             = ja_nl.utterance(s.text)
            db_successes += 1
        except RuntimeError, e:
            print(unicode(e).encode('utf-8'))
            db_failures += 1

        db_parsed += 1
        if not (db_parsed % interval):
            s = d.hl2("%(db_parsed)5d") + d.hl3(" [") + d.hl2("%(interval)4d%%") + d.hl3("]")
            print(s % {'db_parsed': db_parsed, 'interval': (100 * percent) * db_parsed / interval})

except KeyboardInterrupt:
    print("Skipping Database Parse Tests...")

print("\n")
print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
print(str(successes + failures) + " tests complete.")
print(d.header(str(successes) + " succeeded."))
print(d.error(str(failures) + " failed."))
print("\n")
print(str(db_parsed) + "/" + str(ja.sentence_count) + " database sentence tests complete.")
print(d.header(str(db_successes) + " succeeded."))
print(d.error(str(db_failures) + " failed."))

