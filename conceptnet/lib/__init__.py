# Add this directory to the Python path.
import sys, os.path
_path = os.path.dirname(__file__)
joinpath = os.path.join
sys.path.insert(0, _path)

__test__ = False
