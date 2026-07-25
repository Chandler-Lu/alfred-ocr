# -*- coding: UTF-8 -*-
'''Paragraph reconstruction, driven by synthetic line boxes.

Geometry mirrors a plain text column: 30 px tall lines on a 44 px pitch, a
15 px half-width unit (so one ideograph is 30 px), text starting at x=100.
'''
import pytest

from core.formatter import render_lines
from core.layout import (LayoutOptions, TextLine, compute_metrics, group,
                         visual_units)

UNIT = 15
LINE_HEIGHT = 30
PITCH = 44
LEFT = 100


def line(text, top, left=LEFT, width=None, height=LINE_HEIGHT):
    if width is None:
        width = visual_units(text) * UNIT
    return TextLine(text=text, left=left, top=top, width=width, height=height)


def test_wrapped_chinese_lines_form_one_paragraph():
    lines = [
        line('中' * 20, 0),
        line('文' * 20, PITCH),
        line('最后一行结束了', PITCH * 2),
    ]
    assert group(lines) == ['中' * 20 + '文' * 20 + '最后一行结束了']


def test_extra_vertical_gap_starts_a_paragraph():
    lines = [
        line('中' * 20, 0),
        line('文' * 20, PITCH),
        line('短行', PITCH * 2),
        line('新' * 20, PITCH * 2 + 70),
    ]
    paragraphs = group(lines)
    assert len(paragraphs) == 2
    assert paragraphs[0].endswith('短行')
    assert paragraphs[1] == '新' * 20


def test_english_lines_are_joined_with_a_space():
    lines = [
        line('The quick brown fox jumps over', 0),
        line('the lazy dog near the river bank', PITCH),
    ]
    assert render_lines(lines) == \
        'The quick brown fox jumps over the lazy dog near the river bank'


def test_hyphenated_english_word_is_rejoined():
    lines = [line('an inter-', 0), line('national standard applies', PITCH)]
    assert render_lines(lines) == 'an international standard applies'


def test_list_items_stay_on_separate_lines():
    lines = [line('• 第一项', 0), line('• 第二项', PITCH), line('• 第三项', PITCH * 2)]
    assert group(lines) == ['• 第一项', '• 第二项', '• 第三项']


def test_numbered_list_items_stay_separate():
    lines = [line('1. 打开设置', 0), line('2. 点击确认', PITCH)]
    assert len(group(lines)) == 2


def test_first_line_indent_starts_a_paragraph():
    lines = [line('中' * 20, 0), line('文' * 20, PITCH, left=LEFT + 60)]
    assert len(group(lines)) == 2


def test_hanging_indent_of_a_list_item_is_not_a_new_paragraph():
    # The continuation of a bullet is indented under the item text; treating
    # that as a first-line indent would split every wrapped list entry.
    lines = [
        line('• 这是第一项的内容比较长所以', 0),
        line('会换行到第二行继续', PITCH, left=LEFT + 60),
    ]
    assert len(group(lines)) == 1


def test_indent_after_a_short_line_starts_a_paragraph():
    lines = [
        line('中' * 20, 0, left=LEFT + 60),
        line('文' * 20, PITCH),
        line('短', PITCH * 2),
        line('新' * 20, PITCH * 3, left=LEFT + 60),
    ]
    paragraphs = group(lines)
    assert len(paragraphs) == 2
    assert paragraphs[1] == '新' * 20


def test_heading_is_split_from_the_body():
    lines = [
        TextLine(text='标题', left=LEFT, top=0, width=120, height=48),
        line('正文' * 10, 64),
    ]
    paragraphs = group(lines)
    assert paragraphs[0] == '标题'
    assert len(paragraphs) == 2


def test_boxes_on_the_same_visual_row_are_merged():
    lines = [
        TextLine(text='中文', left=0, top=0, width=60, height=30),
        TextLine(text='abc', left=80, top=2, width=45, height=28),
    ]
    assert render_lines(lines) == '中文 abc'


def test_second_column_starts_a_paragraph():
    lines = [
        line('左栏第一行', 0),
        line('左栏第二行', PITCH),
        line('右栏第一行', 0, left=800),
    ]
    assert len(group(lines)) == 2


@pytest.mark.parametrize('texts, expected', [
    (['这是第一句。', '这是第二句。'], 2),
    (['因为，', '所以就这样。'], 1),
    (['continues with', 'no punctuation'], 1),
])
def test_text_only_fallback_without_geometry(texts, expected):
    lines = [TextLine(text=text) for text in texts]
    assert len(group(lines)) == expected


def test_blank_lines_are_dropped():
    lines = [line('内容', 0),
             TextLine(text='   ', left=LEFT, top=PITCH, width=30, height=LINE_HEIGHT)]
    assert group(lines) == ['内容']


def test_empty_input():
    assert group([]) == []


def test_metrics_survive_missing_geometry():
    metrics = compute_metrics([TextLine(text='abc')])
    assert metrics.line_height > 0
    assert metrics.line_pitch > 0
    assert metrics.char_width > 0
    assert metrics.body_width >= 1


def test_metrics_of_a_regular_column():
    lines = [line('中' * 20, 0), line('文' * 20, PITCH)]
    metrics = compute_metrics(lines)
    assert metrics.line_height == pytest.approx(LINE_HEIGHT)
    assert metrics.line_pitch == pytest.approx(PITCH)
    assert metrics.char_width == pytest.approx(UNIT * 2)
    assert metrics.body_left == pytest.approx(LEFT)


def test_line_pitch_ignores_the_paragraph_gaps():
    # The median would be dragged up by the gap and hide it; a low percentile
    # keeps the body pitch as the baseline.
    lines = [line('中' * 20, 0), line('文' * 20, PITCH), line('新' * 20, PITCH + 90)]
    assert compute_metrics(lines).line_pitch == pytest.approx(PITCH)


def test_options_from_settings():
    options = LayoutOptions.from_settings()
    assert options.gap_ratio > 1
    assert options.weight('big_gap') > 0
    assert options.weight('unknown_signal') == 0


def test_custom_options_can_force_line_breaks():
    lines = [line('中' * 20, 0), line('文' * 20, PITCH)]
    assert len(group(lines, LayoutOptions(break_threshold=0.0))) == 2


def test_textline_from_polygon():
    corners = TextLine.from_polygon('内容', [[10, 20], [70, 20], [70, 50], [10, 50]])
    assert (corners.left, corners.top, corners.width, corners.height) == \
        (10, 20, 60, 30)
    points = TextLine.from_polygon('内容', [{'X': 5, 'Y': 6}, {'X': 15, 'Y': 26}])
    assert (points.left, points.top, points.width, points.height) == (5, 6, 10, 20)
    assert not TextLine.from_polygon('内容', []).has_geometry
    assert not TextLine.from_polygon('内容', [{'oops': 1}]).has_geometry


def test_textline_from_box_tolerates_rubbish():
    assert not TextLine.from_box('内容', left=None, top='x').has_geometry
