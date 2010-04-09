"""
Tools for working with ConceptNet as a generalized semantic network.

Requires the NetworkX library.
"""
import networkx as nx
import codecs
from csc.conceptnet.models import Assertion

def make_network(lang):
    """
    Get the ConceptNet network for a particular language. It takes one
    parameter, which is `lang`, the language ID as a string.
    """
    assertions = Assertion.useful.filter(language__id=lang)
    graph = nx.MultiDiGraph()
    for text1, text2, rel, score, freq in assertions.values_list(
        'concept1__text', 'concept2__text', 'relation__name', 'score',
        'frequency__value').iterator():
        if text1 and text2:
            graph.add_edge(text1, text2, rel=rel, score=score, freq=freq)
    return graph

def export_gml(lang, filename):
    f = codecs.open(filename, 'w', encoding='utf-7')
    graph = make_network(lang)
    nx.write_gml(graph, f)
    f.close()

def export_edgelist(lang, filename):
    f = codecs.open(filename, 'w', encoding='utf-8')
    graph = make_network(lang)
    nx.write_edgelist(graph, f, data=True, delimiter='\t')
    f.close()

