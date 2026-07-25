'''Unified configuration: defaults, config file, environment.

Resolution order, highest priority first:

    1. environment variable - ``baidu_api_key`` or ``BAIDU_API_KEY``
    2. credentials.json (credentials only)
    3. config/user.yaml, ~/.config/alfred-ocr/config.yaml
    4. config/default.yaml
    5. the DEFAULTS table below

Values are coerced to the type of their default, so ``paragraph_gap_ratio``
always arrives as a float no matter where it came from. A missing credential is
an empty string, never a KeyError: one unconfigured provider must not stop the
other eight from working.
'''
# -*- coding: UTF-8 -*-
from __future__ import annotations

import json
import os
import platform
import re
import tempfile
from typing import Any, Dict, Iterable, List, Mapping, Optional

from core.exceptions import ConfigError

IS_WINDOWS = platform.system() == 'Windows'
IS_MACOS = platform.system() == 'Darwin'

PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(PACKAGE_ROOT)
CONFIG_DIR = os.path.join(PROJECT_ROOT, 'config')
USER_CONFIG_DIR = os.path.expanduser('~/.config/alfred-ocr')

CREDENTIAL_NAMES = (
    'baidu_api_key',
    'baidu_secret_key',
    'tencent_secret_id',
    'tencent_secret_key',
    'google_access_token',
    'google_post_referer',
    'caiyun_token',
    'mathpix_app_id',
    'mathpix_app_key',
)

# Quicker on Windows has no per-action environment variables. Fill these in, or
# better, drop the same keys into credentials.json, which git ignores.
INLINE_CREDENTIALS: Dict[str, str] = {name: '' for name in CREDENTIAL_NAMES}

DEFAULTS: Dict[str, Any] = {
    # --- endpoints -------------------------------------------------------
    'baidu_token_api': 'https://aip.baidubce.com/oauth/2.0/token',
    'baidu_ocr_api': 'https://aip.baidubce.com/rest/2.0/ocr/v1/general',
    'baidu_qrcode_api': 'https://aip.baidubce.com/rest/2.0/ocr/v1/qrcode',
    'baidu_table_api': 'https://aip.baidubce.com/rest/2.0/ocr/v1/table',
    'baidu_formula_api': 'https://aip.baidubce.com/rest/2.0/ocr/v1/formula',
    'tencent_ocr_api': 'https://ocr.tencentcloudapi.com',
    'tencent_ocr_host': 'ocr.tencentcloudapi.com',
    'google_ocr_api': 'https://vision.googleapis.com/v1/images:annotate',
    'mathpix_api': 'https://api.mathpix.com/v3/text',
    'caiyun_translate_api': 'http://api.interpreter.caiyunai.com/v1/translator',
    'cnocr_api': 'http://127.0.0.1:8501/ocr',

    # --- http ------------------------------------------------------------
    'http_timeout': 20.0,
    'http_retries': 2,
    'cnocr_timeout': 1.5,
    # Proxy for every outbound request, as "host:port" or a full URL. Some
    # engines are unreachable from parts of the world without one. Set it to an
    # empty string in a config file to connect directly.
    'http_proxy': '127.0.0.1:7890',

    # --- providers -------------------------------------------------------
    'baidu_language_type': 'CHN_ENG',
    'baidu_token_ttl': 25 * 24 * 3600,
    'baidu_max_image_bytes': 4 * 1024 * 1024,
    'baidu_table_max_image_bytes': 8 * 1024 * 1024,
    'tencent_max_image_bytes': 3 * 1024 * 1024,
    'tencent_action': 'GeneralFastOCR',
    'tencent_region': 'ap-shanghai',
    'tencent_version': '2018-11-19',
    'cnocr_serve': 0,
    'cnocr_rec_model': 'doc-densenet_lite_136-gru',
    'cnocr_det_model': 'ch_PP-OCRv3_det',
    'multi_file_path': '/private/tmp/com.chandler.alfredocr',

    # --- text clean-up ---------------------------------------------------
    'text_add_cjk_latin_space': True,
    'text_normalize_punctuation': True,
    'text_fold_fullwidth_ascii': False,

    # --- paragraph reconstruction ---------------------------------------
    # Thresholds are ratios of measured page metrics (line pitch, character
    # width), so the same numbers work for a Retina screenshot and a scan.
    'paragraph_enabled': True,
    'paragraph_gap_ratio': 1.45,
    'paragraph_short_line_chars': 3.0,
    'paragraph_latin_short_factor': 1.6,
    'paragraph_indent_chars': 1.2,
    'paragraph_height_tolerance': 0.3,
    'paragraph_break_threshold': 1.0,
    # Legacy pixel nudges, kept so existing workflow variables keep working.
    'baidu_ocr_spacing_offset': 8,
    'baidu_ocr_spacing_variance': 15,
    'baidu_ocr_width_offset': 50,

    # --- misc ------------------------------------------------------------
    'image_extensions': '.png,.jpg,.jpeg,.bmp,.webp,.tiff',
    'debug': False,
}

_TRUE = ('1', 'true', 'yes', 'on')
_FLAT_ENTRY_RE = re.compile(r'^([A-Za-z_][A-Za-z0-9_.\-]*)\s*:(?:\s+(.*))?$')


def _parse_scalar(raw: str) -> Any:
    text = raw.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ('"', "'"):
        return text[1:-1]
    return text


def parse_flat_yaml(content: str) -> Dict[str, Any]:
    '''Parse the ``key: value`` subset used by config files.

    Used when PyYAML is not installed, which is the normal case for an Alfred
    workflow: the configuration is deliberately flat so that no dependency is
    needed to read it. The key must look like an identifier, so a colon inside
    a value - ``cnocr_api: http://127.0.0.1:8501/ocr`` - is left alone.
    '''
    values: Dict[str, Any] = {}
    for line in content.splitlines():
        if line[:1] in (' ', '\t'):
            continue  # nested block: only PyYAML understands those
        match = _FLAT_ENTRY_RE.match(line.strip())
        if not match:
            continue
        if match.group(2) is None:
            # "key:" with nothing after it, exactly as PyYAML reads it.
            values[match.group(1)] = None
            continue
        values[match.group(1)] = _parse_scalar(match.group(2).split(' #')[0])
    return values


def load_config_file(path: str) -> Dict[str, Any]:
    try:
        with open(path, 'r', encoding='utf-8') as handle:
            content = handle.read()
    except OSError:
        return {}
    if path.endswith('.json'):
        try:
            data = json.loads(content)
        except ValueError:
            return {}
        return data if isinstance(data, dict) else {}
    try:
        import yaml  # optional dependency
    except ImportError:
        return parse_flat_yaml(content)
    try:
        data = yaml.safe_load(content)
    except Exception:  # noqa: BLE001 - a broken config must not crash the OCR
        return {}
    return data if isinstance(data, dict) else {}


class Settings:
    '''Read-only view over defaults, config files and the environment.'''

    def __init__(self, environ: Optional[Mapping[str, str]] = None,
                 config_paths: Optional[Iterable[str]] = None,
                 credential_paths: Optional[Iterable[str]] = None) -> None:
        self._environ = os.environ if environ is None else environ
        self._config_paths = list(config_paths if config_paths is not None
                                  else self.default_config_paths())
        self._credential_paths = list(
            credential_paths if credential_paths is not None
            else self.default_credential_paths())
        self._file_values: Dict[str, Any] = {}
        self._file_credentials: Dict[str, str] = {}
        self.reload()

    @staticmethod
    def default_config_paths() -> List[str]:
        return [
            os.environ.get('alfred_ocr_config', ''),
            os.path.join(CONFIG_DIR, 'user.yaml'),
            os.path.join(USER_CONFIG_DIR, 'config.yaml'),
            os.path.join(CONFIG_DIR, 'default.yaml'),
        ]

    @staticmethod
    def default_credential_paths() -> List[str]:
        return [
            os.environ.get('alfred_ocr_credentials', ''),
            os.path.join(CONFIG_DIR, 'credentials.json'),
            os.path.join(USER_CONFIG_DIR, 'credentials.json'),
        ]

    def reload(self) -> None:
        self._file_values = {}
        for path in self._config_paths:
            if not path or not os.path.isfile(path):
                continue
            for key, value in load_config_file(path).items():
                # Earlier paths win, so only fill what is still missing.
                self._file_values.setdefault(str(key), value)

        self._file_credentials = {}
        for path in self._credential_paths:
            if not path or not os.path.isfile(path):
                continue
            for key, value in load_config_file(path).items():
                if value is not None:
                    self._file_credentials.setdefault(str(key), str(value))

    def _raw(self, name: str) -> Optional[Any]:
        # An empty environment variable means "unset", because Alfred exports
        # every workflow variable whether or not the user filled it in, and an
        # untouched field must not wipe out a default.
        for key in (name, name.upper()):
            value = self._environ.get(key)
            if value not in (None, ''):
                return value
        # An empty value in a config file is deliberate - somebody typed it -
        # and is the way to switch off a non-empty default such as the proxy.
        if name in self._file_values:
            value = self._file_values[name]
            if value is not None:
                return value
        return None

    def get(self, name: str, default: Any = None) -> Any:
        fallback = DEFAULTS.get(name, default)
        raw = self._raw(name)
        if raw is None:
            return fallback
        return _coerce(raw, fallback)

    def str(self, name: str, default: str = '') -> str:
        return str(self.get(name, default))

    def int(self, name: str, default: int = 0) -> int:
        return int(self.get(name, default))

    def float(self, name: str, default: float = 0.0) -> float:
        return float(self.get(name, default))

    def bool(self, name: str, default: bool = False) -> bool:
        return bool(self.get(name, default))

    def list(self, name: str) -> List[str]:
        value = self.get(name, '')
        if isinstance(value, (list, tuple)):
            return [str(item).strip() for item in value if str(item).strip()]
        return [item.strip() for item in str(value).split(',') if item.strip()]

    def credential(self, name: str) -> str:
        raw = self._raw(name)
        if raw:
            return str(raw).strip()
        return (self._file_credentials.get(name, '')
                or INLINE_CREDENTIALS.get(name, '')).strip()

    def require(self, *names: str) -> None:
        '''Fail with a readable message instead of a 401 from the vendor.'''
        missing = [name for name in names if not self.credential(name)]
        if missing:
            raise ConfigError('Error: missing credential(s): ' + ', '.join(missing))

    @property
    def debug(self) -> bool:
        return self.bool('debug')

    def token_cache_path(self, filename: str = 'baidu_api_token.json') -> str:
        '''First writable location for a cached access token.

        The historical location (``./baidu_api_token.json``) wins when it
        already exists, so an upgrade does not force a needless token request.
        '''
        candidates = [
            self.str('token_cache_path', ''),
            os.path.join(os.getcwd(), filename),
            os.path.join(USER_CONFIG_DIR, filename),
            os.path.join(PACKAGE_ROOT, filename),
            os.path.join(tempfile.gettempdir(), 'com.chandler.alfredocr.' + filename),
        ]
        fallback: Optional[str] = None
        for path in candidates:
            if not path:
                continue
            if os.path.isfile(path):
                return path
            directory = os.path.dirname(path) or '.'
            if fallback is None and os.path.isdir(directory) \
                    and os.access(directory, os.W_OK):
                fallback = path
        return fallback or candidates[-1]


def _coerce(raw: Any, fallback: Any) -> Any:
    if isinstance(fallback, bool):
        if isinstance(raw, bool):
            return raw
        return str(raw).strip().lower() in _TRUE
    if isinstance(fallback, int) and not isinstance(fallback, bool):
        try:
            return int(float(str(raw).strip()))
        except ValueError:
            return fallback
    if isinstance(fallback, float):
        try:
            return float(str(raw).strip())
        except ValueError:
            return fallback
    if isinstance(fallback, (list, tuple)) and isinstance(raw, str):
        return [item.strip() for item in raw.split(',') if item.strip()]
    return raw if not isinstance(raw, str) else raw.strip()


settings = Settings()


def reload() -> None:
    '''Re-read configuration; used by tests and long-running processes.'''
    settings.reload()
