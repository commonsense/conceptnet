#python-encoding: UTF-8

from csc.nl.ja.util       import *
from csc.nl.ja.properties import *

class JaTreeNode():
    ''' Things common to tree nodes '''

    def __init__(self):
        self.parent = None

    def __str__(self):
        return self.surface

    def bredth_first(self, return_filter = None, access_filter = None):
        return JaTreeBreadthFirstSearch(self, return_filter)

    def depth_first(self, return_filter = None, access_filter = None):
        return JaTreeDepthFirstSearch(self, return_filter, access_filter)

    @property
    def top(self):
        node = self
        while node.parent:
            node = node.parent
        return node

    @lazy_property
    def node_type(self):
        return self.__class__.__name__

    @lazy_property
    def is_branch(self):
        return isinstance(self, JaTreeBranch)

    @lazy_property
    def is_leaf(self):
        return isinstance(self, JaTreeLeaf)

    def find_child(self, node):
        return None

class JaTreeBranch(JaTreeNode):
    ''' A branch node with children '''

    def __init__(self):
        JaTreeNode.__init__(self)
        self.children  = []

    def find_child(self, node):
        ''' Returns the index (or indexes as an array) of the provided node.
        This works on identity, not equality
        '''

        results = filter(lambda v: v[1] is node, [ (i, x) for i, x in enumerate(self.children) ])

        length = len(results)
        if length == 0: return None
        if length == 1: return results[0][0]
        else:           return [ x[0] for x in results ]

class JaTreeLeaf(JaTreeNode):
    ''' A leaf node with no children '''

    def __init__(self):
        JaTreeNode.__init__(self)

class JaLanguageNode(JaProperties):
    ''' Things common to language-based tree nodes '''

    def __init__(self):
        pass

    def dump(self, color = True):
        print('\n'.join(self.dump_lines(0, color)) + '\n')

    @lazy_property
    def surface(self):
        return str().join( [ x.surface for x in self.children ] )

    @property
    def chunks(self):
        return [ n for n in self.depth_first(lambda x: x.is_chunk) ]

    @property
    def tokens(self):
        return_filter = lambda x: x.is_token
        return [ n for n in self.depth_first(return_filter = return_filter) ]

    @property
    def words(self):
        this = self

        # Does not proceed into sub-words unless called originally on a word itself #
        access_filter = lambda x: not x.parent or x.parent == this or not x.parent.is_word
        return_filter = lambda x: x.is_word

        return [ n for n in self.depth_first(return_filter = return_filter, access_filter = access_filter) ]

class JaTreeSearch():
    def __init__(self, inst, return_filter = None, access_filter = None):
        self.inst          = inst
        self.return_filter = return_filter or (lambda x: True)
        self.access_filter = access_filter or (lambda x: True)
        self.reset()

    def __iter__(self):
        return self

class JaTreeDepthFirstSearch(JaTreeSearch):
    ''' Iterator class for doing depth first searches on a JaTreeNode based tree '''

    def __init__(self, inst, return_filter = None, access_filter = None):
        JaTreeSearch.__init__(self, inst, return_filter, access_filter)

    def reset(self, node = None):
        ''' Returns the search to its initial state so you can re-run it '''
        self.stack = [ {'node': self.inst, 'index': None} ]

    # Step back up and do the node again next iteration #
    def redo(self):
        ''' Rewind so we can look at the last node again. '''

        if len(self.stack) == 1:
            self.reset()
        else:
            self.stack.pop(-1)
            self.stack[-1]['index'] -= 1

    # Reasionably stable recursion #
    def next(self):
        ''' Return the next node '''

        while ( True ):
            if len(self.stack) == 0:
                self.reset()
                raise StopIteration

            node  = self.stack[-1]['node']
            index = self.stack[-1]['index']

            # First visit to the node #
            if index == None:
                # Make sure we can access this node first #
                if not self.access_filter(node):
                    # Don't go here #
                    self.stack.pop(-1)
                    continue

                if not self.return_filter(node):
                    # It's okay, just don't return it #
                    self.stack[-1]['index'] = 0
                    continue

                # It's a node we want to see #
                self.stack[-1]['index'] = 0
                return self.stack[-1]['node']

            # Go into the children if possible #
            if node.is_branch and index < len(node.children):
                self.stack.append( \
                {
                    'node':  node.children[index],
                    'index': None
                })

                self.stack[-2]['index'] = index + 1
                continue

            self.stack.pop(-1)

class JaTreeBreadthFirstSearch(JaTreeSearch):
    ''' Iterator class for doing bredth first searches on a JaTreeNode based tree '''

    def __init__(self, inst, return_filter = None, access_filter = None):
        JaTreeSearch.__init__(self, inst, return_filter, access_filter)

    def reset(self, node = None):
        ''' Returns the search to its initial state so you can re-run it '''
        self.stack = [ {'node': self.inst, 'index': None} ]

    # Step back up and do the node again next iteration #
    def redo(self):
        ''' Rewind so we can look at the last node again. '''
        raise NotImplementedError("Sorry, redo is not implemented on JaTreeBreadthFirstSearch yet...")

    # Reasionably stable recursion #
    def next(self):
        ''' Return the next node '''

        while ( True ):
            if len(self.stack) == 0:
                self.reset()
                raise StopIteration

            node  = self.stack[0]['node']
            index = self.stack[0]['index']

            # First visit to the node #
            if index == None:
                # Make sure we can access this node first #
                if not self.access_filter(node):
                    # Don't go here #
                    self.stack.pop(0)
                    continue

                if not self.return_filter(node):
                    # It's okay, just don't return it #
                    self.stack[0]['index'] = 0
                    continue

                # It's a node we want to see #
                self.stack[0]['index'] = 0
                return self.stack[0]['node']

            # Go into the children if possible #
            if node.is_branch and index < len(node.children):
                self.stack.append( \
                {
                    'node':  node.children[index],
                    'index': None
                })

                self.stack[0]['index'] = index + 1
                continue

            self.stack.pop(0)

