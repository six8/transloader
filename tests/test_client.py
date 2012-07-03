from transloader import TransloadIt
import os

TRANSLOADIT_KEY = os.getenv('TRANSLOADIT_KEY')
TRANSLOADIT_SECRET = os.getenv('TRANSLOADIT_SECRET')

def test_list():
    transloadit = TransloadIt(TRANSLOADIT_KEY, TRANSLOADIT_SECRET)
    for a in transloadit.assemblies():
        print a.info
    assert False