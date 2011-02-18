from csc.conceptnet4.models import Concept
from csc.conceptnet4.analogyspace import *
import operator
import cPickle as pickle
import os

class ConceptTools(object):
    
    def __init__(self, tensor):
        self.tensor = tensor

    def get_related_concepts(self, root_concepts, root_weights=None, max_visited_nodes=100, max_results=10, 
                             link_weights_forward=None, link_weights_reverse=None, prettyprint=True):
        '''
        root_concepts: a list of concept names to start from
        root_weights: a list of weights (0.0 to 1.0) specifying how to weight the concepts we're starting from

        max_visited_nodes: will not explore more than this number of concepts
        max_results: the number of results to display
        
        link_weights_forward: a dictionary mapping Relation to weight in range (0.0, 1.0), specifying how to weight forward relations (concept on left)
        link_weights_reverse: a dictionary mapping Relation to weight in range(0,0, 1.0), specifying how to weight reverse relatiosn (concept on right)
           If either are None, uses default ConceptTools weights

        '''

        
        #Concept_weights: maps a concept to a weight, specifying how to weigh its children
        concept_weights = {}
        if root_weights:
            assert(len(root_concepts) == len(root_weights))
            for concept, weight in zip(root_concepts, root_weights):
                concept_weights[concept] = weight
        else:
            for c in root_concepts:
                concept_weights[c] = 1

        
        #Concepts: maps concepts discovered to a tuple with the original score of the assertion, the weight we've assigned it, 
        #          and the level it was discovered on
        concepts = {}
       

        #Relation weights
        forward_relation_weights = {}
        reverse_relation_weights = {}
        
        #If link_weights_forward or reverse are None, use default weights
        if not(link_weights_forward):
            link_weights_forward = self.get_default_weights_forward()
        if not(link_weights_reverse):
            link_weights_reverse = self.get_default_weights_reverse()

        #Filter out the relations whose weights are equal to 0
        for relation in link_weights_forward:
            weight = link_weights_forward[relation]
            if weight != 0:
                forward_relation_weights[relation] = weight
        for relation in link_weights_reverse:
            weight = link_weights_reverse[relation]
            if weight != 0:
                reverse_relation_weights[relation] = weight


        visited_nodes = 0
        level = 1
        concept_queue = root_concepts

        #Concepts we've already expanded
        seen = {}


        #Function for getting the 'weighted average' of two weights; used when we run into a concept we've already seen before
        #distance is the difference in levels (concepts on the same level of search have distance of 0)
        def weighted_mean(previous_weight, current_weight, distance):
            w1 = (1.0 / (2 * (distance+1)))    #If on same level, should just compute arithmetic mean
            w2 = 1.0 - w1
            return w1*current_weight + w2*previous_weight


        #This formula was used in the previous version of concept tools....
        # Init discount factors
        #distance_discount = 0.5
        # FIXME: magic formula comes from...?
       # def branching_discount(bf, bf_mu=2.5, bf_sigma=1.0):
         #   return ((1./(bf_sigma*((2*math.pi)**0.5)))
          #          *(math.e**(-(math.log(bf+5,5)-bf_mu)**2/(2*bf_sigma**2))))

        while concept_queue:
            next_level_concepts = []

            i = 0
            while i < len(concept_queue) and visited_nodes <= max_visited_nodes:
                #Gets the next concept
                c = concept_queue[i]
                
                #If we've already expanded on this concept, or this concept isn't in the tensor, continue
                if c in seen or self.tensor[c,:] == 0:
                    i += 1
                    continue

                visited_nodes += 1
                
                #Gets the slice of the tensor dealing with the concept we're looking at
                slice = self.tensor[c, :]
                
                #Iterate over all assertions made about this concept
                for a in slice.iterkeys():
                    direction, relation, concept2  = a[0]
                    score = slice[a]

                    if score <= 0:
                        continue
                    
                    #Checks to see that this is a relation we care about
                    if relation in forward_relation_weights and direction == 'right':
                        next_level_concepts.append(concept2)
                        
                        #The weight to give this concept (how 'relevant' it is)
                        #Currently takes into account the parent concept's weight, the weight given to the relation, the assertion score, and the level we're on
                        parent_weight = concept_weights[c]
                        concept2_weight = (score * (1./level)  * parent_weight)*forward_relation_weights[relation]
                        
                        if concept2 in concepts:
                            #If we've already seen this concept, get the weighted average of the previous weight and the new weight
                            _, prev_weight, prev_level = concepts[concept2]
                            print "AVERAGING"
                            print "Concept2", concept2
                            print "Prev Weight", prev_weight
                            print "Current Wight", concept2_weight
                            print "Prev Level / Current Level", prev_level, level
                            print "Regular Average", ((prev_weight + concept2_weight)/2.0)
                            concept2_weight = weighted_mean(prev_weight, concept2_weight, (level - prev_level))
                            print "Weight Given", concept2_weight
                        #print "WEIGHT GIVEN", weight
                        concepts[concept2] = (score, concept2_weight, level)
                        concept_weights[concept2] = concept2_weight 

                    elif relation in reverse_relation_weights and direction == 'left':
                        next_level_concepts.append(concept2)

                        parent_weight = concept_weights[c]
                        concept2_weight = (score * (1./level) * parent_weight)*reverse_relation_weights[relation]

                        if concept2 in concepts:
                            _, prev_weight, prev_level = concepts[concept2]
                            concept2_weight = weighted_mean(prev_weight, concept2_weight, (level - prev_level))
                        concepts[concept2] = (score, concept2_weight, level)
                        concept_weights[concept2] = concept2_weight
                    
                    
                #Mark this concept as explored  
                seen[c] = True
                i += 1

            level += 1
            concept_queue = next_level_concepts
            
        #print concepts

        #Now get the top concepts
        concept_lst = sorted(concepts.items(), key=lambda x:(x[1][1], x[0]), reverse=True)
        
        if prettyprint and concept_lst:
            print "Top Related Concepts"
            print "-----------------------------"
            print "%-20s %s, %s" % ('concept', 'score', 'weight')
            for c, (score,weight,level) in concept_lst[:max_results]:
                str = "%-20s %s, %s" % (c, score, weight)
                print str


        return concept_lst
        


    def get_default_weights_forward(self):
        forward_link_weights = {'AtLocation': 0.9, 'CapableOf': 0.8, 'Causes': 1.0, 'CausesDesire': 1.0, 'ConceptuallyRelatedTo': 1.0, 'CreatedBy': 1.0,
            'DefinedAs': 1.0, 'Desires': 1.0, 'HasFirstSubevent': 1.0, 'HasLastSubevent': 1.0, 'HasPrerequisite': 1.0, 'HasProperty': 1.0,
            'HasSubevent': 0.9, 'IsA': 0.9, 'MadeOf': 0.7, 'MotivatedByGoal': 1.0,'PartOf': 1.0, 'ReceivesAction': 0.6, 'UsedFor': 1.0}
        return forward_link_weights
    def get_default_weights_reverse(self):
        reverse_link_weights = {'AtLocation': 0.0, 'CapableOf': 0.0, 'Causes': 0.0, 'CausesDesire': 0.0, 'ConceptuallyRelatedTo': 0.0, 'CreatedBy': 0.0,
            'DefinedAs': 0.0, 'Desires': 0.0, 'HasFirstSubevent': 0.0, 'HasLastSubevent': 0.0, 'HasPrerequisite': 0.0, 'HasProperty': 0.0,
            'HasSubevent': 0.0, 'IsA': 0.0,'MadeOf': 0.0, 'MotivatedByGoal': 0.0, 'PartOf': 0.0, 'ReceivesAction': 0.0, 'UsedFor': 0.0}
        return reverse_link_weights

    
    #Some examples
    def project_affective(self, root_concepts, root_weights=None):
        '''
        Gets the emotional context and consequences underlying thes root_concepts
        '''
        relation_weights_forward = {'Desires':1.0, 'CausesDesire': 1.0, 'MotivatedByGoal':1.0}
        self.get_related_concepts(root_concepts, root_weights, link_weights_forward=relation_weights_forward, link_weights_reverse={})

    def project_spatial(self, root_concepts, root_weights=None):
        '''
        Gets relevant locations and objects in the same scene as the root concepts
        '''
        relation_weights_forward = {'AtLocation':1.0, 'ConceptuallyRelatedTo': .5}
        self.get_related_concepts(root_concepts, root_weights, link_weights_forward=relation_weights_forward, link_weights_reverse={})
    
    def project_details(self, root_concepts, root_weights=None):
        '''
        Gets a thing's parts, materials, properties, and instances and an event's subevents
        '''
        relation_weights_forward = {'HasFirstSubevent':1.0,'HasLastSubevent':1.0, 'HasSubevent':1.0, 'MadeOf':1.0, 'PartOf':1.0, 'HasProperty':0.9}
        self.get_related_concepts(root_concepts, root_weights, link_weights_forward=relation_weights_forward, link_weights_reverse={})

    def project_consequences(self, root_concepts, root_weights = None):
        '''
        Gets the 'causal projection', which is possible consequences of an event or possible actions resulting from its presence
        '''
        relation_weights_forward = {'CausesDesire':1.0, 'UsedFor':0.4, 'CapableOf':0.4, 'ReceivesAction':0.3, 'Causes':1.0}
        self.get_related_concepts(root_concepts, root_weights, link_weights_forward=relation_weights_forward, link_weights_reverse={})

    def project_utility(self, root_concepts, root_weights = None):
        '''
        Gets the 'causal projection', which is possible consequences of an event or possible actions resulting from its presence
        '''
        relation_weights_forward = {'UsedFor':1.0, 'CapableOf':1.0}
        self.get_related_concepts(root_concepts, root_weights, link_weights_forward=relation_weights_forward, link_weights_reverse={})



#Loads the concepts from the database into a tensor
#I just added this without knowing about get_pickled_cached_thing so..this should obviously be changed
class LoadTensor():
    
    def __init__(self, lang='en', path='tmp.pkl'):
        self.language = lang
        self.file_name = path

    def reload(self):
        print "Refreshing Tensor"
        tensor = conceptnet_2d_from_db(self.language)
        fl = file(self.file_name, 'wb')
        pickle.dump(tensor, fl, False)
        print "Tensor refreshed"
        fl.close()

    def load(self):
        #Checks to see if the pickle file already exists
        if (os.path.exists(self.file_name) == False):
            #If not, reloads pickle
            self.reload()

        print "Loading Tensor"
        fl = file(self.file_name, 'rb')
        tensor = pickle.load(fl)
        fl.close()
        return tensor





if __name__ == '__main__':
    #--------Some example concepts to use
    #print "Getting test concepts"
    dog = Concept.get('dog', 'en').text
    leash = Concept.get('leash', 'en').text
    umb = Concept.get('umbrella', 'en').text
    cat = Concept.get('cat', 'en').text
    #pets = [dog, cat]

    #temple = Concept.get('temple', 'en').text
   # hindu = Concept.get('hindu', 'en').text
   # asia = Concept.get('asia', 'en').text
   # nepal = Concept.get('Nepal', 'en').text
   # spain = Concept.get('Spain', 'en').text
   #test = [temple, asia, nepal]

    #----------Load Tensor
    tensor = LoadTensor().load()

    
    #Sample relation dictionary
    atlocal = Relation.get('AtLocation').name
    usedfor = Relation.get('UsedFor').name
    desires = Relation.get('Desires').name
    #isa = Relation.get('IsA')
    #partof = Relation.get('PartOf')
    relation_weights_f = {atlocal: 1, usedfor: .5, desires: 0}
    relation_weights_r = {atlocal: 1, usedfor: .2, desires: 0}
    # relation_weights_f = {'IsA': 1, 'PartOf': .5, 'Desires': 0}
    #relation_weights_r = {'IsA': 1, 'PartOf': .5}

    #print "Building ConceptTools"
    #c = ConceptTools(tensor)
    #c = ConceptTools()

    #----------Sample ConceptTools stuff
    c.get_related_concepts([dog], [1], max_levels=1, link_weights_forward=relation_weights_f, link_weights_reverse=relation_weights_r)
    #c.get_related_concepts([spain], [1], max_levels=2, link_weights_forward=relation_weights_f, link_weights_reverse=relation_weights_r)
    #related_concepts = c.get_related_concepts([temple], [1], max_levels=2)
    #print "Project Affective"
    #project_affective(dog, tensor)

    c.project_affective([dog])
    #c.project_consequences([dog])
    #c.project_details([dog])
    #c.project_spatial([dog])
    #c.project_utility([leash])
    #c.project_utility([umb])
