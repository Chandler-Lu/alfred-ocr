# -*- coding: UTF-8 -*-
import json

import pytest

from core import config
from core.config import Settings, parse_flat_yaml
from core.exceptions import ConfigError


def test_defaults_are_typed():
    settings = Settings(environ={}, config_paths=[], credential_paths=[])
    assert isinstance(settings.get('http_timeout'), float)
    assert isinstance(settings.get('http_retries'), int)
    assert isinstance(settings.get('paragraph_enabled'), bool)
    assert settings.str('baidu_language_type') == 'CHN_ENG'


def test_environment_wins_and_is_coerced():
    settings = Settings(environ={'http_retries': '5', 'paragraph_gap_ratio': '2.5'},
                        config_paths=[], credential_paths=[])
    assert settings.int('http_retries') == 5
    assert settings.float('paragraph_gap_ratio') == 2.5


def test_uppercase_environment_variables_work():
    settings = Settings(environ={'BAIDU_LANGUAGE_TYPE': 'ENG'},
                        config_paths=[], credential_paths=[])
    assert settings.str('baidu_language_type') == 'ENG'


def test_rubbish_in_the_environment_falls_back_to_the_default():
    settings = Settings(environ={'http_timeout': 'soon'},
                        config_paths=[], credential_paths=[])
    assert settings.float('http_timeout') == config.DEFAULTS['http_timeout']


@pytest.mark.parametrize('raw, expected', [
    ('1', True), ('true', True), ('YES', True), ('on', True),
    ('0', False), ('false', False), ('no', False),
])
def test_boolean_parsing(raw, expected):
    settings = Settings(environ={'paragraph_enabled': raw},
                        config_paths=[], credential_paths=[])
    assert settings.bool('paragraph_enabled') is expected


def test_missing_credentials_never_raise_on_import():
    settings = Settings(environ={}, config_paths=[], credential_paths=[])
    assert settings.credential('baidu_api_key') == ''


def test_require_names_the_missing_credentials():
    settings = Settings(environ={'baidu_api_key': 'k'},
                        config_paths=[], credential_paths=[])
    settings.require('baidu_api_key')
    with pytest.raises(ConfigError) as error:
        settings.require('baidu_api_key', 'baidu_secret_key', 'caiyun_token')
    assert 'baidu_secret_key' in error.value.message
    assert 'caiyun_token' in error.value.message
    assert 'baidu_api_key' not in error.value.message


def test_credentials_file(tmp_path):
    path = tmp_path / 'credentials.json'
    path.write_text(json.dumps({'baidu_api_key': 'from-file'}), encoding='utf-8')
    settings = Settings(environ={}, config_paths=[], credential_paths=[str(path)])
    assert settings.credential('baidu_api_key') == 'from-file'


def test_environment_beats_the_credentials_file(tmp_path):
    path = tmp_path / 'credentials.json'
    path.write_text(json.dumps({'baidu_api_key': 'from-file'}), encoding='utf-8')
    settings = Settings(environ={'baidu_api_key': 'from-env'},
                        config_paths=[], credential_paths=[str(path)])
    assert settings.credential('baidu_api_key') == 'from-env'


def test_config_file_is_read_and_earlier_paths_win(tmp_path):
    high = tmp_path / 'user.yaml'
    low = tmp_path / 'default.yaml'
    high.write_text('paragraph_gap_ratio: 3.0\n', encoding='utf-8')
    low.write_text('paragraph_gap_ratio: 1.1\nhttp_retries: 7\n', encoding='utf-8')
    settings = Settings(environ={}, config_paths=[str(high), str(low)],
                        credential_paths=[])
    assert settings.float('paragraph_gap_ratio') == 3.0
    assert settings.int('http_retries') == 7


def test_a_broken_config_file_is_ignored(tmp_path):
    path = tmp_path / 'user.json'
    path.write_text('{not json', encoding='utf-8')
    settings = Settings(environ={}, config_paths=[str(path)], credential_paths=[])
    assert settings.float('paragraph_gap_ratio') == \
        config.DEFAULTS['paragraph_gap_ratio']


def test_flat_yaml_parser():
    parsed = parse_flat_yaml(
        '# comment\n'
        'name: value  # trailing\n'
        'quoted: "spaced value"\n'
        'number: 42\n'
        'nested:\n'
        '  ignored: 1\n'
        'bad line\n')
    assert parsed == {'name': 'value', 'quoted': 'spaced value',
                      'number': '42', 'nested': None}


def test_an_empty_environment_variable_does_not_wipe_a_default():
    # Alfred exports every workflow variable, filled in or not.
    settings = Settings(environ={'http_proxy': ''},
                        config_paths=[], credential_paths=[])
    assert settings.str('http_proxy') == config.DEFAULTS['http_proxy']


def test_an_empty_config_file_value_switches_a_default_off(tmp_path):
    path = tmp_path / 'user.yaml'
    path.write_text('http_proxy: ""\n', encoding='utf-8')
    settings = Settings(environ={}, config_paths=[str(path)],
                        credential_paths=[])
    assert settings.str('http_proxy') == ''


def test_a_key_with_no_value_leaves_the_default_alone(tmp_path):
    path = tmp_path / 'user.yaml'
    path.write_text('http_proxy:\n', encoding='utf-8')
    settings = Settings(environ={}, config_paths=[str(path)],
                        credential_paths=[])
    assert settings.str('http_proxy') == config.DEFAULTS['http_proxy']


def test_the_proxy_is_a_setting_not_a_credential():
    # It lives in default.yaml, so it must not be demanded as a credential.
    assert 'http_proxy' not in config.CREDENTIAL_NAMES
    assert 'http_proxy' in config.DEFAULTS
    assert not any('proxy' in name for name in config.CREDENTIAL_NAMES)


def test_the_proxy_can_be_set_per_machine_in_the_environment():
    settings = Settings(environ={'http_proxy': '10.0.0.1:8080'},
                        config_paths=[], credential_paths=[])
    assert settings.str('http_proxy') == '10.0.0.1:8080'


def test_flat_yaml_parser_keeps_colons_inside_values():
    parsed = parse_flat_yaml('cnocr_api: http://127.0.0.1:8501/ocr\n')
    assert parsed == {'cnocr_api': 'http://127.0.0.1:8501/ocr'}


def _default_yaml_path():
    import os
    path = os.path.join(config.CONFIG_DIR, 'default.yaml')
    if not os.path.isfile(path):
        pytest.skip('no default.yaml shipped')
    return path


def test_shipped_default_yaml_only_uses_known_keys():
    for key in config.load_config_file(_default_yaml_path()):
        assert key in config.DEFAULTS, 'unknown setting in default.yaml: ' + key


def test_shipped_default_yaml_matches_the_builtin_defaults():
    path = _default_yaml_path()
    settings = Settings(environ={}, config_paths=[path], credential_paths=[])
    for key, value in config.load_config_file(path).items():
        assert settings.get(key) == config.DEFAULTS[key], \
            'default.yaml disagrees with DEFAULTS for ' + key


def test_the_builtin_reader_agrees_with_pyyaml():
    # Most Alfred installs have no PyYAML, so the fallback must read the
    # shipped file the same way.
    yaml = pytest.importorskip('yaml')
    path = _default_yaml_path()
    with open(path, 'r', encoding='utf-8') as handle:
        content = handle.read()
    from_pyyaml = yaml.safe_load(content)
    from_fallback = parse_flat_yaml(content)
    assert set(from_pyyaml) == set(from_fallback)
    for key, value in from_pyyaml.items():
        assert config._coerce(from_fallback[key], config.DEFAULTS[key]) == \
            config._coerce(value, config.DEFAULTS[key]), key


def test_list_setting():
    settings = Settings(environ={'image_extensions': '.png, .gif'},
                        config_paths=[], credential_paths=[])
    assert settings.list('image_extensions') == ['.png', '.gif']


def test_token_cache_path_is_writable(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    settings = Settings(environ={}, config_paths=[], credential_paths=[])
    path = settings.token_cache_path()
    with open(path, 'w', encoding='utf-8') as handle:
        handle.write('{}')
    assert settings.token_cache_path() == path
