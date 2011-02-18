from django.conf import settings
from django.db import connection, models

try:
    from django.db.models.sql.aggregates import Aggregate
except ImportError:
    supports_aggregates = False
else:
    supports_aggregates = True

from django.contrib.contenttypes.models import ContentType

if supports_aggregates:
    class CoalesceWrapper(Aggregate):
        sql_template = 'COALESCE(%(function)s(%(field)s), %(default)s)'
    
        def __init__(self, lookup, **extra): 
            self.lookup = lookup
            self.extra = extra
    
        def _default_alias(self):
            return '%s__%s' % (self.lookup, self.__class__.__name__.lower())
        default_alias = property(_default_alias)
    
        def add_to_query(self, query, alias, col, source, is_summary):
            super(CoalesceWrapper, self).__init__(col, source, is_summary, **self.extra)
            query.aggregate_select[alias] = self


    class CoalesceSum(CoalesceWrapper):
        sql_function = 'SUM'


    class CoalesceCount(CoalesceWrapper):
        sql_function = 'COUNT'


class VoteManager(models.Manager):
    def get_score(self, obj):
        """
        Get a dictionary containing the total score for ``obj`` and
        the number of votes it's received.
        """
        ctype = ContentType.objects.get_for_model(obj)
        result = self.filter(object_id=obj._get_pk_val(),
                             content_type=ctype).extra(
            select={
                'score': 'COALESCE(SUM(vote), 0)',
                'num_votes': 'COALESCE(COUNT(vote), 0)',
        }).values_list('score', 'num_votes')[0]

        return {
            'score': int(result[0]),
            'num_votes': int(result[1]),
        }

    def get_scores_in_bulk(self, objects):
        """
        Get a dictionary mapping object ids to total score and number
        of votes for each object.
        """
        object_ids = [o._get_pk_val() for o in objects]
        if not object_ids:
            return {}
        
        ctype = ContentType.objects.get_for_model(objects[0])
        
        if supports_aggregates:
            queryset = self.filter(
                object_id__in = object_ids,
                content_type = ctype,
            ).values(
                'object_id',
            ).annotate(
                score = CoalesceSum('vote', default='0'),
                num_votes = CoalesceCount('vote', default='0'),
            )
        else:
            queryset = self.filter(
                object_id__in = object_ids,
                content_type = ctype,
                ).extra(
                    select = {
                        'score': 'COALESCE(SUM(vote), 0)',
                        'num_votes': 'COALESCE(COUNT(vote), 0)',
                    }
                ).values('object_id', 'score', 'num_votes')
            queryset.query.group_by.append('object_id')
        
        vote_dict = {}
        for row in queryset:
            vote_dict[row['object_id']] = {
                'score': int(row['score']),
                'num_votes': int(row['num_votes']),
            }
        
        return vote_dict

    def record_vote(self, obj, user, vote):
        """
        Record a user's vote on a given object. Only allows a given user
        to vote once, though that vote may be changed.

        A zero vote indicates that any existing vote should be removed.
        """
        if vote not in (+1, 0, -1):
            raise ValueError('Invalid vote (must be +1/0/-1)')
        ctype = ContentType.objects.get_for_model(obj)
        try:
            v = self.get(user=user, content_type=ctype,
                         object_id=obj._get_pk_val())
            if vote == 0:
                v.delete()
            else:
                v.vote = vote
                v.save()
        except models.ObjectDoesNotExist:
            if vote != 0:
                self.create(user=user, content_type=ctype,
                            object_id=obj._get_pk_val(), vote=vote)

    def get_top(self, Model, limit=10, reversed=False):
        """
        Get the top N scored objects for a given model.

        Yields (object, score) tuples.
        """
        ctype = ContentType.objects.get_for_model(Model)
        query = """
        SELECT object_id, SUM(vote) as %s
        FROM %s
        WHERE content_type_id = %%s
        GROUP BY object_id""" % (
            connection.ops.quote_name('score'),
            connection.ops.quote_name(self.model._meta.db_table),
        )

        # MySQL has issues with re-using the aggregate function in the
        # HAVING clause, so we alias the score and use this alias for
        # its benefit.
        if settings.DATABASE_ENGINE == 'mysql':
            having_score = connection.ops.quote_name('score')
        else:
            having_score = 'SUM(vote)'
        if reversed:
            having_sql = ' HAVING %(having_score)s < 0 ORDER BY %(having_score)s ASC LIMIT %%s'
        else:
            having_sql = ' HAVING %(having_score)s > 0 ORDER BY %(having_score)s DESC LIMIT %%s'
        query += having_sql % {
            'having_score': having_score,
        }

        cursor = connection.cursor()
        cursor.execute(query, [ctype.id, limit])
        results = cursor.fetchall()

        # Use in_bulk() to avoid O(limit) db hits.
        objects = Model.objects.in_bulk([id for id, score in results])

        # Yield each object, score pair. Because of the lazy nature of generic
        # relations, missing objects are silently ignored.
        for id, score in results:
            if id in objects:
                yield objects[id], int(score)

    def get_bottom(self, Model, limit=10):
        """
        Get the bottom (i.e. most negative) N scored objects for a given
        model.

        Yields (object, score) tuples.
        """
        return self.get_top(Model, limit, True)

    def get_for_user(self, obj, user):
        """
        Get the vote made on the given object by the given user, or
        ``None`` if no matching vote exists.
        """
        if not user.is_authenticated():
            return None
        ctype = ContentType.objects.get_for_model(obj)
        try:
            vote = self.get(content_type=ctype, object_id=obj._get_pk_val(),
                            user=user)
        except models.ObjectDoesNotExist:
            vote = None
        return vote

    def get_for_user_in_bulk(self, objects, user):
        """
        Get a dictionary mapping object ids to votes made by the given
        user on the corresponding objects.
        """
        vote_dict = {}
        if len(objects) > 0:
            ctype = ContentType.objects.get_for_model(objects[0])
            votes = list(self.filter(content_type__pk=ctype.id,
                                     object_id__in=[obj._get_pk_val() \
                                                    for obj in objects],
                                     user__pk=user.id))
            vote_dict = dict([(vote.object_id, vote) for vote in votes])
        return vote_dict
