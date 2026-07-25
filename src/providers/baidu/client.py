'''Shared request path for the Baidu AI open platform.

All four endpoints take the same form-encoded image and answer with either a
result or an ``error_code``. A token the platform rejects is refreshed once and
the call is replayed, which used to require the user to delete a cache file.
'''
# -*- coding: UTF-8 -*-
from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from core import auth_manager, http_client
from core.config import settings
from core.exceptions import ApiError, AuthError
from core.image_loader import ImageFile
from core.output import debug


def error_code(payload: Mapping[str, Any]) -> Optional[int]:
    try:
        return int(payload['error_code'])
    except (KeyError, TypeError, ValueError):
        return None


def request(endpoint_setting: str, image: ImageFile,
            max_bytes: Optional[int] = None,
            extra: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    '''POST an image to a Baidu endpoint and return the decoded payload.'''
    url = settings.str(endpoint_setting)
    data: Dict[str, str] = {'image': image.base64(max_bytes)}
    if extra:
        data.update(extra)

    payload: Dict[str, Any] = {}
    for attempt in range(2):
        token = auth_manager.baidu.token(force_refresh=attempt > 0)
        payload = http_client.post_json(
            url,
            params={'access_token': token},
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            data=data,
        )
        code = error_code(payload)
        if code is None:
            return payload
        if code not in auth_manager.BAIDU_INVALID_TOKEN_CODES:
            raise ApiError(str(payload.get('error_msg') or 'Baidu OCR failed'))
        debug('baidu rejected the access token (%s), refreshing', code)

    raise AuthError(str(payload.get('error_msg') or 'Baidu OCR failed'))
