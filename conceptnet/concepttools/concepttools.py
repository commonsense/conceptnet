
# We really want Python 2.5, but for 2.4 a hack will work.
try:
    from collections import defaultdict
except ImportError:
    class defaultdict(dict):
        def __init__(self, default_factory=None, *a, **kw):
            if (default_factory is not None and
                not hasattr(default_factory, '__call__')):
                raise TypeError('first argument must be callable')
            dict.__init__(self, *a, **kw)
            self.default_factory = default_factory
        def __getitem__(self, key):
            try:
                return dict.__getitem__(self, key)
            except KeyError:
                return self.__missing__(key)
        def __missing__(self, key):
            if self.default_factory is None:
                raise KeyError(key)
            self[key] = value = self.default_factory()
            return value
        def __reduce__(self):
            if self.default_factory is None:
                args = tuple()
            else:
                args = self.default_factory,
            return type(self), args, None, None, self.items()
        def copy(self):
            return self.__copy__()
        def __copy__(self):
            return type(self)(self.default_factory, self)
        def __deepcopy__(self, memo):
            import copy
            return type(self)(self.default_factory,
                              copy.deepcopy(self.items()))
        def __repr__(self):
            return 'defaultdict(%s, %s)' % (self.default_factory,
                                            dict.__repr__(self))

import cPickle as pickle
from csamoa.corpus.models import Language
from csamoa.representation.presentation.models import Stem, Predicate
from csamoa.representation.parsing.tools.models import PredicateType

from types import StringType, DictType, IntType
import math

# Get only a set of values out of a QuerySet, in order specified
# Unused now.
def just_values(query, req):
    result = query.values(*req)
    return [tuple([res[x] for x in req]) for res in result]


class Datasource(object):
    '''Pulls directly from the database.'''
    @staticmethod
    def get_preds():
        return [(p['id'], p['relation'], p['concept1'], p['concept2'])
                for p in Predicate.objects.filter(score__gt=0, visible=True)
                .values('id','relation','concept1','concept2')]

class LoadOnceDataSource(Datasource):
    '''On first load, the class pulls the Predicates from the database, then
    keeps them cached statically. If you alter the predicates in the database,
    call reload() to update the cached copy.'''

    def __init__(self):
        Datasource.__init__(self)
        if not hasattr(LoadOnceDataSource, 'loaded'):
            LoadOnceDataSource.reload()

    @classmethod
    def reload(klass):
        base = '/tmp/csamoa_'
        try:
            print 'Loading:'
            print '- Predicates ...'
            klass.preds = pickle.load(open(base+'preds'))
            print '- Forward relations...'
            klass.fwd = defaultdict(list, pickle.load(open(base+'fwd')))
            print '- Reverse relations ...'
            klass.rev = defaultdict(list, pickle.load(open(base+'rev')))
        except:
            print 'Retrieving predicates from database...'
            klass.preds = Datasource.get_preds()

            print "Splitting into forward and reverse..."
            # Dictionaries that return empty lists on looking up
            # values that are not present.
            klass.fwd, klass.rev = defaultdict(list), defaultdict(list)
            for id,pt,s1,s2 in klass.preds:
                klass.fwd[s1].append((id, pt, s2))
                klass.rev[s2].append((id, pt, s1))

            print 'Packing...'
            fwd = dict((s1, tuple(s2s)) for s1, s2s in klass.fwd.items())
            rev = dict((s2, tuple(s1s)) for s2, s1s in klass.rev.items())

            print 'Saving for future use...'
            pickle.dump(klass.preds, open(base+'preds','w'), -1)
            pickle.dump(fwd, open(base+'fwd','w'), -1)
            pickle.dump(rev, open(base+'rev','w'), -1)

        print 'done.'
        klass.loaded = True


class ConceptTools:
    '''ConceptTools: a set of tools for getting information from ConceptNet.'''

    def __init__(self, datasource = LoadOnceDataSource):
        # Instantiate the datasource
        self.datasource = datasource()
        self.preds = datasource.preds
        self.fwd = datasource.fwd
        self.rev = datasource.rev
        self.word_hash = {}
        self.word_lookup = {}
        self.global_uid = 0
        self.node_hash = {}
        self.node_lookup = {}


    def zipped2nodeuid(self,zipped):
        node_hash = self.node_hash
        uid = node_hash.get(zipped,None)
        if not uid:
                uid = self.getuid()
                node_hash[zipped] = uid
                self.node_lookup[uid] = zipped
        return uid


    def encode_node(self,textnode):
        toks = textnode.split()
        output_toks = []
        word_hash,word_lookup = self.word_hash,self.word_lookup
        whget = self.word_hash.get
        getuid = self.getuid
        for word in toks:
            word_uid = whget(word,None)
            if not word_uid:
                word_uid = getuid()
                word_hash[word] = word_uid
                word_lookup[word_uid] = word
            output_toks.append(word_uid)
        return tuple(output_toks)


    # This is a stupid port straight from the old ConceptNet.
    # It should give identical results as the old verion, quirks and all,
    # except it uses the new corpus data.

    def spreading_activation(self,
                             origin_stemids,
                             origin_weights = None,
                             max_node_visits=500,
                             max_results=200,
                             linktype_weights=None):
        """Use spreading activation to get the context of a set of concepts.

        Required parameter:
        origin_stemids -- ids of the stems to start from

        Keyword parameters:
        origin_weights -- weight in range [0.0, 1.0] for the starting stems
        max_node_visits -- maximum number of nodes to visit
        max_results -- maximum number of results to return
        linktype_weights -- tuple of two dictionaries of:
          ConceptNet relation type -> weight in range [0.0, 1.0]

        The first dictionary is "forward" relations, i.e., those for which
        the stem is on the left. The second dictionary is for "reverse"
        relations.

        If a relation type is omitted, relations of that type will be ignored.
        """

        fwd_weights, rev_weights = self.get_weights(linktype_weights)

        # Construct the blacklists of link types to completely ignore.
        fwd_blacklist = [ptype for (ptype, weight) in fwd_weights.items()
                         if weight==0.0]
        rev_blacklist = [ptype for (ptype, weight) in rev_weights.items()
                         if weight==0.0]

        if origin_weights is None:
            origin_weights = [1 for id in origin_stemids]

        # Determine if we have to consider backward flows.
        backward_flow_p = len([x for x in rev_weights.items() if x[1] > 0]) > 0

        # Init discount factors
        distance_discount = 0.5
        # FIXME: magic formula comes from...?
        def branching_discount(bf, bf_mu=2.5, bf_sigma=1.0):
            return ((1./(bf_sigma*((2*math.pi)**0.5)))
                    *(math.e**(-(math.log(bf+5,5)-bf_mu)**2/(2*bf_sigma**2))))

        # FIXME: does this ever apply?
#         utter_echo_discount = \
#             lambda utter,echo:min(1.0,math.log(utter+0.5*echo+2,3))

        # Add the initial nodes to the queue, discounted by branching
#        origin_stemids = map(lambda x:(self.zipped2nodeuid(self.encode_node(x[0].strip())),x[1]),origin_stemids)
        (origin_stemids, origin_weights) = self.get_stemids(zip(origin_stemids, origin_weights))
        queue = [(stem_id,
                  weight*branching_discount(len(self.fwd[stem_id])))
                 for (stem_id, weight) in zip(origin_stemids, origin_weights)]

        # Do breadth-first search.
        visited = []
        nodes_seen = 1
        i = 0
        while len(queue)>0 and nodes_seen<max_node_visits:
            # Pop off the queue.
            cur_stem_id,cur_score = queue[0]
            visited.append(queue[0])
            del queue[0]

            # Get forward edges (format: (id, predicate type, stem 2 id))
            fes = self.fwd[cur_stem_id]
                        
            # Remove the links whose predicate types are blacklisted.
            fes = filter(lambda x:x[1] not in fwd_blacklist,fes)

            # Append the newly-discovered forward links to the queue.
            # Updated score used to have an extra factor: ued(x[2], x[3])
            # where ued = utter_echo_discount. That was when x[2] corresponded
            # to some 'f' value and x[3] was 'inferred'.
            def get_next_id_score(x, bd=branching_discount):
                #FIXME: This evil hack shouldn't be necessary - there should be no links whose types aren't in our weights dictionary
                if not x[1] in fwd_weights:
                    fwd_weights[x[1]] = 0
                return (x[2], distance_discount  * bd(len(self.fwd[x[2]])) * fwd_weights[x[1]] * cur_score)
            forward_next_nodeidscores = map(get_next_id_score, fes)
            queue += forward_next_nodeidscores

            # If there are any inverse linkages, look backwards.
            if backward_flow_p:
                bes = self.rev[cur_stem_id]
                bes = filter(lambda x:x[1] not in backward_linktype_blacklist,bes)
                backward_next_nodeidscores = map(lambda x,
                                                 bd=branching_discount:
                                                     (x[2],
                                                      distance_discount
                                                      *bd(len(self.rev[x[2]]))
                                                      *rev_weights[x[1]]
                                                      *cur_score),
                                                 bes)
                queue += backward_next_nodeidscores

            queue.sort(lambda x,y:int((y[1]-x[1])*10000))
            queue=queue[:500]
            nodes_seen += 1

        # Search finished. Add up the scores of everything we visited.
        node_dict = {}
        #print visited
        for nodeid, score in visited:
            # Ignore origin stems (a stem is not in its own context)
            if nodeid in origin_stemids: continue

            cur_score = node_dict.get(nodeid,0.0)
            # Update the score. FIXME: why this formula?
            new_score = max(score,cur_score) \
                + (1.0 - max(score,cur_score)) * min(score,cur_score)
            node_dict[nodeid] = new_score

        # Sort the rest and output them.
        items = node_dict.items()
        items.sort(lambda x,y:int((y[1]-x[1])*100))
        output = [(Stem.objects.get(id=x[0]), x[1]) for x in items[:max_results]]
        return output


    @staticmethod
    def get_stemids(textnodes,
                    lang=Language.objects.get(id='en')):
        # Find the starting nodes in ConceptNet, if they exist.
        stemids, weights = [], []
        for text, weight in textnodes:
            # Filter.
            text = text.strip().lower()
            if text == '': continue

            # Try to get the stem.
            try:
                stem_id = Stem.get(text, lang).id
                stemids.append(stem_id)
                weights.append(weight)
            except Stem.DoesNotExist:
                # Ignore stems that don't exist in ConceptNet.
                print "Warning: ignoring stem '%s' (not in ConceptNet)" % text
        return stemids, weights


    @staticmethod
    def get_weights(linktype_weights):
        # Get the full link-weight dictionary:
        # - If none is specified, use the default.
        # - Otherwise, default unspecified weights to 0.
        if not linktype_weights:
            fwd_weights, rev_weights = ConceptTools.default_linktype_weights
        else:
            # Unpack.
            fwd_weights, rev_weights = linktype_weights

            # Set unspecified linktype weights to 0.
            all_linktypes = ConceptTools.default_linktype_weights[0].keys()
            for linktype in all_linktypes:
                fwd_weights.setdefault(linktype, 0.0)
                rev_weights.setdefault(linktype, 0.0)

        # Convert link types into PredicateTypes.
        fwd_weights = ConceptTools._lookup_predtypes(fwd_weights)
        rev_weights = ConceptTools._lookup_predtypes(rev_weights)

        return fwd_weights, rev_weights


    default_linktype_weights = ({
            'AtLocation': 0.9,
            'CapableOf': 0.8,
            'Causes': 1.0,
            'CausesDesire': 1.0,
            'ConceptuallyRelatedTo': 1.0,
            'CreatedBy': 1.0,
            'DefinedAs': 1.0,
            'Desires': 1.0,
            'HasFirstSubevent': 1.0,
            'HasLastSubevent': 1.0,
            'HasPrerequisite': 1.0,
            'HasProperty': 1.0,
            'HasSubevent': 0.9,
            'IsA': 0.9,
            'MadeOf': 0.7,
            'MotivatedByGoal': 1.0,
            'PartOf': 1.0,
            'ReceivesAction': 0.6,
            'UsedFor': 1.0
            }, {
            'AtLocation': 0.0,
            'CapableOf': 0.0,
            'Causes': 0.0,
            'CausesDesire': 0.0,
            'ConceptuallyRelatedTo': 0.0,
            'CreatedBy': 0.0,
            'DefinedAs': 0.0,
            'Desires': 0.0,
            'HasFirstSubevent': 0.0,
            'HasLastSubevent': 0.0,
            'HasPrerequisite': 0.0,
            'HasProperty': 0.0,
            'HasSubevent': 0.0,
            'IsA': 0.0,
            'MadeOf': 0.0,
            'MotivatedByGoal': 0.0,
            'PartOf': 0.0,
            'ReceivesAction': 0.0,
            'UsedFor': 0.0})

    @staticmethod
    def _lookup_predtypes(pts):
        result = {}
        for ptype, weight in pts.iteritems():
            try:
                result[PredicateType.objects.get(name=ptype).id] = weight
            except PredicateType.DoesNotExist:
                print "Warning: Bad predicate type '%s'!" % ptype
        return result


    def project_affective(self,textnode_list):

        """
        -inputs a list of concepts
        -computes the affective projection, which is
        the emotional context and consequences underlying these concepts
        -returns a rank-ordered list of concepts and their scores
        e.g.: (('concept1',score1), ('concept2,score2), ...)
      """
        linktype_weights_dict = ({
            'Desires':1.0,
            'CausesDesire':1.0,
            'MotivatedByGoal':1.0
            },
            {})
        return self.spreading_activation(textnode_list,linktype_weights=linktype_weights_dict)

    def project_spatial(self,textnode_list):

        """
        -inputs a list of concepts
        -computes the spatial projection, which consists of
        relevant locations, relevant objects in the same scene.
        -returns a rank-ordered list of concepts and their scores
        e.g.: (('concept1',score1), ('concept2,score2), ...)
      """
        linktype_weights_dict = ({
            'AtLocation':1.0,
            'ConceptuallyRelatedTo':0.5
           },
           {})

        return self.spreading_activation(textnode_list,linktype_weights=linktype_weights_dict)

    def project_details(self,textnode_list):

        """
        -inputs a list of concepts
        -computes the detail projection, which consists of
        a thing's parts, materials, properties, and instances
        and an event's subevents
        -returns a rank-ordered list of concepts and their scores
        e.g.: (('concept1',score1), ('concept2,score2), ...)
      """
        linktype_weights_dict = ({
            'HasFirstSubevent':1.0,
            'HasLastSubevent':1.0,
            'HasSubevent':1.0,
            'MadeOf':1.0,
            'PartOf':1.0,
            'HasProperty':0.9
            },
            {})
        return self.spreading_activation(textnode_list,linktype_weights=linktype_weights_dict)

    def project_consequences(self,textnode_list):

        """
        -inputs a list of concepts
        -computes the causal projection, which consists of
        possible consequences of an event or possible actions
        resulting from the presence of a thing
        -returns a rank-ordered list of concepts and their scores
        e.g.: (('concept1',score1), ('concept2,score2), ...)
      """
        linktype_weights_dict = ({
            'CausesDesire':1.0,
            'UsedFor':0.4,
            'CapableOf':0.4,
            'ReceivesAction':0.3,
            'Causes':1.0
            },
            {})
        return self.spreading_activation(textnode_list,linktype_weights=linktype_weights_dict)

    def get_all_projections(self,textnode_list):

        """
        inputs a list of concepts
        computes all available contextual projections
        and returns a list of pairs, each of the form:
             ('ProjectionName',
                (('concept1',score1), ('concept2,score2), ...)
             )
      """
        output = []
        output += [('Consequences',self.project_consequences(textnode_list))]
        output += [('Details',self.project_details(textnode_list))]
        output += [('Spatial',self.project_spatial(textnode_list))]
        output += [('Affective',self.project_affective(textnode_list))]
        return output


    def display_node(self,textnode):

        """
        returns the pretty print of a node's contents
        """
      
        decode_node,encode_node,decode_word = self.decode_node,self.encode_node,self.decode_word
        zipped2nodeuid,nodeuid2zipped = self.zipped2nodeuid, self.nodeuid2zipped
        zipped2edgeuid,edgeuid2zipped = self.zipped2edgeuid, self.edgeuid2zipped
        fw_edges,bw_edges = self.fwd,self.rev
        textnode=textnode.strip()
        encoded_node = encode_node(textnode)
        node_uid = zipped2nodeuid(encoded_node)
        fes = map(edgeuid2zipped,fw_edges.get(node_uid,[])[:1000])
        fes.sort(lambda x,y:y[2]+y[3]-x[2]-x[3])
        print fes
        bes = map(edgeuid2zipped,bw_edges.get(node_uid,[])[:1000])
        bes.sort(lambda x,y:2*(y[2]-x[2])+1*(y[3]--x[3]))
        pp_fw_edges = map(lambda x:'=='+decode_word(x[0])+'==> '+decode_node(nodeuid2zipped(x[1]))+' '+str(x[2:])+'',fes)
        pp_bw_edges = map(lambda x:'<=='+decode_word(x[0])+'== '+decode_node(nodeuid2zipped(x[1]))+' '+str(x[2:])+'',bes)
        output = '['+textnode+']'
        output+= '\n'+ '**OUT:********'
        for line in pp_fw_edges:
            output+= '\n  '+line
        output+='\n'+ '**IN:*********'
        for line in pp_bw_edges:
            output+= '\n  '+line
        return output


    def get_analogous_concepts(self,textnode,simple_results_p=0):

        """
        -inputs a node
        -uses structure-mapping to generate a list of
        analogous concepts
        -each analogous concept shares some structural features
        with the input node
        -the strength of an analogy is determined by the number
        and weights of each feature. a weighting scheme is used
        to disproportionately weight different relation types
        and also weights a structural feature by the equation:
        math.log(f+f2+0.5*(i+i2)+2,4), where f=
        i =
        - outputs a list of RESULTs rank-ordered by relevance
        - each RESULT is a triple of the form:
                     ('analogous concept', SHARED_STRUCTURES, SCORE)
        - SCORE is a scalar valuation of quality of a result
          (for now, this number does not have much external meaning)
        - SHARED_STRUCTURES is a list of triples, each of the form:
                     ('RelationType', 'target node', SCORE2)
        - SCORE2 is a scalar valuation of the strength of a
        particular shared structure
        - if simple_results_p = 1, then output object is simply
        a list of rank-ordered concepts
      """
        decode_node,encode_node,encode_word,decode_word = self.decode_node,self.encode_node,self.encode_word,self.decode_word
        zipped2nodeuid,nodeuid2zipped = self.zipped2nodeuid, self.nodeuid2zipped
        zipped2edgeuid,edgeuid2zipped = self.zipped2edgeuid, self.edgeuid2zipped
        fw_edges,bw_edges = self.fwd,self.rev
        linktype_stoplist = ['ConceptuallyRelatedTo','ThematicKLine','SuperThematicKline']
        linktype_stoplist = map(encode_word,linktype_stoplist)
        linktype_weights = {'HasProperty':3.0,
                            'UsedFor':2.0,
                            'CapableOf':2.0,
                            'ReceivesAction':1.5}
        textnode=textnode.strip()
        encoded_node = encode_node(textnode)
        node_uid = zipped2nodeuid(encoded_node)
        fes = fw_edges.get(node_uid,[])
        print fw_edges
        fes = map(edgeuid2zipped,fes)
        candidates = {}
        for fe in fes:
            commonpred,commonnode,f,i = fe
            if commonpred in linktype_stoplist:
                continue
            bes = bw_edges.get(commonnode,[])
            bes = map(edgeuid2zipped,bes)
            bes = filter(lambda x:x[0]==commonpred and x[1]!=node_uid,bes)
            for be in bes:
                commonpred2,candidate,f2,i2 = be
                link_strength = math.log(f+f2+0.5*(i+i2)+2,4)
                weight = link_strength*linktype_weights.get(decode_word(commonpred),1.0)
                candidates[candidate] = candidates.get(candidate,[])+[(commonpred,commonnode,weight)]
        scored_candidates = map(lambda x:(x[0],x[1],sum(map(lambda y:y[2],x[1]))),candidates.items())
        scored_candidates.sort(lambda x,y:int(1000*(y[2]-x[2])))
        scored_candidates = map(lambda y:(decode_node(nodeuid2zipped(y[0])),map(lambda x:(decode_word(x[0]),decode_node(nodeuid2zipped(x[1])),weight),y[1]),y[2]),scored_candidates)
        if simple_results_p:
            return map(lambda x:x[0],scored_candidates)
        return scored_candidates


    def getuid(self):
        self.global_uid += 1
        return self.global_uid


    def nodeuid2zipped(self,uid):
        return self.node_lookup.get(uid,None)


    def zipped2edgeuid(self,edge):
        edge_hash = self.edge_hash
        edge_uid = edge_hash.get(edge,None)
        if not edge_uid:
            edge_uid = self.getuid()
            edge_hash[edge]=edge_uid
            self.edge_lookup[edge_uid] = edge
        return edge_uid


    def edgeuid2zipped(self,uid):
        return self.edge_lookup.get(uid,None)


    def encode_word(self,word):
        word_hash= self.word_hash
        word_uid = word_hash.get(word,None)
        if not word_uid:
            word_uid = self.getuid()
            word_hash[word] = word_uid
            self.word_lookup[word_uid] = word
        return word_uid


    def decode_word(self,word_uid):
        return self.word_lookup.get(word_uid,None)


    def decode_node(self,node_tuple):
        wl_get = self.word_lookup.get
        return ' '.join(map(lambda word_uid:wl_get(word_uid,'UNKNOWN'),node_tuple))

class ConceptNet_compat:
    @staticmethod
    def split_textnodes_weights(textnodes):
        # Make textnodes into a dict of (text, weight). Possible inputs:
        if isinstance(textnodes, dict):
            # a dictionary.
            return textnodes.keys(), textnodes.values()
        elif isinstance(textnodes, str):
            # a single item:
            return [textnodes], [1.0]
        elif isinstance(textnodes, list) and all([isinstance(x, str) for x in textnodes]):
            # probably a list of strings:
            textnodes = dict([(x, 1.0) for x in textnodes])
            return textnodes.keys(), textnodes.values()

    # Old-style to new-style translation
    _oldnew_translation = {
        'FirstSubeventOf':'HasFirstSubevent',
        'DesirousEffectOf':'CausesDesire',
        'ThematicKLine':'ConceptuallyRelatedTo',
        'SubeventOf':'HasSubevent',
        'SuperThematicKLine':'ConceptuallyRelatedTo',
        'LastSubeventOf':'HasLastSubevent',
        'LocationOf':'AtLocation',
        'CapableOfReceivingAction':'ReceivesAction',
        'PrerequisiteEventOf':'HasPrerequisite',
        'MotivationOf':'MotivatedByGoal',
        'PropertyOf':'HasProperty',
        'EffectOf':'Causes',
        'DesireOf':'Desires'
        }

    @staticmethod
    def _old_to_new(map):
        '''Converts linktype weights dictionaries from old form to new.'''
        fwdt = ((ptype, weight) for ptype, weight in map.items()
                if not ptype.endswith('Inverse'))
        revt = ((ptype[:-len('Inverse')], weight)
                for ptype, weight in map.items() if ptype.endswith('Inverse'))

        fwds = dict((ConceptTools.oldnew_translation.get(ptype, ptype), weight)
                    for ptype, weight in fwdt)
        revs = dict((ConceptTools.oldnew_translation.get(ptype, ptype), weight)
                    for ptype, weight in revt)
        return fwds, revs



if __name__ == '__main__':
    c = ConceptTools()
    print c.get_context('couch')
