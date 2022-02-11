# -*- coding: utf-8 -*-

# Copyright (c) 2019, Guus Rongen

def check_argument(argument, name, types):
    
    if not isinstance(argument, types):
        raise TypeError(f'Expected argument type {types} for variable {name}, '
                        f'got {type(argument)}.')
