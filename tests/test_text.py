# -*- coding: utf-8 -*-

from snl_d3d_cec_verify.text import Spinner


def test_spinner(mocker):
    
    from snl_d3d_cec_verify.text import sys
    
    spy_write = mocker.spy(sys.stdout, 'write')
    spin = Spinner()
    
    for _ in range(4):
        spin()
    
    expected_args = [mocker.call('-'),
                     mocker.call('\x08'),
                     mocker.call('/'),
                     mocker.call('\x08'),
                     mocker.call('|'),
                     mocker.call('\x08'),
                     mocker.call('\\'),
                     mocker.call('\x08')]
    
    assert spy_write.call_args_list == expected_args
