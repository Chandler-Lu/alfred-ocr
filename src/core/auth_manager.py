'''Access tokens: fetch, cache on disk, refresh when rejected.

The cache records when a token was issued and how long the vendor says it
lives, instead of guessing from the file's mtime, and a corrupt or unwritable
cache degrades to a fresh request rather than an exception.
'''
# -*- coding: UTF-8 -*-
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, Optional

from core.config import settings
from core.exceptions import ApiError
from core.output import debug

# Baidu rejects a stale or revoked token with these codes.
BAIDU_INVALID_TOKEN_CODES = frozenset((110, 111))
# Refresh a day before expiry rather than fail mid-request.
REFRESH_MARGIN = 86400.0


class TokenCache:
    '''Small JSON document holding one token and its issue time.'''

    def __init__(self, filename: str) -> None:
        self.filename = filename

    @property
    def path(self) -> str:
        return settings.token_cache_path(self.filename)

    def read(self) -> Optional[Dict[str, Any]]:
        path = self.path
        try:
            with open(path, 'r', encoding='utf-8') as handle:
                payload = json.load(handle)
        except (OSError, ValueError):
            return None
        if not isinstance(payload, dict) or not payload.get('access_token'):
            return None
        payload.setdefault('issued_at', _mtime(path))
        return payload

    def write(self, payload: Dict[str, Any]) -> None:
        try:
            with open(self.path, 'w', encoding='utf-8') as handle:
                json.dump(dict(payload, issued_at=time.time()), handle)
        except OSError as error:
            # A read-only workflow directory costs us the cache, not the OCR.
            debug('token cache not writable: %s', error)

    @staticmethod
    def is_fresh(payload: Dict[str, Any], max_ttl: float) -> bool:
        try:
            issued_at = float(payload.get('issued_at') or 0.0)
        except (TypeError, ValueError):
            return False
        try:
            lifetime = float(payload.get('expires_in', max_ttl))
        except (TypeError, ValueError):
            lifetime = max_ttl
        lifetime = min(lifetime, max_ttl) - REFRESH_MARGIN
        return time.time() - issued_at < max(lifetime, 60.0)


class BaiduAuth:
    '''client_credentials flow for the Baidu AI open platform.'''

    def __init__(self) -> None:
        self.cache = TokenCache('baidu_api_token.json')
        self._token: Optional[str] = None

    def token(self, force_refresh: bool = False) -> str:
        if force_refresh:
            self._token = self.request_token()
            return self._token
        if self._token:
            return self._token

        payload = self.cache.read()
        if payload and self.cache.is_fresh(payload, settings.float('baidu_token_ttl')):
            self._token = str(payload['access_token'])
        else:
            self._token = self.request_token()
        return self._token

    def request_token(self) -> str:
        from core import http_client

        settings.require('baidu_api_key', 'baidu_secret_key')
        payload = http_client.get_json(
            settings.str('baidu_token_api'),
            params={
                'grant_type': 'client_credentials',
                'client_id': settings.credential('baidu_api_key'),
                'client_secret': settings.credential('baidu_secret_key'),
            },
        )
        token = payload.get('access_token')
        if not token:
            raise ApiError('Error: ' + str(payload.get('error_description')
                                           or payload.get('error')
                                           or 'cannot obtain Baidu token'))
        self.cache.write(payload)
        return str(token)

    def forget(self) -> None:
        self._token = None


def _mtime(path: str) -> float:
    try:
        return os.stat(path).st_mtime
    except OSError:
        return 0.0


baidu = BaiduAuth()
