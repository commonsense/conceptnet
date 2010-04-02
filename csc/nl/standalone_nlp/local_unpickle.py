from pickle import Unpickler
from StringIO import StringIO

module_subst = {
    'csc.nl': 'nl',
    'csc.nl.en': 'nl',
    'csc.nl.euro': 'euro',
    'csc.nl.mblem.trie': 'trie'
}

class LocalUnpickler(Unpickler):
    def find_class(self, module, name):
        return Unpickler.find_class(self, module_subst.get(module, module), name)

def loads(str):
    file = StringIO(str)
    return LocalUnpickler(file).load()
