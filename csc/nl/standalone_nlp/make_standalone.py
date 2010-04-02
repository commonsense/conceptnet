from __future__ import with_statement
__import__('os').environ.setdefault('DJANGO_SETTINGS_MODULE', 'csc.django_settings')
from csc.nl import get_nl
import cPickle as pickle
import local_unpickle

def make_standalone(lcode):
    nl = get_nl(lcode)
    with open('lang_%s.py' % lcode, 'w') as out_py:
        out_py.write('import sys, os\n')
        out_py.write('import cPickle as pickle\n')
        out_py.write('sys.path.insert(0, os.path.dirname(__file__))\n')
        
        # Pre-load objects
        nl.stopwords
        nl.lemmatizer
        nl.unlemmatizer
        nl.swapdict
        nl.autocorrect
        nl.blacklist
        nl.frequencies

        fake_picklestr = pickle.dumps(nl)
        fake_obj = local_unpickle.loads(fake_picklestr)
        picklestr = pickle.dumps(fake_obj)

        out_py.write('picklestr = """%s"""\n' % (picklestr))
        out_py.write('%s_nl = nltools = pickle.loads(picklestr)\n' % (lcode))

if __name__ == '__main__':
    make_standalone('en')
    make_standalone('zh')
