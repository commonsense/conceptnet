import sys
sys.path.insert(0, '..')
import settings

from util import queryset_foreach
from corpus.models import DependencyParse

def generalize_dep(dep):
    if dep.linktype.startswith('prep_') or dep.linktype.startswith('prepc_'):
        newlt = 'prep'
    elif dep.linktype.startswith('conj_'):
        newlt = 'conj'
    else: return

    newdep = DependencyParse(sentence_id=dep.sentence_id,
                             linktype=newlt,
                             word1=dep.word1,
                             word2=dep.word2,
                             index1=dep.index1,
                             index2=dep.index2)
    newdep.save()

def progress_callback(num, den):
    print num, '/', den

queryset_foreach(DependencyParse.objects.all(), generalize_dep)

