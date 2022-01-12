# -*- coding: utf-8 -*-

import re
import sys
import itertools
from typing import Optional


class Spinner():
    """An ASCII spinner which writes to stdout
    
    Running the spinner without input:
    
    >>> spin = Spinner()
    >>> for _ in range(4):
    ...     spin()
    -\b \b/\b \b|\b \b\\\b \b
    
    If text passed to the spinner contains a percentage sign, the spinner
    will display the percentage value:
    
    >>> for line in ["1.1%", "1.2%"]:
    ...     spin(line)
    1.1%\b\b\b\b    \b\b\b\b1.2%\b\b\b\b    \b\b\b\b
    
    .. automethod:: __call__
    
    """
    
    def __init__(self):
        self.spinner = itertools.cycle(['-', '/', '|', '\\'])
    
    def __call__(self, text: Optional[str] = None):
        """Increment the spinner and write to stdout
        
        :param text: text to parse for percentage sign
        
        """
        
        out = None
        
        if text is not None:
            percentage = re.search(r'\d+\.\d+(?=%)', text)
            if percentage is not None:
                out = percentage.group() + "%"
        
        if out is None: out = next(self.spinner)
        
        sys.stdout.write(out)
        sys.stdout.flush()
        sys.stdout.write('\b' * len(out) + ' ' * len(out) + '\b' * len(out))
