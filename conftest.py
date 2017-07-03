#!/usr/bin/env python3

import os.path
import pytest

def pytest_configure(config):
    source_root = os.path.dirname(os.path.abspath(__file__))
    if os.getcwd() != source_root:
        os.chdir(source_root)