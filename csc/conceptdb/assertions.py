import mongoengine as mon
from csc.conceptnet5.justify import Justification, JustifiedObject, Reason
from csc.conceptnet5.metadata import Relation, Dataset, Language

class Expression(mon.EmbeddedDocument, JustifiedObject):
    text = mon.StringField(required=True)
    justification = mon.EmbeddedDocumentField(Justification)

class Assertion(mon.Document, JustifiedObject):
    dataset = mon.StringField(required=True)
    relation = mon.StringField(required=True)
    arguments = mon.ListField(mon.StringField())
    complete = mon.IntField()
    context = mon.StringField()
    polarity = mon.IntField()
    expressions = mon.ListField(mon.EmbeddedDocumentField(Expression))
    justification = mon.EmbeddedDocumentField(Justification)

    meta = {'indexes': ['arguments',
                        ('arguments', '-justification.confidence'),
                        ('dataset', 'relation', 'polarity'),
                        'context',
                        'justification.support',
                        'justification.oppose',
                        'justification.confidence',
                       ]}

    @staticmethod
    def make(dataset, relation, arguments, polarity=1, context=None):
        try:
            a = Assertion.objects.get(
                dataset=dataset,
                relation=relation,
                arguments=arguments,
                polarity=polarity,
                context=context
            )
        except Assertion.DoesNotExist:
            a = Assertion(
                dataset=dataset,
                relation=relation,
                arguments=arguments,
                complete=(None not in arguments),
                context=context,
                polarity=polarity,
                expressions=[],
                justification=Justification.empty()
            )
            a.save()
        return a

    def connect_to_sentence(dataset, text):
        sent = Sentence.make(dataset, text)
        sent.

    def get_dataset(self):
        return Dataset.objects.with_id(self.dataset)

    def get_relation(self):
        return Relation.objects.with_id(self.relation)
    
    def check_consistency(self):
        # TODO: more consistency checks
        self.justification.check_consistency()

class Sentence(mon.Document, JustifiedObject):
    text = mon.StringField(required=True)
    words = mon.ListField(mon.StringField())
    dataset = mon.StringField(required=True)
    justification = mon.EmbeddedDocumentField(Justification)
    derived_assertions = mon.ListField(mon.ReferenceField(Assertion))

    @staticmethod
    def make(dataset, text):
        if isinstance(dataset, basestring):
            dataset = Dataset.objects.with_id(dataset)
        try:
            s = Sentence.objects.get(dataset=dataset, text=text)
        except Sentence.DoesNotExist:
            s = Sentence(
                text=text,
                dataset=dataset.name,
                words=dataset.nl.normalize(text).split(),
                justification=Justification.empty(),
                derived_assertions=[]
            )
            s.save()
        return s
    
    def add_assertion(self, assertion):
        self.update(derived_assertions=self.derived_assertions + [assertion])
