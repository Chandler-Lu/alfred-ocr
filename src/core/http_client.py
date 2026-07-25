'''HTTP plumbing shared by every online provider.

Supplies the three things the old per-provider try/except blocks lacked: a
timeout (Alfred otherwise hangs forever on a dropped connection), a retry for
transient failures, and one place that turns requests' exception zoo into an
OcrError.
'''
# -*- coding: UTF-8 -*-
from __future__ import annotations

import time
from typing import Any, Dict, Mapping, Optional

import requests

from core.config import settings
from core.exceptions import ApiError, NetworkError
from core.output import debug

RETRY_STATUS = frozenset((429, 500, 502, 503, 504))

_session: Optional[requests.Session] = None


def session() -> requests.Session:
    global _session
    if _session is None:
        _session = requests.Session()
    return _session


def proxies_for(host_port: str) -> Optional[Dict[str, str]]:
    '''Build a requests proxy mapping from a bare ``host:port`` setting.'''
    if not host_port:
        return None
    if '://' in host_port:
        return {'http': host_port, 'https': host_port}
    return {'http': 'http://' + host_port, 'https': 'http://' + host_port}


def default_proxies() -> Optional[Dict[str, str]]:
    '''The globally configured proxy, shared by every provider.'''
    return proxies_for(settings.str('http_proxy'))


def request(method: str,
            url: str,
            *,
            params: Optional[Mapping[str, Any]] = None,
            headers: Optional[Mapping[str, str]] = None,
            data: Any = None,
            json_body: Any = None,
            files: Any = None,
            timeout: Optional[float] = None,
            retries: Optional[int] = None,
            proxies: Optional[Mapping[str, str]] = None) -> requests.Response:
    '''Perform a request, retrying transient failures.

    ``data`` and ``files`` must be re-sendable - bytes or plain dicts, not open
    file objects - because a retry replays them.

    ``proxies`` left as None means "use the globally configured proxy"; pass an
    empty mapping to force a direct connection for one call.
    '''
    attempts = max(0, settings.int('http_retries') if retries is None else retries) + 1
    wait = settings.float('http_timeout') if timeout is None else timeout
    resolved_proxies = (default_proxies() if proxies is None
                        else (dict(proxies) or None))
    last_error: Optional[BaseException] = None

    for attempt in range(attempts):
        if attempt:
            time.sleep(min(0.4 * (2 ** (attempt - 1)), 2.0))
        try:
            response = session().request(
                method, url,
                params=params, headers=headers, data=data, json=json_body,
                files=files, timeout=wait,
                proxies=resolved_proxies,
            )
        except requests.exceptions.Timeout as error:
            last_error = error
            continue
        except requests.exceptions.ConnectionError as error:
            last_error = error
            continue
        except requests.exceptions.RequestException as error:
            raise NetworkError('Request failed!') from error

        if response.status_code in RETRY_STATUS and attempt < attempts - 1:
            debug('HTTP %s from %s, retrying', response.status_code, url)
            continue
        return response

    if isinstance(last_error, requests.exceptions.Timeout):
        raise NetworkError('Request timeout!') from last_error
    raise NetworkError('Error: Network connection refused!') from last_error


def request_json(method: str, url: str, **kwargs: Any) -> Dict[str, Any]:
    '''Like :func:`request`, but insists on a 200 with a JSON object body.'''
    response = request(method, url, **kwargs)
    if response.status_code != 200:
        debug('HTTP %s %s -> %s: %s', method, url, response.status_code,
              response.text[:400])
        raise ApiError('Request failed!')
    try:
        payload = response.json()
    except ValueError as error:
        debug('non-JSON body from %s: %s', url, response.text[:400])
        raise ApiError('Request failed!') from error
    if not isinstance(payload, dict):
        raise ApiError('Request failed!')
    return payload


def post_json(url: str, **kwargs: Any) -> Dict[str, Any]:
    return request_json('POST', url, **kwargs)


def get_json(url: str, **kwargs: Any) -> Dict[str, Any]:
    return request_json('GET', url, **kwargs)


def download(url: str, destination: str, timeout: Optional[float] = None) -> str:
    '''Fetch a remote image to ``destination`` and return the path.'''
    response = request('GET', url, timeout=timeout)
    if response.status_code != 200:
        raise ApiError('Request failed!')
    with open(destination, 'wb') as handle:
        handle.write(response.content)
    return destination
