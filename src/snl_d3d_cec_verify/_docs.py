# -*- coding: utf-8 -*-

from inspect import signature


def docstringtemplate(func):
    """Treat the docstring as a template, with access to defaults"""
    
    try:
        f = func
        spec = signature(f)
    except TypeError:
        f = func.__func__
        spec = signature(f)
    
    defaults = {key: f"``{repr(param.default)}``"
                    if not param.default == param.empty
                        else None
                            for key, param in spec.parameters.items()}
    
    f.__doc__ = f.__doc__ and f.__doc__.format(**defaults)
    
    return func
