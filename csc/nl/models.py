from django.db import models
from csc.corpus.models import Language

class AutoreplaceRule(models.Model):
    """
    An AutoreplaceRule indicates that one word should be replaced by another.
    These rules are used to correct misspellings when parsing ConceptNet.
    """
    language = models.ForeignKey(Language)
    family = models.CharField(blank=False,max_length=128)
    match = models.CharField(blank=False,max_length=128)
    replace_with = models.CharField(blank=True,max_length=128)
    unique_together = (('language', 'family', 'match'),)

    def __str__(self):
        return " (" + str(self.language.id) + ") " + self.family + " [" + self.match + " => " + self.replace_with + "]"

    class Autoreplacer:
        def __init__(self,kb,language,family):
            self.language = language
            self.kb = kb
            self.family = family

        def __str__(self):
            return "(" + str(self.language.id) +") " + self.family + " autoreplace KB"

        def __call__(self, text):
            toks = text.split()
            toks = [self.kb.get(x,x) for x in toks]
            return ' '.join(toks)

    @staticmethod
    def build_autoreplacer(language,family):
        kb = {}
        for rule in language.autoreplacerule_set.filter(family=family):
            kb[rule.match] = rule.replace_with
        return AutoreplaceRule.Autoreplacer(kb,language,family)

    class Admin:
        pass

class FunctionClass(models.Model):
    """A class of function words."""
    name = models.TextField(unique=True)

    def __unicode__(self):
        return u"<FunctionClass: %s>" % self.name

    def function_word_set(self, language):
        "Get a set of all the words in this class."
        words = self.words.filter(language=language).values_list('word', flat=True)
        return set(words)

class Frequency(models.Model):
    """
    A Frequency is attached to an :class:`Assertion` to indicate how often
    it is the case. Each Frequency is attached to a natural-language modifier
    (generally an adverb), and has a value from -10 to 10.
    """
    language = models.ForeignKey(Language)
    text = models.CharField(max_length=50, blank=True,
                            help_text='The frequency adverb used (e.g., "always", "sometimes", "never"). Empty means that the sentence has no frequency adverb.')
    # FIXME: is this help text still valid?
    value = models.IntegerField(help_text='A number between -10 and 10 indicating a rough numerical frequency to associate with this word. "always" would be 10, "never" would be -10, and not specifying a frequency adverb in English is specified to be 5.')

    def __unicode__(self):
        return u'<%s: "%s" (%d)>' % (self.language.id, self.text, self.value)

    class Meta:
        unique_together = (('language', 'text'),)
        verbose_name = 'frequency adverb'
        verbose_name_plural = 'frequency adverbs'

class FunctionWord(models.Model):
    """
    A FunctionWord is a word that should be handled specially by a parser or
    normalizer. FunctionWords can be grouped into different *classes*
    depending on how they should be handled.

    The most pertinent family of FunctionWord is *stop words*, words that
    should be ignored when normalizing a phrase of text.
    """
    language = models.ForeignKey(Language)
    word = models.TextField()
    functionclass = models.ForeignKey(FunctionClass, null=False, related_name='words')

    def __unicode__(self):
        return "<" + self.language.id + ":" + self.word + ">"

