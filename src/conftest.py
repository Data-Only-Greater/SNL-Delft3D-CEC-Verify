# -*- coding: utf-8 -*-

from pathlib import Path

import pytest # type: ignore


@pytest.fixture
def data_dir():
    this_file = Path(__file__).resolve()
    return (this_file.parent / ".." / "test_data").resolve()
