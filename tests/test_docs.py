# -*- coding: utf-8 -*-

import sys

import pytest

from snl_d3d_cec_verify._docs import docstringtemplate


class Mock():
    
    def instance_method(self, default=1):
        """Mock instance method
        
        :param default: mock, defaults to {default}
        
        """
    
    @classmethod
    def class_method(cls, default=2):
        """Mock classmethod
        
        :param default: mock, defaults to {default}
        
        """
    
    @staticmethod
    def static_method(default=3):
        """Mock staticmethod
        
        :param default: mock, defaults to {default}
        
        """


def test_docstringtemplate():
    f = docstringtemplate(Mock.__dict__['instance_method'])
    assert "defaults to ``1``" in f.__doc__


def test_docstringtemplate_classmethod():
    f = docstringtemplate(Mock.__dict__['class_method'])
    assert "defaults to ``2``" in f.__func__.__doc__


def is_python_version(major, minor):
    if major != sys.version_info.major: return False
    if minor != sys.version_info.minor: return False
    return True


@pytest.mark.skipif(not is_python_version(3, 9),
                    reason="Requires Python == 3.9")
def test_docstringtemplate_staticmethod_py39():
    f = docstringtemplate(Mock.__dict__['static_method'])
    assert "defaults to ``3``" in f.__func__.__doc__


@pytest.mark.skipif(is_python_version(3, 9),
                    reason="Requires Python >= 3.10")
def test_docstringtemplate_staticmethod_py310():
    f = docstringtemplate(Mock.__dict__['static_method'])
    assert "defaults to ``3``" in f.__doc__
