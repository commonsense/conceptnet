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
        return Assertion(
            dataset=dataset,
            relation=relation,
            arguments=arguments,
            polarity=polarity,
            context=context
        )

    def get_dataset(self):
        return Dataset.objects.with_id(self.dataset)

    def get_relation(self):
        return Relation.objects.with_id(self.relation)
    
    def check_consistency(self):
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
        return Sentence(
            text=text,
            dataset=dataset.name,
            words=dataset.language.nl.normalize(text).split(),
            justification=Justification.default(),
            derived_assertions=[]
        )

