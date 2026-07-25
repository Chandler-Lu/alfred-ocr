# -*- coding: UTF-8 -*-
import json

import pytest

import main
from core.base_provider import INPUT_TEXT, BaseProvider, OcrResult
from core.exceptions import ApiError, EmptyResultError
from router import ServiceRouter


class StubProvider(BaseProvider):
    name = 'stub'
    selector = 1234
    summary = 'stub provider'
    result = OcrResult.raw('recognized text')
    error = None

    def recognize(self, payload):
        if type(self).error is not None:
            raise type(self).error
        type(self).seen = payload
        return type(self).result


class StubTextProvider(BaseProvider):
    name = 'stub-text'
    summary = 'stub translator'
    input_kind = INPUT_TEXT
    output_format = 'alfred'

    def recognize(self, payload):
        return OcrResult.raw('translated: ' + str(payload))


@pytest.fixture
def stub_router(monkeypatch):
    StubProvider.error = None
    StubProvider.result = OcrResult.raw('recognized text')
    monkeypatch.setattr(
        main, 'ServiceRouter',
        lambda *args, **kwargs: ServiceRouter([StubProvider, StubTextProvider]))


def test_recognized_text_goes_to_stdout(stub_router, capsys, image_file):
    assert main.main(['stub', image_file.path]) == 0
    assert capsys.readouterr().out == 'recognized text'


def test_the_screenshot_is_deleted_afterwards(stub_router, image_file):
    import os
    main.main(['stub', image_file.path])
    assert not os.path.exists(image_file.path)


def test_the_screenshot_is_deleted_even_when_recognition_fails(stub_router,
                                                               image_file):
    import os
    StubProvider.error = ApiError('image size error')
    main.main(['stub', image_file.path])
    assert not os.path.exists(image_file.path)


def test_provider_errors_are_one_plain_line(stub_router, capsys, image_file):
    StubProvider.error = ApiError('image size error')
    main.main(['stub', image_file.path])
    assert capsys.readouterr().out == 'image size error'


def test_an_empty_result_becomes_a_message(stub_router, capsys, image_file):
    StubProvider.error = EmptyResultError()
    main.main(['stub', image_file.path])
    assert capsys.readouterr().out == 'Empty!'


def test_a_traceback_never_reaches_the_clipboard(stub_router, capsys, image_file):
    StubProvider.error = RuntimeError('boom')
    main.main(['stub', image_file.path])
    captured = capsys.readouterr()
    assert captured.out == 'Error: unexpected failure!'
    assert 'Traceback' in captured.err


def test_an_unknown_service(stub_router, capsys):
    main.main(['nope', 'x.png'])
    assert capsys.readouterr().out == 'Invalid API selector.'


def test_usage_without_arguments(stub_router, capsys):
    main.main([])
    out = capsys.readouterr().out
    assert 'Usage' in out and 'stub' in out


def test_a_vanished_screenshot_produces_silence(stub_router, capsys, tmp_path):
    main.main(['stub', str(tmp_path / 'gone.png')])
    assert capsys.readouterr().out == ''


def test_a_missing_image_argument_produces_silence(stub_router, capsys):
    main.main(['stub'])
    assert capsys.readouterr().out == ''


def test_text_providers_take_the_remaining_arguments(stub_router, capsys):
    main.main(['stub-text', '你好', '世界'])
    payload = json.loads(capsys.readouterr().out)
    assert payload['items'][0]['title'] == 'translated: 你好 世界'
    assert payload['items'][0]['text']['copy'] == 'translated: 你好 世界'


def test_json_flag_wraps_any_provider(stub_router, capsys, image_file):
    main.main(['stub', image_file.path, '--json'])
    payload = json.loads(capsys.readouterr().out)
    assert payload['items'][0]['title'] == 'recognized text'


def test_json_flag_also_wraps_errors(stub_router, capsys, image_file):
    StubProvider.error = ApiError('image size error')
    main.main(['stub', image_file.path, '--json'])
    payload = json.loads(capsys.readouterr().out)
    assert payload['items'][0]['title'] == 'image size error'
    assert payload['items'][0]['valid'] is False


def test_copy_flag(stub_router, capsys, image_file, monkeypatch):
    copied = {}
    monkeypatch.setattr(main.output, 'copy_to_clipboard',
                        lambda text: copied.setdefault('text', text) or True)
    main.main(['stub', image_file.path, '--copy'])
    assert copied['text'] == 'recognized text'


def test_the_legacy_numeric_selector_still_works(stub_router, capsys, image_file):
    main.main(['1234', image_file.path])
    assert capsys.readouterr().out == 'recognized text'


def test_split_arguments():
    positional, flags = main.split_arguments(['1', 'a.png', '--json', '--copy'])
    assert positional == ['1', 'a.png']
    assert flags == ['--json', '--copy']
