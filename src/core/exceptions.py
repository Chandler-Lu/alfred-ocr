'''Exception hierarchy shared by every layer.

Anything the user is allowed to see is an OcrError carrying a short, finished
sentence. main.py prints that sentence and exits 0, because Alfred and Quicker
pipe stdout straight into the clipboard and would happily paste a traceback.
'''
# -*- coding: UTF-8 -*-
from __future__ import annotations


class OcrError(Exception):
    '''Base class for every expected, user-facing failure.'''

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ConfigError(OcrError):
    '''A credential or setting is missing or malformed.'''


class NetworkError(OcrError):
    '''The remote endpoint could not be reached.'''


class ApiError(OcrError):
    '''The remote endpoint answered, but reported a failure.'''


class AuthError(ApiError):
    '''The endpoint rejected our credentials or access token.'''


class ImageError(OcrError):
    '''The input image is missing, unreadable or oversized.'''


class DependencyError(ConfigError):
    '''An optional third-party package is required but not installed.'''


class RoutingError(OcrError):
    '''No provider is registered for the requested service.'''


class EmptyResultError(OcrError):
    '''The engine ran successfully but found nothing.'''

    def __init__(self, message: str = 'Empty!') -> None:
        super().__init__(message)
