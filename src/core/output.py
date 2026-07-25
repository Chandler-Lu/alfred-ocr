'''Everything that leaves the process: stdout, Alfred JSON, clipboard, logs.

stdout belongs to the clipboard - Alfred copies it verbatim - so it carries the
recognized text and nothing else. Diagnostics go to stderr.
'''
# -*- coding: UTF-8 -*-
from __future__ import annotations

import json
import subprocess
import sys
from typing import Any, Dict, List, Optional

from core.config import IS_MACOS, settings
from utils import clipboard


def emit(text: str) -> None:
    '''Write the result without a trailing newline, as the workflow expects.'''
    stream = sys.stdout
    try:
        stream.write(text)
    except UnicodeEncodeError:
        # A console with a narrow code page must not lose the whole result.
        stream.write(text.encode('utf-8', 'replace').decode('utf-8', 'replace'))
    stream.flush()


def debug(message: str, *args: Any) -> None:
    if settings.debug:
        print(message % args if args else message, file=sys.stderr)


def alfred_item(title: str, subtitle: str = '', valid: bool = True,
                arg: Optional[str] = None) -> Dict[str, Any]:
    value = title if arg is None else arg
    return {
        'type': 'default',
        'title': title,
        'subtitle': subtitle,
        'valid': valid,
        'arg': value,
        'text': {'copy': value, 'largetype': value},
    }


def alfred_json(items: List[Dict[str, Any]]) -> str:
    return json.dumps({'items': items}, ensure_ascii=False)


def copy_to_clipboard(text: str) -> bool:
    return clipboard.copy_text(text)


def notify(title: str, message: str) -> bool:
    '''Best-effort desktop notification; silently skipped off macOS.'''
    if not IS_MACOS:
        return False
    script = 'display notification "%s" with title "%s"' % (
        message.replace('"', '\\"'), title.replace('"', '\\"'))
    try:
        return subprocess.run(['osascript', '-e', script],
                              stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL,
                              check=False).returncode == 0
    except OSError:
        return False
