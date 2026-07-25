# -*- coding: UTF-8 -*-
import os
import sys

import pytest

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from core import (auth_manager, base_provider, config, formatter,  # noqa: E402
                  http_client, image_loader, layout, output)
from providers.baidu import client as baidu_client  # noqa: E402

# Modules that captured the settings singleton at import time.
_SETTINGS_HOLDERS = (
    (auth_manager, 'settings'),
    (base_provider, 'default_settings'),
    (baidu_client, 'settings'),
    (config, 'settings'),
    (formatter, 'settings'),
    (http_client, 'settings'),
    (image_loader, 'settings'),
    (layout, 'settings'),
    (output, 'settings'),
)


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch):
    '''Keep tests away from the developer's own credentials and config files.'''
    for name in tuple(config.CREDENTIAL_NAMES) + tuple(config.DEFAULTS):
        monkeypatch.delenv(name, raising=False)
        monkeypatch.delenv(name.upper(), raising=False)

    settings = config.Settings(config_paths=[], credential_paths=[])
    for module, attribute in _SETTINGS_HOLDERS:
        monkeypatch.setattr(module, attribute, settings)
    monkeypatch.setattr(auth_manager, 'baidu', auth_manager.BaiduAuth())
    return settings


@pytest.fixture
def image_file(tmp_path):
    path = tmp_path / 'shot.png'
    path.write_bytes(b'\x89PNG\r\n\x1a\n' + b'x' * 64)
    return image_loader.ImageFile(path=str(path))
