#!/usr/bin/env python3
'''Deprecated entry point, kept so already-installed workflows keep working.

``ocr.py <selector> <image>`` now forwards to main.py, which accepts the same
arguments. Point new actions at main.py.
'''
# -*- coding: UTF-8 -*-
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import main  # noqa: E402

if __name__ == '__main__':
    sys.exit(main())
