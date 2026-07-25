# -*- coding: UTF-8 -*-
import pytest

from core.formatter import (add_cjk_latin_space, format_text,
                            normalize_punctuation, render_lines)
from core.layout import TextLine
from utils.punctuation import fold_fullwidth_ascii, is_cjk, latin_ratio


@pytest.mark.parametrize('source, expected', [
    ('你好world', '你好 world'),
    ('中文123测试', '中文 123 测试'),
    ('word汉字', 'word 汉字'),
    ('已经100%完成了', '已经 100% 完成了'),
    ('已经 100% 完成了', '已经 100% 完成了'),
    ('全是中文没有变化', '全是中文没有变化'),
    ('pure english stays', 'pure english stays'),
])
def test_cjk_latin_spacing(source, expected):
    assert format_text(source) == expected


def test_plus_sign_is_not_a_chinese_character():
    # The old character class [\u4e00-\u9fa5+] treated '+' as CJK.
    assert format_text('C++代码') == 'C++ 代码'
    assert format_text('a+b') == 'a+b'


@pytest.mark.parametrize('source', [
    '访问 https://example.com/a_b?x=1&y=2 查看',
    '邮箱 admin@example.com 已启用',
    '合计 1,000.50 元',
    '时间 12:30 开始',
])
def test_protected_tokens_survive(source):
    assert format_text(source) == source


def test_url_stops_at_chinese():
    assert format_text('访问https://example.com看看') == \
        '访问 https://example.com 看看'


def test_url_keeps_sentence_punctuation_outside():
    assert format_text('见 https://example.com。') == '见 https://example.com。'


@pytest.mark.parametrize('source, expected', [
    ('注意:内容', '注意：内容'),
    ('注意: 内容', '注意：内容'),
    ('中文,然后继续', '中文，然后继续'),
    ('使用Python,然后运行', '使用 Python，然后运行'),
    ('他说(不行)', '他说（不行）'),
])
def test_punctuation_follows_the_local_script(source, expected):
    assert format_text(source) == expected


@pytest.mark.parametrize('source, expected', [
    ('Hello，world！', 'Hello,world!'),
    ('Total（five）items', 'Total(five)items'),
])
def test_fullwidth_becomes_ascii_between_latin(source, expected):
    assert format_text(source) == expected


def test_ascii_technical_notation_is_left_alone():
    # A line-wide "this line is Chinese" switch used to mangle all of these.
    assert format_text('计算f(x)=1的值') == '计算 f(x)=1 的值'
    assert format_text('共1,000人参加') == '共 1,000 人参加'
    assert format_text('版本v1.2.3发布') == '版本 v1.2.3 发布'


def test_chinese_parentheses_kept_when_context_is_chinese():
    assert format_text('中文（English）说明') == '中文（English）说明'


def test_em_dash_misread_is_repaired():
    assert format_text('中文—一测试') == '中文——测试'


@pytest.mark.parametrize('source', [
    '你好world你好',
    '注意:内容',
    '访问 https://example.com/a 查看',
    'mixed 中文 and english 混排',
])
def test_format_is_idempotent(source):
    once = format_text(source)
    assert format_text(once) == once


def test_newlines_are_preserved():
    assert format_text('第一段text\n第二段text') == '第一段 text\n第二段 text'


def test_toggles_can_be_switched_off():
    assert format_text('你好world', add_space=False) == '你好world'
    assert format_text('注意:内容', normalize=False) == '注意:内容'
    assert format_text('ＡＢ12', fold_fullwidth=True) == 'AB12'


def test_add_space_is_idempotent_on_its_own():
    assert add_cjk_latin_space('你好 world') == '你好 world'


def test_normalize_punctuation_leaves_decimals():
    assert normalize_punctuation('3.14') == '3.14'


def test_fold_fullwidth_ascii():
    assert fold_fullwidth_ascii('ＡＢ１２') == 'AB12'
    assert fold_fullwidth_ascii('中文，') == '中文，'


def test_script_helpers():
    assert is_cjk('abc中')
    assert not is_cjk('abc')
    assert latin_ratio('abcd') == 1.0
    assert latin_ratio('中文') == 0.0
    assert latin_ratio('') == 0.0
    assert format_text('') == ''


def test_render_lines_formats_after_merging():
    # The space between the Chinese line and the English one only becomes
    # visible once the two lines have been joined.
    lines = [
        TextLine('这是中文', left=100, top=0, width=120, height=30),
        TextLine('English text', left=100, top=40, width=180, height=30),
    ]
    assert render_lines(lines) == '这是中文 English text'


def test_render_lines_without_paragraph_merging():
    lines = [
        TextLine('第一行', left=100, top=0, width=90, height=30),
        TextLine('第二行', left=100, top=40, width=90, height=30),
    ]
    assert render_lines(lines, paragraphs=False) == '第一行\n第二行'


def test_render_lines_on_empty_input():
    assert render_lines([]) == ''
