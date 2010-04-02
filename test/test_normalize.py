from csc.conceptnet4.models import *
def test_normalize():
    assert en.nl.normalize('they are running') == 'run'
    assert en.nl.normalize('went') == 'go'
