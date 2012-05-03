# everything starting with _ gets exported to grader & user spaces

from random import randint as _rint
from copy import deepcopy as _deepcopy
from random import choice as _choice
from random import sample as _sample
from random import choice as _uar
from io import StringIO as _StringIO
import string as __string
import sys as _sys
_chars = __string.digits+__string.ascii_letters+' !@#$%^&*()'

class _TeeOut():
    def __init__(self, out1, out2):
        self.out1 = out1
        self.out2 = out2
    def write(self, data):
        self.out1.write(data)
        self.out2.write(data)
    def flush(self):
        self.out1.flush()
        self.out2.flush()

def _realClose(expected, query):
    return (abs(expected - query)<1e-4*max(1, abs(expected)))

def _sfloat(S):
    try: return float(S)
    except ValueError: return None        

__all__ = [__i__ for __i__ in globals() if __i__[0:2] != '__']

