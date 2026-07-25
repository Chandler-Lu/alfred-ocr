'''Character tables and script predicates.

Pure data plus the few one-line tests built on it. core/formatter.py owns the
rules that use these; keeping the tables separate makes them easy to audit and
to extend for another script.
'''
# -*- coding: UTF-8 -*-
from __future__ import annotations

import re

# Ideographs, kana and friends. Deliberately excludes CJK punctuation, which
# must not receive a space: 中文，Python - not 中文， Python.
CJK = (
    '\u2e80-\u2eff'          # CJK Radicals Supplement
    '\u3005\u3007'           # 々 〇
    '\u3040-\u30ff'          # Hiragana, Katakana
    '\u3100-\u312f'          # Bopomofo
    '\u31a0-\u31bf'          # Bopomofo Extended
    '\u3400-\u4dbf'          # Unified Ideographs Extension A
    '\u4e00-\u9fff'          # Unified Ideographs
    '\ua000-\ua4cf'          # Yi
    '\uac00-\ud7af'          # Hangul syllables
    '\uf900-\ufaff'          # Compatibility Ideographs
    '\U00020000-\U0002ffff'  # Extensions B-G
)

CJK_PUNCTUATION = '，。！？；：、·…—～《》〈〉「」『』【】〔〕（）“”‘’'

# Punctuation that closes a sentence, and punctuation that promises more text.
SENTENCE_FINAL = '。．.!！?？;；…'
CONTINUING = '，,、;；:：/\\|~-\u2013\u2014“"\'(（《「『【'

# ASCII marks that become full-width next to CJK.
ASCII_TO_FULLWIDTH = {
    ',': '，',
    ';': '；',
    ':': '：',
    '!': '！',
    '?': '？',
}

# Full-width marks that become ASCII when both neighbours are Latin.
FULLWIDTH_TO_ASCII = {
    '，': ',',
    '。': '.',
    '；': ';',
    '：': ':',
    '！': '!',
    '？': '?',
    '（': '(',
    '）': ')',
}

# Baidu regularly reads an em dash as "—一" or "一—".
DASH_FIXES = (('—一', '——'), ('一—', '——'))

FULLWIDTH_ASCII_OFFSET = 0xfee0

_CJK_RE = re.compile('[' + CJK + ']')
_LATIN_LETTER_RE = re.compile('[A-Za-z]')


def is_cjk(text: str) -> bool:
    '''True when ``text`` contains at least one CJK character.'''
    return bool(_CJK_RE.search(text))


def is_cjk_char(char: str) -> bool:
    return bool(char) and bool(_CJK_RE.match(char[0]))


def is_cjk_like_char(char: str) -> bool:
    '''CJK characters plus CJK punctuation: anything that needs no space.'''
    return bool(char) and (is_cjk_char(char) or char[0] in CJK_PUNCTUATION)


def latin_ratio(text: str) -> float:
    '''Share of Latin letters among the letter-ish characters of ``text``.'''
    latin = len(_LATIN_LETTER_RE.findall(text))
    cjk = len(_CJK_RE.findall(text))
    total = latin + cjk
    return latin / total if total else 0.0


def fold_fullwidth_ascii(text: str) -> str:
    '''Ａ１ -> A1, leaving full-width punctuation alone.'''
    out = []
    for char in text:
        code = ord(char)
        if 0xff01 <= code <= 0xff5e and \
                chr(code - FULLWIDTH_ASCII_OFFSET).isalnum():
            out.append(chr(code - FULLWIDTH_ASCII_OFFSET))
        elif char == '\u3000':
            out.append(' ')
        else:
            out.append(char)
    return ''.join(out)
