'''macOS clipboard helpers.

Reading an image relies on pngpaste, which ships with the Alfred workflow; the
functions degrade to False instead of raising when a tool is unavailable, since
losing the clipboard is never worth aborting a recognition for.
'''
# -*- coding: UTF-8 -*-
from __future__ import annotations

import os
import shutil
import subprocess
from typing import Optional


def copy_text(text: str) -> bool:
    '''Put ``text`` on the clipboard. True when it worked.'''
    tool = _first_available((['pbcopy'], ['clip']))
    if not tool:
        return False
    try:
        process = subprocess.Popen(tool, stdin=subprocess.PIPE)
        process.communicate(text.encode('utf-8'))
        return process.returncode == 0
    except OSError:
        return False


def paste_image(destination: str) -> Optional[str]:
    '''Write the clipboard image to ``destination``; None when there is none.'''
    pngpaste = shutil.which('pngpaste')
    if not pngpaste:
        return None
    try:
        completed = subprocess.run([pngpaste, destination],
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL,
                                   check=False)
    except OSError:
        return None
    if completed.returncode != 0 or not os.path.isfile(destination):
        return None
    return destination


def _first_available(candidates):
    for command in candidates:
        if shutil.which(command[0]):
            return command
    return None
