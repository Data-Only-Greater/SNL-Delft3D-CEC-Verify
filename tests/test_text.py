# -*- coding: utf-8 -*-

# Copyright (c) Django Software Foundation and individual contributors.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#     1. Redistributions of source code must retain the above copyright notice,
#        this list of conditions and the following disclaimer.
#
#     2. Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#
#     3. Neither the name of Django nor the names of its contributors may be used
#        to endorse or promote products derived from this software without
#        specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from snl_d3d_cec_verify.text import slugify


def test_slugify():
    test = slugify(' Jack & Jill like numbers 1,2,3 and 4 and silly '
                   'characters ?%.$!/')
    assert test == 'jack-jill-like-numbers-123-and-4-and-silly-characters'


def test_slugify_unicode():
    test = slugify("Un \xe9l\xe9phant \xe0 l'or\xe9e du bois")
    assert test == 'un-elephant-a-loree-du-bois'


def test_slugify_unicode_allow():
    test = slugify("Un \xe9l\xe9phant \xe0 l'or\xe9e du bois",
                   allow_unicode=True)
    assert test == 'un-\xe9l\xe9phant-\xe0-lor\xe9e-du-bois'


def test_slugify_non_string_input():
    assert slugify(123) == '123'
