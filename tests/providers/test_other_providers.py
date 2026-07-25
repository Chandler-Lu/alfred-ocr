# -*- coding: UTF-8 -*-
'''Tencent, Google, CnOCR, Mathpix, ZXing and Caiyun.'''
import pytest

from core import http_client
from core.exceptions import (ApiError, ConfigError, DependencyError,
                             EmptyResultError)
from providers.caiyun import CaiyunTranslator
from providers.caiyun.translator import detect_direction
from providers.cnocr import CnOcrOffline
from providers.google import GoogleGeneralOcr
from providers.mathpix import MathpixFormulaOcr
from providers.tencent import TencentGeneralOcr
from providers.tencent.general_ocr import line_from_detection


@pytest.fixture
def canned(monkeypatch):
    def respond(payload):
        calls = []

        def fake_post(url, **kwargs):
            calls.append({'url': url, **kwargs})
            return payload
        monkeypatch.setattr(http_client, 'post_json', fake_post)
        return calls
    return respond


'''
Tencent
'''


def test_tencent_lines_go_through_paragraph_merging(monkeypatch, canned,
                                                    image_file):
    monkeypatch.setenv('tencent_secret_id', 'id')
    monkeypatch.setenv('tencent_secret_key', 'secret')
    canned({'Response': {'TextDetections': [
        {'DetectedText': '这是中文',
         'ItemPolygon': {'X': 100, 'Y': 0, 'Width': 120, 'Height': 30}},
        {'DetectedText': 'English text',
         'ItemPolygon': {'X': 100, 'Y': 40, 'Width': 180, 'Height': 30}},
    ]}})
    assert TencentGeneralOcr().run(image_file).render() == '这是中文 English text'


def test_tencent_reports_the_vendor_error(monkeypatch, canned, image_file):
    monkeypatch.setenv('tencent_secret_id', 'id')
    monkeypatch.setenv('tencent_secret_key', 'secret')
    canned({'Response': {'Error': {'Message': 'AuthFailure'}}})
    with pytest.raises(ApiError) as error:
        TencentGeneralOcr().run(image_file)
    assert error.value.message == 'AuthFailure'


def test_tencent_needs_credentials(image_file):
    with pytest.raises(ConfigError):
        TencentGeneralOcr().run(image_file)


def test_tencent_signature_is_deterministic(monkeypatch):
    monkeypatch.setenv('tencent_secret_id', 'id')
    monkeypatch.setenv('tencent_secret_key', 'secret')
    provider = TencentGeneralOcr()
    first = provider.authorization(b'{"a":1}', 1600000000)
    second = provider.authorization(b'{"a":1}', 1600000000)
    assert first == second
    assert first.startswith('TC3-HMAC-SHA256 Credential=id/2020-09-13/ocr/')
    assert provider.authorization(b'{"a":2}', 1600000000) != first


def test_tencent_falls_back_to_the_polygon():
    line = line_from_detection({'DetectedText': 'x',
                                'Polygon': [{'X': 3, 'Y': 4}, {'X': 13, 'Y': 24}]})
    assert (line.left, line.top, line.width, line.height) == (3, 4, 10, 20)


'''
Google
'''


def test_google_returns_the_page_text(monkeypatch, canned, image_file):
    monkeypatch.setenv('google_access_token', 'token')
    canned({'responses': [{'textAnnotations': [
        {'description': '第一行text\n第二行\n'}]}]})
    assert GoogleGeneralOcr().run(image_file).render() == '第一行 text\n第二行'


def test_google_reports_the_vendor_error(monkeypatch, canned, image_file):
    monkeypatch.setenv('google_access_token', 'token')
    canned({'responses': [{'error': {'message': 'Bad image data'}}]})
    with pytest.raises(ApiError):
        GoogleGeneralOcr().run(image_file)


def test_google_on_an_empty_page(monkeypatch, canned, image_file):
    monkeypatch.setenv('google_access_token', 'token')
    canned({'responses': [{}]})
    with pytest.raises(EmptyResultError):
        GoogleGeneralOcr().run(image_file)


def test_google_does_not_set_its_own_proxy(monkeypatch, canned, image_file):
    # The proxy is global and lives in http_client; no provider overrides it.
    monkeypatch.setenv('google_access_token', 'token')
    calls = canned({'responses': [{'textAnnotations': [{'description': 'x'}]}]})
    GoogleGeneralOcr().run(image_file)
    assert 'proxies' not in calls[0]


'''
CnOCR
'''


def test_cnocr_service_mode(monkeypatch, canned, image_file):
    monkeypatch.setenv('cnocr_serve', '1')
    canned({'results': [
        {'text': '这是中文', 'position': [[100, 0], [220, 0], [220, 30], [100, 30]]},
        {'text': 'English text',
         'position': [[100, 40], [280, 40], [280, 70], [100, 70]]},
    ]})
    assert CnOcrOffline().run(image_file).render() == '这是中文 English text'


def test_cnocr_reports_a_missing_dependency(monkeypatch, image_file):
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == 'cnocr':
            raise ImportError('no cnocr')
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', fake_import)
    with pytest.raises(DependencyError):
        CnOcrOffline().run(image_file)


'''
Mathpix
'''


def test_mathpix_prefers_styled_latex(monkeypatch, canned, image_file):
    monkeypatch.setenv('mathpix_app_id', 'id')
    monkeypatch.setenv('mathpix_app_key', 'key')
    canned({'latex_styled': '\\frac{1}{2}', 'text': 'ignored'})
    assert MathpixFormulaOcr().run(image_file).render() == '\\frac{1}{2}'


def test_mathpix_reports_the_vendor_error(monkeypatch, canned, image_file):
    monkeypatch.setenv('mathpix_app_id', 'id')
    monkeypatch.setenv('mathpix_app_key', 'key')
    canned({'error': 'invalid credentials'})
    with pytest.raises(ApiError):
        MathpixFormulaOcr().run(image_file)


'''
ZXing
'''


def test_zxing_reports_a_missing_dependency(monkeypatch, image_file):
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name in ('cv2', 'zxingcpp'):
            raise ImportError('missing')
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', fake_import)
    from providers.zxing import ZxingQrReader
    with pytest.raises(DependencyError):
        ZxingQrReader().run(image_file)


'''
Caiyun
'''


@pytest.mark.parametrize('text, expected', [
    ('你好世界', 'zh2en'),
    ('hello world', 'auto2zh'),
    # Kanji-heavy Japanese must not be mistaken for Chinese.
    ('こんにちは', 'auto2zh'),
    ('日本語のテキスト', 'auto2zh'),
    ('한국어', 'auto2zh'),
])
def test_translation_direction(text, expected):
    assert detect_direction(text) == expected


def test_translation(monkeypatch, canned):
    monkeypatch.setenv('caiyun_token', 'token')
    canned({'target': '你好'})
    assert CaiyunTranslator().run('hello').render() == '你好'


def test_translation_joins_a_list_result(monkeypatch, canned):
    monkeypatch.setenv('caiyun_token', 'token')
    canned({'target': ['第一行', '第二行']})
    assert CaiyunTranslator().translate('two lines') == '第一行\n第二行'


def test_translation_without_a_token():
    with pytest.raises(ConfigError):
        CaiyunTranslator().run('hello')


def test_translation_of_nothing(monkeypatch):
    monkeypatch.setenv('caiyun_token', 'token')
    with pytest.raises(ApiError):
        CaiyunTranslator().run('   ')
