__version__ = "4.0b2"
__author__ = "kcarnold@media.mit.edu, rspeer@media.mit.edu, jalonso@media.mit.edu, havasi@media.mit.edu, hugo@media.mit.edu"
__url__ = 'conceptnet.media.mit.edu'
from django.db import models
from django.contrib.auth.models import User
from django.utils.functional import memoize
from datetime import datetime
from voting.models import Vote
from events.models import Event, Activity
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from csc.nl import get_nl
import re

class ScoredModel(object):
    """
    A ScoredModel is one that users can vote on through a Django-based Web
    site.

    The score is cached in a column of the object's database table, and updated
    whenever necessary.

    This makes use of the `django-voting` library. However, if you alter votes
    by using the `django-voting` library directly, the score will not be
    updated correctly.
    """
    def get_rating(self, user):
        """
        Get the Vote object representing a certain user's vote on a certain
        object. Returns None if the user has not voted on that object.
        """
        return getattr(Vote.objects.get_for_user(self, user), 'vote', None)

    def set_rating(self, user, val, activity):
        """
        Set a user's Vote on a certain object. If the user has previously voted
        on that object, it removes the old vote.
        """
        Vote.objects.record_vote(self, user, val)
        Event.record_event(self, user, activity)
        #self.update_score()

    def update_score(self):
        """
        Ensure that the `score` property of this object agrees with the sum of
        the votes it has received.
        """
        self.score = Vote.objects.get_score(self)['score']
        self.save()

# Register signals to make score updates happen automatically.
def denormalize_votes(sender, instance, created=False, **kwargs):
    """This recalculates the vote total for the object
    being voted on"""
    instance.object.update_score()

models.signals.post_save.connect(denormalize_votes, sender=Vote)
models.signals.post_delete.connect(denormalize_votes, sender=Vote)

cached_langs = {}
def get_lang(lang_code):
    """
    Get a Language instance for a particular language, and remember it so that
    it doesn't have to be looked up again.
    """
    return Language.objects.get(id=lang_code)
get_lang = memoize(get_lang, cached_langs, 1)

class Language(models.Model):
    """
    A database object representing a language.

    Instances of Language can be used in filter expressions to select only
    objects that apply to a particular language. For example:
    
    >>> en = Language.get('en')
    >>> english_sentences = Sentence.objects.filter(language=en)
    """
    id = models.CharField(max_length=16,primary_key=True)
    name = models.TextField(blank=True)
    sentence_count = models.IntegerField(default=0)

    def __str__(self):
        return "%s (%s)" % (self.name, self.id)

    @staticmethod
    def get(id):
        """
        Get a language from its ISO language code.

        Some relevant language codes::

            en = English
            pt = Portuguese
            ko = Korean
            ja = Japanese
            nl = Dutch
            es = Spanish
            fr = French
            ar = Arabic
            zh = Chinese
        """
        if isinstance(id,Language): return id
        return get_lang(id)

    @property
    def nl(self):
        """
        A collection of natural language tools for a language.

        See :mod:`csc.nl` for more information on using these tools.
        """
        return get_nl(self.id)

class Sentence(models.Model, ScoredModel):
    """
    A statement entered by a contributor, in unparsed natural language.
    """
    text = models.TextField(blank=False)
    creator = models.ForeignKey(User)
    created_on = models.DateTimeField(default=datetime.now)
    language = models.ForeignKey(Language)
    activity = models.ForeignKey(Activity)
    score = models.IntegerField(default=0)
    votes = generic.GenericRelation(Vote)

    def __unicode__(self):
        return  u'<' + self.language.id + u': ' + \
                u'"' + self.text + u'"' + \
                u'(by:' + unicode(self.creator_id) + \
                u' activity:' + self.activity.name + \
                u')>'
    

    def update_consistency(self):
        """
        Assume that the creator of this sentence voted for it, and calculate
        the score.
        """
        try:
            if self.creator is not None and self.get_rating(self.creator) is None:
                if self.creator.username != 'verbosity':
                    Vote.objects.record_vote(self, self.creator, 1)
            self.update_score()
        except User.DoesNotExist:
            self.creator = User.objects.get(username='_ghost')
            Vote.objects.record_vote(self, self.creator, 1)
            self.update_score()

class TaggedSentence(models.Model):
    """
    The results of running a sentence through a tagger such as MXPOST.

    We could use this as a step in parsing ConceptNet, but we currently don't.
    """
    text = models.TextField()
    language = models.ForeignKey(Language)
    sentence = models.ForeignKey(Sentence, primary_key=True)
    
    def tagged_words(self):
        for part in self.text.split(" "):
            word, tag = part.rsplit("/", 1)
            yield word, tag
    
    def __unicode__(self):
        return self.text
    
class DependencyParse(models.Model):
    """
    Each instance of DependencyParse is a single link in the Stanford
    dependency parse of a sentence.
    """
    sentence = models.ForeignKey('Sentence')
    linktype = models.CharField(max_length=20)
    word1 = models.CharField(max_length=100)
    word2 = models.CharField(max_length=100)
    index1 = models.IntegerField()
    index2 = models.IntegerField()
    
    _PARSE_RE = re.compile(r"(.+)\((.*)-(\d+)'*, (.*)-(\d+)'*\)")
    
    @staticmethod
    def from_string(sentence_id, depstring):
        try:
            link, w1, i1, w2, i2 = DependencyParse._PARSE_RE.match(depstring).groups()
        except AttributeError:
            raise ValueError("didn't match regex pattern: %s" % depstring)
        dep_obj = DependencyParse(sentence_id=sentence_id, linktype=link,
                                  word1=w1, index1=int(i1),
                                  word2=w2, index2=int(i2))
        return dep_obj

    def __unicode__(self):
        return u'%s(%s_%d, %s_%d) (sent %d)' % (
            self.linktype, self.word1, self.index1, self.word2, self.index2,
            self.sentence_id)

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
        db_table = 'nl_frequency'
