from csc.nl.euro import LemmatizedEuroNL

def NL():
    exceptions = {
        u'people': (u'person', u's'),
        u'ground': (u'ground', u''),
    }
    return LemmatizedEuroNL('en', exceptions=exceptions)
