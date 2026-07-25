# -*- coding: UTF-8 -*-
import pytest

from core.exceptions import ApiError, ConfigError, EmptyResultError, ImageError
from providers.baidu import (BaiduFormulaOcr, BaiduGeneralOcr, BaiduMultiFileOcr,
                             BaiduQrReader, BaiduTableOcr)
from providers.baidu import client
from providers.baidu.qr_reader import format_codes
from providers.baidu.table_ocr import to_tsv


@pytest.fixture
def baidu_credentials(monkeypatch):
    monkeypatch.setenv('baidu_api_key', 'key')
    monkeypatch.setenv('baidu_secret_key', 'secret')


@pytest.fixture
def fake_baidu(monkeypatch):
    '''Capture the outgoing request and answer with a canned payload.'''
    calls = []

    def respond(payload):
        def fake_request(endpoint_setting, image, max_bytes=None, extra=None):
            calls.append({'endpoint': endpoint_setting, 'image': image,
                          'max_bytes': max_bytes, 'extra': extra})
            return payload
        monkeypatch.setattr(client, 'request', fake_request)
        return calls

    return respond


def test_general_ocr_returns_paragraphs(baidu_credentials, fake_baidu, image_file):
    fake_baidu({'words_result': [
        {'words': '这是第一段的第一行内容',
         'location': {'left': 100, 'top': 0, 'width': 330, 'height': 30}},
        {'words': '继续同一段落的第二行',
         'location': {'left': 100, 'top': 40, 'width': 300, 'height': 30}},
        {'words': '第二段从这里开始了',
         'location': {'left': 160, 'top': 120, 'width': 270, 'height': 30}},
    ]})
    text = BaiduGeneralOcr().run(image_file).render()
    assert text == '这是第一段的第一行内容继续同一段落的第二行\n第二段从这里开始了'


def test_general_ocr_sends_the_language_and_the_limit(baidu_credentials,
                                                      fake_baidu, image_file):
    calls = fake_baidu({'words_result': [{'words': 'x'}]})
    BaiduGeneralOcr().run(image_file)
    assert calls[0]['endpoint'] == 'baidu_ocr_api'
    assert calls[0]['extra'] == {'language_type': 'CHN_ENG'}
    assert calls[0]['max_bytes'] == 4 * 1024 * 1024


def test_general_ocr_on_an_empty_page(baidu_credentials, fake_baidu, image_file):
    fake_baidu({'words_result': []})
    with pytest.raises(EmptyResultError):
        BaiduGeneralOcr().run(image_file)


def test_missing_credentials_are_reported_before_the_request(image_file):
    with pytest.raises(ConfigError) as error:
        BaiduGeneralOcr().run(image_file)
    assert 'baidu_api_key' in error.value.message


def test_an_oversized_image_is_refused_before_upload(baidu_credentials,
                                                     monkeypatch, image_file):
    monkeypatch.setenv('baidu_max_image_bytes', '8')

    def must_not_run(*args, **kwargs):
        raise AssertionError('the image was uploaded despite the size limit')

    monkeypatch.setattr(client, 'request', must_not_run)
    with pytest.raises(ImageError) as error:
        BaiduGeneralOcr().run(image_file)
    assert error.value.message == 'Too large!'


def test_api_errors_surface_the_vendor_message(baidu_credentials, monkeypatch,
                                               image_file):
    from core import auth_manager, http_client

    monkeypatch.setattr(auth_manager.baidu, 'token', lambda force_refresh=False: 't')
    monkeypatch.setattr(http_client, 'post_json',
                        lambda *args, **kwargs: {'error_code': 216201,
                                                 'error_msg': 'image format error'})
    with pytest.raises(ApiError) as error:
        BaiduGeneralOcr().run(image_file)
    assert error.value.message == 'image format error'


def test_a_rejected_token_is_refreshed_once(baidu_credentials, monkeypatch,
                                            image_file):
    from core import auth_manager, http_client

    tokens = []
    responses = [{'error_code': 110, 'error_msg': 'Access token invalid'},
                 {'words_result': [{'words': 'ok'}]}]

    def fake_token(force_refresh=False):
        tokens.append(force_refresh)
        return 'refreshed' if force_refresh else 'cached'

    monkeypatch.setattr(auth_manager.baidu, 'token', fake_token)
    monkeypatch.setattr(http_client, 'post_json',
                        lambda *args, **kwargs: responses.pop(0))
    assert BaiduGeneralOcr().run(image_file).render() == 'ok'
    assert tokens == [False, True]


def test_table_is_laid_out_as_tsv():
    body = [
        {'row_start': 0, 'col_start': 0, 'words': '姓名'},
        {'row_start': 0, 'col_start': 1, 'words': '分数'},
        {'row_start': 1, 'col_start': 0, 'words': '张三'},
        {'row_start': 1, 'col_start': 1, 'words': '90'},
    ]
    assert to_tsv(body) == '姓名\t分数\n张三\t90'


def test_table_cell_newlines_and_tabs_do_not_shift_the_grid():
    assert to_tsv([{'row_start': 0, 'col_start': 0, 'words': 'a\nb\tc'}]) == 'a b c'


def test_table_ignores_malformed_cells():
    assert to_tsv([{'words': 'orphan'}]) == ''


def test_table_provider(baidu_credentials, fake_baidu, image_file):
    fake_baidu({'tables_result': [
        {'body': [{'row_start': 0, 'col_start': 0, 'words': 'a'}]},
        {'body': [{'row_start': 0, 'col_start': 0, 'words': 'b'}]},
    ]})
    assert BaiduTableOcr().run(image_file).render() == 'a\n\nb'


def test_qrcode_single_group():
    assert format_codes([{'text': ['line1', 'line2']}]) == 'line1\nline2'


def test_qrcode_multiple_groups():
    assert format_codes([{'text': ['a']}, {'text': ['b']}]) == \
        'Group 1\na\n\nGroup 2\nb'


def test_qrcode_empty():
    with pytest.raises(EmptyResultError):
        format_codes([])
    with pytest.raises(EmptyResultError):
        format_codes([{'text': []}])


def test_qrcode_payload_is_not_reformatted(baidu_credentials, fake_baidu,
                                           image_file):
    fake_baidu({'codes_result': [{'text': ['https://example.com/中文,x']}]})
    assert BaiduQrReader().run(image_file).render() == 'https://example.com/中文,x'


def test_formula_keeps_the_latex(baidu_credentials, fake_baidu, image_file):
    fake_baidu({'formula_result': [{'words': 'a_{1}'}, {'words': 'b^{2}'}]})
    assert BaiduFormulaOcr().run(image_file).render() == 'a_{1} \\\\\n\nb^{2} \\\\'


def test_multi_file_recognizes_every_image(baidu_credentials, monkeypatch,
                                           tmp_path):
    for name in ('a.png', 'b.png'):
        (tmp_path / name).write_bytes(b'\x89PNG' + b'x' * 16)

    pages = {'a.png': 'first page', 'b.png': 'second page'}

    def fake_request(endpoint_setting, image, max_bytes=None, extra=None):
        return {'words_result': [{'words': pages[image.name]}]}

    monkeypatch.setattr(client, 'request', fake_request)
    text = BaiduMultiFileOcr().run(str(tmp_path)).render()
    assert text == 'first page\n\nsecond page'
    # The drop folder is emptied as the pages are consumed.
    assert not list(tmp_path.iterdir())


def test_multi_file_keeps_going_after_a_failed_page(baidu_credentials,
                                                    monkeypatch, tmp_path):
    for name in ('a.png', 'b.png'):
        (tmp_path / name).write_bytes(b'\x89PNG' + b'x' * 16)

    def fake_request(endpoint_setting, image, max_bytes=None, extra=None):
        if image.name == 'a.png':
            raise ApiError('image format error')
        return {'words_result': [{'words': 'second page'}]}

    monkeypatch.setattr(client, 'request', fake_request)
    text = BaiduMultiFileOcr().run(str(tmp_path)).render()
    assert text == 'image format error\n\nsecond page'


def test_multi_file_on_an_empty_folder(baidu_credentials, tmp_path):
    with pytest.raises(ImageError):
        BaiduMultiFileOcr().run(str(tmp_path))
