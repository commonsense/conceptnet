import mongoengine as mon

class Reason(mon.Document):
    name = mon.StringField(required=True, primary_key=True)
    type = mon.StringField(required=True)
    reliability = mon.FloatField(default=0.0)

class JustifiedObject(object):
    """
    This mixin provides convenience methods for working with an object with
    a `justification` field.
    """
    def confidence(self):
        return self.justification.confidence_score

    def add_support(self, reasons):
        self.update(justification=self.justification.add_support(reasons))
        return self
    
    def add_opposition(self, reasons):
        self.update(justification=self.justification.add_opposition(reasons))
        return self
    
    def get_support(self):
        return self.justification.get_support()
    
    def get_oppose(self):
        return self.justification.get_oppose()


class Justification(mon.EmbeddedDocument):
    """
    A Justification is a data structure that keeps track of evidence for
    and against a statement being correct.
    
    The evidence comes in the form of two "and/or" trees of Reasons: one
    tree of supporting reasons and one tree of opposing reasons. The trees
    are expressed as a list of lists, representing a disjunction of
    conjunctions.

    These lists of lists would be difficult to make MongoDB indices from,
    however, so internally they are expressed as two lists:

      - The *flat list* is a simple list of Reasons, without the tree
        structure.
      - The *offset list* gives *n*-1 indices into the flat list, so that
        splitting the flat list at those indices gives the *n* conjunctions.

    """
    support_flat = mon.ListField(mon.ReferenceField(Reason))
    oppose_flat = mon.ListField(mon.ReferenceField(Reason))
    support_offsets = mon.ListField(mon.IntField())
    oppose_offsets = mon.ListField(mon.IntField())
    confidence_score = mon.FloatField(default=0.0)

    @staticmethod
    def empty():
        """
        Get the default, empty justification.
        """
        return Justification(
            support_flat=[],
            oppose_flat=[],
            support_offsets=[],
            oppose_offsets=[],
            confidence_score=0.0
        )

    @staticmethod
    def make():
        """
        Make a Justification data structure from a tree of supporting reasons
        and a tree of opposing reasons.
        """
        # TODO: not implemented yet!
        raise NotImplementedError

    def check_consistency(self):
        for offset in self.support_offsets:
            assert offset < len(self.support)
        for offset in self.oppose_offsets:
            assert offset < len(self.oppose)
        for reason in self.support_flat:
            assert isinstance(reason, Reason)
        for reason in self.oppose_flat:
            assert isinstance(reason, Reason)

    def add_conjunction(self, reasons, flatlist, offsetlist):
        for r in reasons:
            if not isinstance(r, Reason): raise TypeError
        offset = len(flatlist)
        flatlist.extend(reasons)
        offsetlist.append(offset)

    def add_support(self, reasons):
        self.add_conjunction(reasons, self.support_flat, self.support_offsets)
        return self

    def add_opposition(self, reasons):
        self.add_conjunction(reasons, self.oppose_flat, self.oppose_offsets)
        return self
    
    def get_disjunction(self, flatlist, offsetlist):
        conjunctions = []
        prev_offset = 0
        for offset in offsetlist:
            conjunctions.append(flatlist[prev_offset:offset])
            prev_offset = offset
        conjunctions.append(flatlist[prev_offset:])
        return conjunctions
    
    def get_support(self):
        return self.get_disjunction(self.support, self.support_offsets)

    def get_opposition(self):
        return self.get_disjunction(self.oppose_flat, self.oppose_offsets)
    
    # Aliases
    add_oppose = add_opposition
    get_oppose = get_opposition

