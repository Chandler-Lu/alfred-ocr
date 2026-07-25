'''Result formatting: punctuation, CJK/Latin spacing, paragraph merging.

Two independent passes, both driven by the *local* script context rather than
by a verdict about the whole line:

    normalize_punctuation()  ASCII <-> full-width, decided per character
    add_cjk_latin_space()    one space on every CJK <-> Latin boundary

URLs, e-mail addresses and grouped numbers are masked out beforehand, so
``https://a.com/b`` and ``1,000.50`` come through untouched.

render_lines() is the entry point providers use: it merges the recognized lines
into paragraphs (core/layout.py) and only then formats them, so a boundary
between a Chinese line and an English one is visible to the spacing rules.
'''
# -*- coding: UTF-8 -*-
from __future__ import annotations

import re
from typing import Iterable, List, Optional, Tuple

from core import layout
from core.config import settings
from core.layout import LayoutOptions, TextLine
from utils.punctuation import (ASCII_TO_FULLWIDTH, CJK, CJK_PUNCTUATION,
                               DASH_FIXES, FULLWIDTH_TO_ASCII,
                               fold_fullwidth_ascii, is_cjk, is_cjk_like_char)

_SENTINEL = '\x00'

# Content that must never be reshaped internally. A URL stops at whitespace and
# at any CJK character, otherwise it would swallow the rest of the sentence.
_URL_STOP = r'\s\u3000' + CJK + CJK_PUNCTUATION
_PROTECTED_RE = re.compile(
    '(?:'
    r'(?:[A-Za-z][A-Za-z0-9+.\-]*://|www\.|mailto:)[^' + _URL_STOP + ']+'
    r'|[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}'
    r'|\d+(?:[.,]\d+)+'
    r'|\d+:\d+(?::\d+)?'
    ')'
)
# Sentence punctuation at the end of a protected token belongs to the sentence.
_TOKEN_TRAILING = '.,;:!?)]}\'"'
_MASK_RE = re.compile(_SENTINEL + r'(\d+)' + _SENTINEL)

# Characters that take a space when a CJK character precedes them. The sentinel
# stands in for masked Latin content such as a URL.
_AFTER_CJK = r'A-Za-z0-9$@#\(\[\{' + _SENTINEL
# Characters that take a space when a CJK character follows them. Includes the
# trailing symbols of technical names: C++代码, C#代码, 100%的人.
_BEFORE_CJK = r'A-Za-z0-9%+#*&$\)\]\}' + _SENTINEL

_SPACE_AFTER_CJK_RE = re.compile('([' + CJK + '])([' + _AFTER_CJK + '])')
_SPACE_BEFORE_CJK_RE = re.compile('([' + _BEFORE_CJK + '])([' + CJK + '])')

_ASCII_PAREN_RE = re.compile(r'\(([^()]{0,120})\)')
_FULLWIDTH_PAREN_RE = re.compile(r'（([^（）]{0,120})）')

_SPACE_RUN_RE = re.compile(r'[ \t\u00a0\u3000]{2,}')
_SPACE_BEFORE_CJK_PUNCT_RE = re.compile(r'[ \t]+([' + CJK_PUNCTUATION + '])')
_SPACE_AFTER_OPENING_RE = re.compile(r'([（《「『【〔])[ \t]+')
_SPACE_AFTER_CJK_PUNCT_RE = re.compile(r'([，。！？；：、》」』】〕）])[ \t]+')
_TRAILING_SPACE_RE = re.compile(r'[ \t]+$', re.MULTILINE)


def _mask_protected(text: str) -> Tuple[str, List[str]]:
    tokens: List[str] = []

    def replace(match: 're.Match[str]') -> str:
        token = match.group(0)
        trailing = ''
        while len(token) > 1 and token[-1] in _TOKEN_TRAILING:
            trailing = token[-1] + trailing
            token = token[:-1]
        tokens.append(token)
        return _SENTINEL + str(len(tokens) - 1) + _SENTINEL + trailing

    return _PROTECTED_RE.sub(replace, text.replace(_SENTINEL, '')), tokens


def _unmask_protected(text: str, tokens: List[str]) -> str:
    if not tokens:
        return text

    def replace(match: 're.Match[str]') -> str:
        index = int(match.group(1))
        return tokens[index] if index < len(tokens) else match.group(0)

    return _MASK_RE.sub(replace, text)


def _neighbour(text: str, index: int, step: int) -> str:
    '''Nearest meaningful character in direction ``step``, or ''.

    Spaces and masked tokens are stepped over: a URL between a Chinese word and
    its punctuation must not hide the fact that the sentence is Chinese,
    otherwise 见 https://example.com。 loses its 。
    '''
    position = index + step
    sentinels = 0
    while 0 <= position < len(text):
        char = text[position]
        if char == _SENTINEL:
            sentinels += 1
        elif sentinels % 2 == 1:
            pass  # inside a placeholder
        elif char not in ' \t\u00a0\u3000':
            return char
        position += step
    return ''


def _normalize_parentheses(text: str) -> str:
    def to_fullwidth(match: 're.Match[str]') -> str:
        inner = match.group(1)
        return '（' + inner + '）' if is_cjk(inner) else match.group(0)

    def to_ascii(match: 're.Match[str]') -> str:
        inner = match.group(1)
        if is_cjk(inner):
            return match.group(0)
        start, end = match.span()
        if is_cjk_like_char(_neighbour(text, start, -1)) or \
                is_cjk_like_char(_neighbour(text, end - 1, 1)):
            return match.group(0)
        return '(' + inner + ')'

    text = _ASCII_PAREN_RE.sub(to_fullwidth, text)
    return _FULLWIDTH_PAREN_RE.sub(to_ascii, text)


def normalize_punctuation(text: str) -> str:
    '''Give every punctuation mark the width its neighbours ask for.

    ASCII becomes full-width next to CJK; full-width becomes ASCII when both
    neighbours are Latin. Anything ambiguous is left alone, which is why
    ``f(x)`` and ``1,000`` survive inside a Chinese sentence.
    '''
    for wrong, right in DASH_FIXES:
        text = text.replace(wrong, right)
    text = _normalize_parentheses(text)

    out = list(text)
    for index, char in enumerate(text):
        fullwidth = ASCII_TO_FULLWIDTH.get(char)
        if fullwidth is not None:
            if is_cjk_like_char(_neighbour(text, index, -1)) or \
                    is_cjk_like_char(_neighbour(text, index, 1)):
                out[index] = fullwidth
            continue
        ascii_form = FULLWIDTH_TO_ASCII.get(char)
        if ascii_form is not None and char not in '（）':
            if not is_cjk_like_char(_neighbour(text, index, -1)) and \
                    not is_cjk_like_char(_neighbour(text, index, 1)):
                out[index] = ascii_form
    return ''.join(out)


def add_cjk_latin_space(text: str) -> str:
    '''One space between CJK and Latin, idempotently.'''
    text = _SPACE_AFTER_CJK_RE.sub(r'\1 \2', text)
    return _SPACE_BEFORE_CJK_RE.sub(r'\1 \2', text)


def tidy_whitespace(text: str) -> str:
    text = _SPACE_RUN_RE.sub(' ', text)
    text = _SPACE_BEFORE_CJK_PUNCT_RE.sub(r'\1', text)
    text = _SPACE_AFTER_OPENING_RE.sub(r'\1', text)
    text = _SPACE_AFTER_CJK_PUNCT_RE.sub(r'\1', text)
    return _TRAILING_SPACE_RE.sub('', text)


def format_text(text: str,
                add_space: Optional[bool] = None,
                normalize: Optional[bool] = None,
                fold_fullwidth: Optional[bool] = None) -> str:
    '''Full clean-up pipeline. Newlines are preserved.'''
    if not text:
        return ''
    if add_space is None:
        add_space = settings.bool('text_add_cjk_latin_space')
    if normalize is None:
        normalize = settings.bool('text_normalize_punctuation')
    if fold_fullwidth is None:
        fold_fullwidth = settings.bool('text_fold_fullwidth_ascii')

    masked, tokens = _mask_protected(text)
    if fold_fullwidth:
        masked = fold_fullwidth_ascii(masked)
    if normalize:
        masked = normalize_punctuation(masked)
    if add_space:
        masked = add_cjk_latin_space(masked)
    return _unmask_protected(tidy_whitespace(masked), tokens)


def render_lines(lines: Iterable[TextLine],
                 options: Optional[LayoutOptions] = None,
                 paragraphs: Optional[bool] = None) -> str:
    '''Merge lines into paragraphs, then format each of them.

    Formatting runs after the merge on purpose: only then is the boundary
    between a Chinese line and an English one visible to the spacing rules.
    '''
    lines = list(lines)
    if paragraphs is None:
        paragraphs = settings.bool('paragraph_enabled')
    if paragraphs:
        blocks = layout.group(lines, options)
    else:
        blocks = [line.text.strip() for line in lines if line.text.strip()]
    return '\n'.join(format_text(block) for block in blocks if block)
