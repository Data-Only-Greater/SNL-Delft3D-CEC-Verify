# -*- coding: utf-8 -*-

from inspect import signature


def docstringtemplate(f):
    """Treat the docstring as a template, with access to globals and
    defaults"""
    spec = signature(f)
    defaults = {key: param.default if not param.default == param.empty
                        else None for key, param in spec.parameters.items()}
    f.__doc__ = f.__doc__ and f.__doc__.format(**defaults)
    return f

