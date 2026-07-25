'''Rebuild paragraphs from the per-line boxes an OCR engine returns.

The engine reports visual lines; a reader wants paragraphs. Whether two
neighbouring lines belong together is decided by combining weighted signals,
instead of picking one rule for the whole image as the original code did:

    vertical gap      a step larger than the usual line pitch
    short line        the previous line stopped before the column edge
    first-line indent the next line starts right of the column
    font size change  a heading or caption interrupts the flow
    punctuation       what the previous line ends with

Every threshold is a ratio of a measured page metric (line pitch, character
width), so the same numbers work for a Retina screenshot and a 96 dpi scan.
Set debug=1 to print the reasoning for each boundary to stderr.
'''
# -*- coding: UTF-8 -*-
from __future__ import annotations

import re
import statistics
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from core.config import settings
from core.output import debug
from utils.punctuation import CJK_PUNCTUATION, latin_ratio

LIST_MARKER_RE = re.compile(
    r'''^\s*(?:
        [\u2022\u00b7\u25aa\u25e6\u2023\u2219*]\s*
      | [-\u2013\u2014]\s
      | \(?\d{1,3}[.)\u3001]\s*
      | [a-zA-Z][.)]\s
      | [（(][一二三四五六七八九十百\d]{1,3}[）)]
      | [一二三四五六七八九十百]{1,3}[\u3001.]\s*
      | 第[一二三四五六七八九十百千\d]+[章节節条款项項部篇讲课]
      | Step\s+\d+
      | \u25a0|\u25c6|\u2714
    )''',
    re.VERBOSE,
)
SENTENCE_END_RE = re.compile(r'[。．.!！?？;；…】》」』]["”’』」）)\]]?\s*$')
CONTINUATION_RE = re.compile(
    r'[，,、;；:：/\\|~\-\u2013\u2014“"\'(（《「『【等和与及或]\s*$')
TRAILING_HYPHEN_RE = re.compile(r'([A-Za-z])[-\u2010\u2011]\s*$')
LOWER_START_RE = re.compile(r'^[a-z]')

# How strongly each signal argues for a paragraph break. The sum is compared
# with break_threshold; overridable per instance through LayoutOptions.
SIGNAL_WEIGHTS: Dict[str, float] = {
    'big_gap': 1.0,
    'huge_gap': 1.0,
    # A first-line indent is *the* paragraph marker in Chinese typesetting, so
    # it decides on its own. The hanging indent of a list item is excluded.
    'indent': 1.0,
    'short_line': 0.8,
    'unterminated_short_line': 0.25,
    'sentence_end': 0.35,
    'height_change': 0.8,
    'centered': 0.6,
    'continuation': -0.6,
}


@dataclass(frozen=True)
class TextLine:
    '''One recognized line with its box, in pixels.

    ``width``/``height`` of 0 mean "geometry unavailable" - engines such as
    Baidu's *_basic endpoints omit it - and the caller falls back to
    punctuation-only paragraph detection.
    '''

    text: str
    left: float = 0.0
    top: float = 0.0
    width: float = 0.0
    height: float = 0.0

    @property
    def right(self) -> float:
        return self.left + self.width

    @property
    def bottom(self) -> float:
        return self.top + self.height

    @property
    def center_x(self) -> float:
        return self.left + self.width / 2.0

    @property
    def has_geometry(self) -> bool:
        return self.width > 0 and self.height > 0

    @classmethod
    def from_box(cls, text: str, left: Any = 0, top: Any = 0,
                 width: Any = 0, height: Any = 0) -> 'TextLine':
        return cls(text=str(text), left=number(left), top=number(top),
                   width=number(width), height=number(height))

    @classmethod
    def from_polygon(cls, text: str, points: Iterable[Any]) -> 'TextLine':
        '''Build from a list of corner points, as CnOCR and Tencent report.'''
        xs: List[float] = []
        ys: List[float] = []
        for point in points or []:
            try:
                if isinstance(point, Mapping):
                    xs.append(float(point['X']))
                    ys.append(float(point['Y']))
                else:
                    xs.append(float(point[0]))
                    ys.append(float(point[1]))
            except (KeyError, IndexError, TypeError, ValueError):
                return cls(text=str(text))
        if not xs or not ys:
            return cls(text=str(text))
        return cls(text=str(text), left=min(xs), top=min(ys),
                   width=max(xs) - min(xs), height=max(ys) - min(ys))


@dataclass(frozen=True)
class LayoutOptions:
    gap_ratio: float = 1.45
    short_line_chars: float = 3.0
    latin_short_factor: float = 1.6
    indent_chars: float = 1.2
    height_tolerance: float = 0.3
    break_threshold: float = 1.0
    spacing_offset: float = 8.0
    width_offset: float = 50.0
    weights: Dict[str, float] = field(default_factory=lambda: dict(SIGNAL_WEIGHTS))

    @classmethod
    def from_settings(cls) -> 'LayoutOptions':
        return cls(
            gap_ratio=settings.float('paragraph_gap_ratio'),
            short_line_chars=settings.float('paragraph_short_line_chars'),
            latin_short_factor=settings.float('paragraph_latin_short_factor'),
            indent_chars=settings.float('paragraph_indent_chars'),
            height_tolerance=settings.float('paragraph_height_tolerance'),
            break_threshold=settings.float('paragraph_break_threshold'),
            spacing_offset=settings.float('baidu_ocr_spacing_offset'),
            width_offset=settings.float('baidu_ocr_width_offset'),
        )

    def weight(self, signal: str) -> float:
        return self.weights.get(signal, SIGNAL_WEIGHTS.get(signal, 0.0))


@dataclass(frozen=True)
class PageMetrics:
    line_pitch: float
    line_height: float
    char_width: float
    body_left: float
    body_right: float

    @property
    def body_width(self) -> float:
        return max(1.0, self.body_right - self.body_left)

    @property
    def body_center(self) -> float:
        return (self.body_left + self.body_right) / 2.0


@dataclass(frozen=True)
class Decision:
    '''Why two lines were joined or split. Carried around for debugging.'''

    break_paragraph: bool
    same_visual_line: bool = False
    dehyphenate: bool = False
    score: float = 0.0
    signals: Tuple[str, ...] = ()

    @property
    def reason(self) -> str:
        if self.same_visual_line:
            return 'same-line'
        return ('break' if self.break_paragraph else 'join') + \
            '(' + ','.join(self.signals) + ' = %.2f)' % self.score


def number(value: Any) -> float:
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        return 0.0


def _median(values: Sequence[float], default: float) -> float:
    try:
        return float(statistics.median(values))
    except statistics.StatisticsError:
        return default


def _percentile(values: Sequence[float], fraction: float, default: float) -> float:
    if not values:
        return default
    ordered = sorted(values)
    index = int(round(fraction * (len(ordered) - 1)))
    return float(ordered[min(max(index, 0), len(ordered) - 1)])


def _dominant(values: Sequence[float], tolerance: float, default: float,
              prefer_high: bool) -> float:
    '''The edge shared by the largest group of lines.

    Body text repeats the same left and right edge, so the biggest cluster is
    the text column - unlike a percentile, which a second column or one
    over-long line pulls off target. Ties go to the outermost candidate.
    '''
    if not values:
        return default
    ordered = sorted(values)
    best_count = 0
    best_edge = ordered[-1] if prefer_high else ordered[0]
    for anchor in ordered:
        bucket = [value for value in ordered if abs(value - anchor) <= tolerance]
        edge = max(bucket) if prefer_high else min(bucket)
        better = len(bucket) > best_count or (
            len(bucket) == best_count and
            (edge > best_edge if prefer_high else edge < best_edge))
        if better:
            best_count, best_edge = len(bucket), edge
    return best_edge


def visual_units(text: str) -> int:
    '''Length of ``text`` in half-width units, so 中 counts as two.'''
    units = 0
    for char in text:
        if unicodedata.east_asian_width(char) in ('W', 'F') or \
                char in CJK_PUNCTUATION:
            units += 2
        else:
            units += 1
    return units


def compute_metrics(lines: Sequence[TextLine]) -> PageMetrics:
    '''Measure the page so thresholds can be expressed relative to it.'''
    boxed = [line for line in lines if line.has_geometry]
    line_height = _median([line.height for line in boxed], 20.0)

    pitches = [
        later.top - earlier.top
        for earlier, later in zip(lines, lines[1:])
        if later.top - earlier.top > line_height * 0.4
    ]
    # A low percentile, not the median: on a short excerpt the paragraph gaps
    # themselves make up a large share of the samples and would inflate the
    # baseline until no gap looks unusual any more.
    line_pitch = _percentile(pitches, 0.35, line_height * 1.4) or line_height * 1.4

    # One ideograph is two half-width units wide.
    unit_widths = [line.width / visual_units(line.text)
                   for line in boxed if visual_units(line.text) > 0]
    char_width = _median(unit_widths, 0.0) * 2.0
    if char_width <= 0:
        char_width = line_height

    return PageMetrics(
        line_pitch=line_pitch,
        line_height=line_height,
        char_width=char_width,
        # Tighter tolerance on the left so a first-line indent stays outside
        # the body cluster instead of redefining it.
        body_left=_dominant([line.left for line in boxed],
                            char_width * 0.6, 0.0, prefer_high=False),
        body_right=_dominant([line.right for line in boxed],
                             char_width, 0.0, prefer_high=True),
    )


def _short_line_limit(line: TextLine, metrics: PageMetrics,
                      options: LayoutOptions) -> float:
    '''How much white space at the end of a line still counts as "full".

    Latin text wraps on word boundaries and can legitimately stop a whole word
    short, so it gets a wider allowance than CJK, which wraps per character.
    '''
    limit = options.short_line_chars * metrics.char_width
    if latin_ratio(line.text) > 0.6:
        limit *= options.latin_short_factor
    return max(limit, options.width_offset * 0.4)


def classify(previous: TextLine, current: TextLine, metrics: PageMetrics,
             options: LayoutOptions) -> Decision:
    '''Decide how ``current`` relates to ``previous``.'''
    if not previous.has_geometry or not current.has_geometry:
        return classify_by_text(previous, current)

    # A line starting above the previous one belongs to a new column or region;
    # keep them apart whatever the other signals say.
    if current.top < previous.top - metrics.line_height * 0.5:
        return Decision(True, signals=('new_column',), score=99.0)

    overlap = min(previous.bottom, current.bottom) - max(previous.top, current.top)
    if (overlap > 0.5 * min(previous.height, current.height)
            and current.left >= previous.right - metrics.char_width):
        return Decision(False, same_visual_line=True)

    if LIST_MARKER_RE.match(current.text):
        return Decision(True, signals=('list_marker',), score=99.0)

    if TRAILING_HYPHEN_RE.search(previous.text) and \
            LOWER_START_RE.match(current.text.lstrip()):
        return Decision(False, dehyphenate=True, signals=('hyphenation',))

    signals: List[str] = []
    score = 0.0

    def vote(signal: str) -> None:
        nonlocal score
        signals.append(signal)
        score += options.weight(signal)

    delta = current.top - previous.top
    if delta > metrics.line_pitch * options.gap_ratio and \
            delta > metrics.line_pitch + options.spacing_offset:
        vote('big_gap')
    if delta > metrics.line_pitch * (options.gap_ratio + 0.8):
        vote('huge_gap')

    indented = current.left - metrics.body_left > \
        options.indent_chars * metrics.char_width
    if indented and LIST_MARKER_RE.match(previous.text) and \
            current.left > previous.left:
        # Continuation of a list item, aligned under its text: not an indent.
        indented = False
    if indented:
        vote('indent')

    is_short = metrics.body_right - previous.right > \
        _short_line_limit(previous, metrics, options)
    if is_short:
        vote('short_line')

    ends_sentence = bool(SENTENCE_END_RE.search(previous.text))
    continues = bool(CONTINUATION_RE.search(previous.text))
    if ends_sentence:
        vote('sentence_end')
    elif is_short and not continues:
        # Short and unpunctuated: a heading, a caption or a list entry.
        vote('unterminated_short_line')
    if continues:
        vote('continuation')

    tallest = max(previous.height, current.height)
    if tallest > 0 and \
            abs(current.height - previous.height) / tallest > options.height_tolerance:
        vote('height_change')

    if is_short and \
            abs(previous.center_x - metrics.body_center) < metrics.char_width and \
            previous.left - metrics.body_left > metrics.char_width * 1.5:
        vote('centered')

    return Decision(score >= options.break_threshold, score=score,
                    signals=tuple(signals))


def classify_by_text(previous: TextLine, current: TextLine) -> Decision:
    '''Fallback when the engine gave us no boxes: trust the punctuation.'''
    if LIST_MARKER_RE.match(current.text):
        return Decision(True, signals=('list_marker',))
    if TRAILING_HYPHEN_RE.search(previous.text) and \
            LOWER_START_RE.match(current.text.lstrip()):
        return Decision(False, dehyphenate=True, signals=('hyphenation',))
    if CONTINUATION_RE.search(previous.text):
        return Decision(False, signals=('continuation',))
    if SENTENCE_END_RE.search(previous.text):
        return Decision(True, signals=('sentence_end',))
    return Decision(False, signals=('no_signal',))


def join_separator(left: str, right: str) -> str:
    '''What to put between two lines of the same paragraph.

    Nothing around CJK, a single space between Latin words - the old code
    always concatenated, which silently glued English lines together.
    '''
    if not left or not right:
        return ''
    if left[-1].isspace() or right[0].isspace():
        return ''
    from utils.punctuation import is_cjk_like_char
    if is_cjk_like_char(left[-1]) or is_cjk_like_char(right[0]):
        return ''
    return ' '


def group(lines: Sequence[TextLine],
          options: Optional[LayoutOptions] = None) -> List[str]:
    '''Join ``lines`` into paragraph strings.'''
    kept = [line for line in lines if line.text and line.text.strip()]
    if not kept:
        return []
    options = options or LayoutOptions.from_settings()
    metrics = compute_metrics(kept)

    paragraphs: List[str] = []
    buffer = kept[0].text.strip()
    for previous, current in zip(kept, kept[1:]):
        decision = classify(previous, current, metrics, options)
        debug('[layout] %-28r %s', current.text[:24], decision.reason)
        text = current.text.strip()
        if decision.break_paragraph:
            paragraphs.append(buffer)
            buffer = text
        elif decision.dehyphenate:
            buffer = TRAILING_HYPHEN_RE.sub(r'\1', buffer) + text
        else:
            buffer += join_separator(buffer, text) + text
    paragraphs.append(buffer)
    return [paragraph for paragraph in paragraphs if paragraph]
