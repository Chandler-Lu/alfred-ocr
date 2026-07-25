'''The contract every provider implements.

A provider turns an input into an OcrResult and nothing else: no printing, no
sys.exit, no clean-up of temporary files. main.py renders the result, reports
errors and removes the screenshot, so all nine engines behave identically.

Adding an engine means subclassing BaseProvider and listing it in router.py.
'''
# -*- coding: UTF-8 -*-
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, ClassVar, List, Optional, Tuple

from core import formatter
from core.config import Settings
from core.config import settings as default_settings
from core.exceptions import EmptyResultError
from core.image_loader import ImageFile
from core.layout import TextLine

# What a provider expects to be handed by main.py.
INPUT_IMAGE = 'image'
INPUT_DIRECTORY = 'directory'
INPUT_TEXT = 'text'
INPUT_NONE = 'none'


@dataclass
class OcrResult:
    '''Recognized content, still unformatted.

    Providers that know the geometry return ``lines`` and get paragraph
    merging; providers that only get a blob of text return ``text``; content
    that must not be touched at all (LaTeX, TSV, QR payloads) uses ``raw``.
    '''

    lines: List[TextLine] = field(default_factory=list)
    text: Optional[str] = None
    formatted: bool = False
    paragraphs: Optional[bool] = None

    @classmethod
    def from_lines(cls, lines: List[TextLine]) -> 'OcrResult':
        return cls(lines=list(lines))

    @classmethod
    def from_text(cls, text: str) -> 'OcrResult':
        return cls(text=text)

    @classmethod
    def raw(cls, text: str) -> 'OcrResult':
        '''Content to emit verbatim.'''
        return cls(text=text, formatted=True)

    def render(self) -> str:
        if self.lines:
            return formatter.render_lines(self.lines, paragraphs=self.paragraphs)
        text = self.text or ''
        return text if self.formatted else formatter.format_text(text)

    def is_empty(self) -> bool:
        if self.lines:
            return not any(line.text.strip() for line in self.lines)
        return not (self.text or '').strip()

    def or_raise(self, message: str = 'Empty!') -> 'OcrResult':
        if self.is_empty():
            raise EmptyResultError(message)
        return self


class BaseProvider(abc.ABC):
    '''Base class for every OCR / translation engine.'''

    name: ClassVar[str] = ''
    aliases: ClassVar[Tuple[str, ...]] = ()
    # Numeric selector used by the shipped Alfred and Quicker actions.
    selector: ClassVar[Optional[int]] = None
    summary: ClassVar[str] = ''
    input_kind: ClassVar[str] = INPUT_IMAGE
    # 'text' goes straight to the clipboard; 'alfred' is wrapped in the JSON a
    # Script Filter expects.
    output_format: ClassVar[str] = 'text'
    required_credentials: ClassVar[Tuple[str, ...]] = ()
    # Name of the setting holding this engine's upload limit, if it has one.
    max_bytes_setting: ClassVar[Optional[str]] = None

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or default_settings

    @property
    def max_bytes(self) -> Optional[int]:
        if not self.max_bytes_setting:
            return None
        return self.settings.int(self.max_bytes_setting)

    @property
    def keys(self) -> Tuple[str, ...]:
        '''Every token the router accepts for this provider.'''
        tokens = [self.name, *self.aliases]
        if self.selector is not None:
            tokens.append(str(self.selector))
        return tuple(tokens)

    def validate(self) -> None:
        if self.required_credentials:
            self.settings.require(*self.required_credentials)

    def run(self, payload: Any = None) -> OcrResult:
        '''Validate the request, then hand it to the engine.'''
        self.validate()
        if isinstance(payload, ImageFile):
            payload.check_size(self.max_bytes)
        return self.recognize(payload)

    @abc.abstractmethod
    def recognize(self, payload: Any) -> OcrResult:
        '''Do the actual work. ``payload`` matches ``input_kind``.'''

    def __repr__(self) -> str:
        return '<%s %s>' % (type(self).__name__, self.name)
