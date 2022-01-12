# -*- coding: utf-8 -*-

import re
import sys
import itertools
from typing import Optional


class Spinner():
    """A context manager which provides an ASCII spinner on stdout
    
    Running the spinner without input:
    
    >>> with Spinner() as spin:
    ...     for _ in range(4):
    ...         spin()
    -\b \b/\b \b|\b \b\\\b \b
    
    If text passed to the spinner contains a percentage sign, the spinner
    will display the percentage value:
    
    >>> with Spinner() as spin:
    ...     for line in ["1.1%", "1.2%"]:
    ...         spin(line)
    1.1%\b\b\b\b    \b\b\b\b1.2%\b\b\b\b    \b\b\b\b
    
    .. automethod:: __call__
    
    """
    
    def __init__(self):
        self.spinner = itertools.cycle(['-', '/', '|', '\\'])
        self._last: Optional[str] = None
    
    def __enter__(self):
        return self
    
    def __call__(self, text: Optional[str] = None):
        """Increment the spinner and write to stdout
        
        :param text: text to parse for percentage sign
        
        """
        
        if self._last is not None:
            n_back = len(self._last)
            sys.stdout.write('\b' * n_back + ' ' * n_back + '\b' * n_back)
        
        out = None
        
        if text is not None:
            percentage = re.search(r'(\d+(?:\.\d+)?)(?=%)', text)
            if percentage is not None:
                out = percentage.group() + "%"
        
        if out is None: out = next(self.spinner)
        
        sys.stdout.write(out)
        sys.stdout.flush()
        
        self._last = out
    
    def __exit__(self, *args, **kwargs):
        
        if self._last is None: return
        
        n_back = len(self._last)
        sys.stdout.write('\b' * n_back + ' ' * n_back + '\b' * n_back)
        sys.stdout.flush()
        
        self._last = None

