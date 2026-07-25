# -*- coding: UTF-8 -*-
import json
import time

import pytest

from core import auth_manager, http_client
from core.auth_manager import BaiduAuth, TokenCache
from core.exceptions import ApiError, ConfigError


@pytest.fixture
def cache_in(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path / 'baidu_api_token.json'


@pytest.fixture
def credentials(monkeypatch):
    monkeypatch.setenv('baidu_api_key', 'key')
    monkeypatch.setenv('baidu_secret_key', 'secret')


def test_a_fresh_cache_is_reused(cache_in, credentials, monkeypatch):
    cache_in.write_text(json.dumps({'access_token': 'cached',
                                    'expires_in': 2592000,
                                    'issued_at': time.time()}), encoding='utf-8')
    monkeypatch.setattr(http_client, 'get_json', _explode)
    assert BaiduAuth().token() == 'cached'


def test_an_expired_cache_is_refreshed(cache_in, credentials, monkeypatch):
    cache_in.write_text(json.dumps({'access_token': 'old',
                                    'expires_in': 2592000,
                                    'issued_at': time.time() - 40 * 86400}),
                        encoding='utf-8')
    monkeypatch.setattr(http_client, 'get_json',
                        lambda *args, **kwargs: {'access_token': 'new',
                                                 'expires_in': 2592000})
    assert BaiduAuth().token() == 'new'
    assert json.loads(cache_in.read_text(encoding='utf-8'))['access_token'] == 'new'


def test_a_corrupt_cache_is_replaced(cache_in, credentials, monkeypatch):
    cache_in.write_text('{ not json', encoding='utf-8')
    monkeypatch.setattr(http_client, 'get_json',
                        lambda *args, **kwargs: {'access_token': 'new'})
    assert BaiduAuth().token() == 'new'


def test_a_cache_without_a_token_is_replaced(cache_in, credentials, monkeypatch):
    cache_in.write_text(json.dumps({'error': 'nope'}), encoding='utf-8')
    monkeypatch.setattr(http_client, 'get_json',
                        lambda *args, **kwargs: {'access_token': 'new'})
    assert BaiduAuth().token() == 'new'


def test_the_token_is_only_fetched_once_per_process(cache_in, credentials,
                                                    monkeypatch):
    calls = []

    def fake_get(*args, **kwargs):
        calls.append(1)
        return {'access_token': 'new'}

    monkeypatch.setattr(http_client, 'get_json', fake_get)
    auth = BaiduAuth()
    assert auth.token() == auth.token() == 'new'
    assert len(calls) == 1


def test_force_refresh_asks_again(cache_in, credentials, monkeypatch):
    tokens = iter(['first', 'second'])
    monkeypatch.setattr(http_client, 'get_json',
                        lambda *args, **kwargs: {'access_token': next(tokens)})
    auth = BaiduAuth()
    assert auth.token() == 'first'
    assert auth.token(force_refresh=True) == 'second'


def test_missing_credentials_are_reported(cache_in):
    with pytest.raises(ConfigError):
        BaiduAuth().token()


def test_a_rejected_key_reports_the_vendor_message(cache_in, credentials,
                                                   monkeypatch):
    monkeypatch.setattr(http_client, 'get_json',
                        lambda *args, **kwargs: {
                            'error': 'invalid_client',
                            'error_description': 'unknown client id'})
    with pytest.raises(ApiError) as error:
        BaiduAuth().token()
    assert 'unknown client id' in error.value.message


def test_an_unwritable_cache_does_not_break_recognition(credentials, monkeypatch):
    monkeypatch.setattr(http_client, 'get_json',
                        lambda *args, **kwargs: {'access_token': 'new'})
    monkeypatch.setattr('builtins.open', _explode_open)
    assert BaiduAuth().token() == 'new'


def test_freshness_uses_the_shorter_of_vendor_ttl_and_setting():
    now = time.time()
    assert TokenCache.is_fresh({'access_token': 't', 'issued_at': now,
                                'expires_in': 2592000}, 2160000)
    assert not TokenCache.is_fresh({'access_token': 't', 'issued_at': now - 100,
                                    'expires_in': 60}, 2160000)


def test_freshness_of_rubbish():
    assert not TokenCache.is_fresh({'issued_at': 'yesterday'}, 100.0)


def test_the_module_singleton_exists():
    assert isinstance(auth_manager.baidu, BaiduAuth)
    assert auth_manager.BAIDU_INVALID_TOKEN_CODES == frozenset((110, 111))


def _explode(*args, **kwargs):
    raise AssertionError('the network was used when it should not have been')


def _explode_open(*args, **kwargs):
    raise OSError('read-only file system')
