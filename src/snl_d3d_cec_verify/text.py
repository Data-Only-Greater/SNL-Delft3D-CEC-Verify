# -*- coding: utf-8 -*-

import sys
import itertools


class Spinner():
    """A simple ASCII spinner which outputs to stdout
    
    >>> spin = Spinner()
    >>> for _ in range(4):
    ...     spin()
    -\b/\b|\b\\\b
    
    """
    
    def __init__(self):
        self.spinner = itertools.cycle(['-', '/', '|', '\\'])
    
    def __call__(self):
        sys.stdout.write(next(self.spinner))
        sys.stdout.flush()
        sys.stdout.write('\b')
