# -*- coding: UTF-8 -*-
import pytest
import requests

from core import http_client
from core.exceptions import ApiError, NetworkError


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=''):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if self._payload is None:
            raise ValueError('no json')
        return self._payload


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(http_client.time, 'sleep', lambda seconds: None)


def _session(monkeypatch, responses):
    calls = []

    class FakeSession:
        def request(self, method, url, **kwargs):
            calls.append({'method': method, 'url': url, **kwargs})
            result = responses.pop(0)
            if isinstance(result, Exception):
                raise result
            return result

    monkeypatch.setattr(http_client, 'session', FakeSession)
    return calls


def test_a_timeout_is_always_passed(monkeypatch):
    calls = _session(monkeypatch, [FakeResponse(payload={'ok': 1})])
    http_client.post_json('https://example.com')
    assert calls[0]['timeout'] == 20.0


def test_connection_errors_are_retried_then_reported(monkeypatch):
    errors = [requests.exceptions.ConnectionError()] * 3
    _session(monkeypatch, errors)
    with pytest.raises(NetworkError) as error:
        http_client.get_json('https://example.com')
    assert error.value.message == 'Error: Network connection refused!'


def test_a_retry_can_succeed(monkeypatch):
    _session(monkeypatch, [requests.exceptions.ConnectionError(),
                           FakeResponse(payload={'ok': 1})])
    assert http_client.get_json('https://example.com') == {'ok': 1}


def test_timeouts_get_their_own_message(monkeypatch):
    _session(monkeypatch, [requests.exceptions.Timeout()] * 3)
    with pytest.raises(NetworkError) as error:
        http_client.get_json('https://example.com')
    assert error.value.message == 'Request timeout!'


def test_server_errors_are_retried(monkeypatch):
    calls = _session(monkeypatch, [FakeResponse(status_code=503),
                                   FakeResponse(payload={'ok': 1})])
    assert http_client.get_json('https://example.com') == {'ok': 1}
    assert len(calls) == 2


def test_a_client_error_is_not_retried(monkeypatch):
    calls = _session(monkeypatch, [FakeResponse(status_code=404, text='nope')])
    with pytest.raises(ApiError):
        http_client.get_json('https://example.com')
    assert len(calls) == 1


def test_a_non_json_body_is_an_api_error(monkeypatch):
    _session(monkeypatch, [FakeResponse(text='<html>')])
    with pytest.raises(ApiError):
        http_client.get_json('https://example.com')


def test_retries_can_be_disabled(monkeypatch):
    calls = _session(monkeypatch, [requests.exceptions.ConnectionError()])
    with pytest.raises(NetworkError):
        http_client.get_json('https://example.com', retries=0)
    assert len(calls) == 1


@pytest.mark.parametrize('value, expected', [
    ('', None),
    ('127.0.0.1:1234', {'http': 'http://127.0.0.1:1234',
                        'https': 'http://127.0.0.1:1234'}),
    ('socks5://127.0.0.1:1', {'http': 'socks5://127.0.0.1:1',
                              'https': 'socks5://127.0.0.1:1'}),
])
def test_proxy_mapping(value, expected):
    assert http_client.proxies_for(value) == expected


DEFAULT_PROXY = {'http': 'http://127.0.0.1:7890',
                 'https': 'http://127.0.0.1:7890'}


def test_the_configured_proxy_is_applied_without_being_asked_for(monkeypatch):
    calls = _session(monkeypatch, [FakeResponse(payload={'ok': 1})])
    http_client.get_json('https://example.com')
    assert calls[0]['proxies'] == DEFAULT_PROXY


def test_the_proxy_can_be_overridden_per_call(monkeypatch):
    calls = _session(monkeypatch, [FakeResponse(payload={'ok': 1})])
    http_client.get_json('https://example.com',
                         proxies={'https': 'http://10.0.0.1:1'})
    assert calls[0]['proxies'] == {'https': 'http://10.0.0.1:1'}


def test_an_empty_mapping_forces_a_direct_connection(monkeypatch):
    calls = _session(monkeypatch, [FakeResponse(payload={'ok': 1})])
    http_client.get_json('https://example.com', proxies={})
    assert calls[0]['proxies'] is None


def test_the_proxy_setting_can_be_switched_off(monkeypatch):
    monkeypatch.setattr(http_client.settings, '_file_values',
                        {'http_proxy': ''})
    calls = _session(monkeypatch, [FakeResponse(payload={'ok': 1})])
    http_client.get_json('https://example.com')
    assert calls[0]['proxies'] is None


def test_the_proxy_applies_to_downloads_too(monkeypatch, tmp_path):
    calls = _session(monkeypatch, [FakeResponse(payload={'ok': 1})])
    monkeypatch.setattr(FakeResponse, 'content', b'bytes', raising=False)
    http_client.download('https://example.com/a.png', str(tmp_path / 'a.png'))
    assert calls[0]['proxies'] == DEFAULT_PROXY


def test_every_provider_shares_the_proxy(monkeypatch, image_file):
    '''The proxy is global: it must reach engines other than Google.'''
    from core import auth_manager
    from providers.baidu import BaiduGeneralOcr
    from providers.caiyun import CaiyunTranslator
    from providers.google import GoogleGeneralOcr
    from providers.mathpix import MathpixFormulaOcr
    from providers.tencent import TencentGeneralOcr

    monkeypatch.setattr(auth_manager.baidu, 'token',
                        lambda force_refresh=False: 'placeholder-token')
    for name in ('baidu_api_key', 'baidu_secret_key', 'tencent_secret_id',
                 'tencent_secret_key', 'google_access_token', 'caiyun_token',
                 'mathpix_app_id', 'mathpix_app_key'):
        monkeypatch.setenv(name, 'placeholder')

    payloads = {
        BaiduGeneralOcr: {'words_result': [{'words': 'x'}]},
        TencentGeneralOcr: {'Response': {'TextDetections': [
            {'DetectedText': 'x'}]}},
        GoogleGeneralOcr: {'responses': [{'textAnnotations': [
            {'description': 'x'}]}]},
        MathpixFormulaOcr: {'latex_styled': 'x'},
        CaiyunTranslator: {'target': 'x'},
    }
    for provider_class, payload in payloads.items():
        calls = _session(monkeypatch, [FakeResponse(payload=payload)] * 2)
        argument = 'hello' if provider_class is CaiyunTranslator else image_file
        provider_class().run(argument)
        assert calls[-1]['proxies'] == DEFAULT_PROXY, provider_class.__name__
