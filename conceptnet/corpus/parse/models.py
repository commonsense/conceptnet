from django.db import models
from csc.corpus.models import Language
from csc.conceptnet4.models import Relation

class FunctionFamilyDetector(object):
    def __init__(self,kb,language,family):
        self.language = language
        self.kb = kb
        self.family = family

    def __str__(self):
        return '<' + self.language.id + ': ' + \
                'function words (family=' + self.family + ')>'

    def __call__(self,word):
        return (word in self.kb)


class FunctionWord(models.Model):
    """ a word of particular significance to a parser """
    language = models.ForeignKey(Language)
    word = models.TextField()
    unique_together = (('language', 'word'),)

    def __str__(self):
        return "<" + self.language.id + ":" + self.word + ">"

    class Meta:
        db_table = 'functionwords'

class FunctionFamily(models.Model):
    """ defines a family of function words """
    family = models.TextField()
    f_word = models.ForeignKey(FunctionWord)
    unique_together = (('family', 'f_word'),)

    def __str__(self):
        return self.family + ": " + str(self.f_word)

    class Meta:
        db_table = 'functionfamilies'

    @staticmethod
    def build_function_detector(language, family):
        # Prepare the kb
        words = list(FunctionFamily.objects.filter(family=family,f_word__language=language).values_list('f_word__word', flat=True))

        return FunctionFamilyDetector(words,language,family)

class ParsingPattern(models.Model):
    pattern = models.TextField(blank=False)
    predtype = models.ForeignKey(Relation)
    polarity = models.IntegerField()
    sort_order = models.IntegerField()
    language = models.ForeignKey(Language)

    class Meta:
        db_table = 'parsing_patterns'


class SecondOrderPattern(models.Model):
    regex = models.TextField()
    language = models.ForeignKey(Language)
    use_group = models.IntegerField(default=0)
    abort = models.BooleanField(default=False)

    def __str__(self):
        return "(" + self.language.id + ") /" + self.regex + "/"

    def compile(self):
        self._compiled_regex = re.compile( self.regex )

    def __call__(self, text):
        if not hasattr( self, '_compiled_regex' ): self.compile()
        return self._compiled_regex.search(text)

    class Meta:
        db_table = 'secondorderpatterns'

    class SecondOrderSplitter:
        def __init__(self,patterns,language):
            self.language = language
            self.patterns = patterns

        def __call__(self,text):
                 # FIXME: THIS IS A HIDEOUSLY USELESS ROUTINE
            for pattern in self.patterns:
                m = pattern(text)
                if m:
                    if pattern.abort: text = ''
                    else: text = m.groups()[pattern.use_group]
            return [text]

        def __str__(self):
            return "Second order splitter (" + self.language.id + ")"

    @staticmethod
    def build_splitter(language):
        return SecondOrderPattern.SecondOrderSplitter(language.secondorderpattern_set.all(), language)
