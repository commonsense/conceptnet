#python-encoding: UTF-8

from csc.nl import NLTools, get_nl
import re

def ja_enc(string):
    ''' Encodes an ascii, unicode, or utf-8 to utf-8, hopefully without making a fuss '''

    try:
        s = str(string)
    except:
        s = string

    try:
        d = s.decode('utf-8', 'ignore')
    except:
        d = s

    try:
        e = d.encode('utf-8', 'ignore')
    except:
        e = d

    return e

def ja_dec(string):
    ''' Decodes a utf-8 string to unicode, hopefully without making a fuss '''
    try:
        e = string.decode('utf-8')
    except:
        e = string

    return e

def has_hiragana(string):
    ''' True if the string contains hiragana '''

    u = unicode(ja_enc(string), 'utf-8')
    for c in u:
        if c >= u'\u3040' and c <= u'\u309F': return True
    return False

def has_katakana(string):
    ''' True if the string contains katakana '''

    u = unicode(ja_enc(string), 'utf-8')
    for c in u:
        if c >= u'\u30A0' and c <= u'\u30FF': return True
    return False

def has_romaji(string):
    ''' True if the string contains roman characters '''

    u = unicode(ja_enc(string), 'utf-8')
    for c in u:
        if c >= u'\u0041' and c <= u'\u005A': return True
        if c >= u'\u0061' and c <= u'\u007A': return True
    return False

def has_romandigit(string):
    ''' True if the string contains romaji digits (ascii 0-9) '''

    u = unicode(ja_enc(string), 'utf-8')
    for c in u:
        if c >= u'\u0030' and c <= u'\u0039': return True
    return False

def has_jadigit(string):
    ''' True if the string contains japanese double-width digits '''

    u = unicode(ja_enc(string), 'utf-8')
    for c in u:
        if c >= u'\uff10' and c <= u'\uff19': return True
    return False

def has_digit(string):
    ''' True if the string contains roman digits or japanese digits '''
    return has_romandigit(string) or has_jadigit(string)

def has_kanji(string):
    ''' True if the string contains kanji '''

    u = unicode(ja_enc(string), 'utf-8')
    for c in u:
        if c >= u'\u4E00' and c <= u'\u9FBF': return True
    return False

def clean_input(text):
    ''' Does conversion on the input to avoid problems in parsing '''

    text     = ja_enc(text)
    ja_digit = [ ja_enc(x) for x in ['０', '１', '２', '３', '４', '５', '６', '７', '８', '９'] ]

    for i in range(0, 10):
        text = text.replace(str(i), ja_digit[i])

    p    = re.compile(' +', re.UNICODE)
    text = p.sub('', text)

    p    = re.compile('　', re.UNICODE)
    text = p.sub('', text)

    p    = re.compile('\?', re.UNICODE)
    text = p.sub(ja_enc('？'), text)

    p    = re.compile('!', re.UNICODE)
    text = p.sub(ja_enc('！'), text)

    return ja_enc(text)

def utf8_len(text):
    ''' Returns the number of characters in a utf-8 string '''
    return len(unicode(ja_enc(text), 'utf-8'))

class lazy_property(object):
    ''' Decorator for delayed-initialization of properties '''

    def __init__(self, func):
        '''
        A lazy decorator. Runs a function only once to get a
        property's value; after that, the precomputed value is used.

        Replace expensive computations in __init__ with this.
        '''
        self.func     = func
        self.__name__ = func.__name__
        self.__doc__  = func.__doc__
        self.__dict__.update(func.__dict__)

    def __get__(self, instance, cls):
        assert self.__name__ not in instance.__dict__
        result = instance.__dict__[self.__name__] = self.func(instance)
        return result

    @staticmethod
    def preset(cls, name, val):
        cls.__dict__[name] = val

