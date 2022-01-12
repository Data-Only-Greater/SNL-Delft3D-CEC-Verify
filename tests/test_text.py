# -*- coding: utf-8 -*-

from snl_d3d_cec_verify.text import Spinner


def test_spinner(mocker):
    
    from snl_d3d_cec_verify.text import sys
    
    spy_write = mocker.spy(sys.stdout, 'write')
    spin = Spinner()
    
    for _ in range(4):
        spin()
    
    expected_args = [mocker.call('-'),
                     mocker.call('\x08 \x08'),
                     mocker.call('/'),
                     mocker.call('\x08 \x08'),
                     mocker.call('|'),
                     mocker.call('\x08 \x08'),
                     mocker.call('\\'),
                     mocker.call('\x08 \x08')]
    
    assert spy_write.call_args_list == expected_args


def test_spinner_text(mocker):
    
    from snl_d3d_cec_verify.text import sys
    
    spy_write = mocker.spy(sys.stdout, 'write')
    spin = Spinner()
    
    for line in ["1.1%", "1.2%", "mock", "mock"]:
        spin(line)
    
    expected_args = [mocker.call('1.1%'),
                     mocker.call('\x08\x08\x08\x08    \x08\x08\x08\x08'),
                     mocker.call('1.2%'),
                     mocker.call('\x08\x08\x08\x08    \x08\x08\x08\x08'),
                     mocker.call('-'),
                     mocker.call('\x08 \x08'),
                     mocker.call('/'),
                     mocker.call('\x08 \x08')]
    
    assert spy_write.call_args_list == expected_args
