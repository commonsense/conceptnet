from csc.util import run_doctests
import csc.nl.euro

def test_nl():
    run_doctests(csc.nl.euro)

def check_correct_db():
    # Make sure we're testing on SQLite when we're feeling paranoid
    from django.conf import settings
    assert settings.DATABASE_NAME.endswith('ConceptNet.db')
