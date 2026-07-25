#!/usr/bin/env python3
'''Capture then OCR - the single entry point.

    python src/main.py <service> [image | text] [--json] [--copy] [--debug]

``service`` is a numeric selector (kept for the shipped Alfred and Quicker
actions), a provider name, or an Alfred keyword:

    python src/main.py 1 /tmp/shot.png
    python src/main.py baidu /tmp/shot.png
    python src/main.py oob -                 # read the image from the clipboard
    python src/main.py translate "你好"

Recognized text goes to stdout and nothing else does, because Alfred copies
stdout to the clipboard. Diagnostics go to stderr, and no failure is ever
allowed to reach the clipboard as a traceback.
'''
# -*- coding: UTF-8 -*-
from __future__ import annotations

import os
import sys
import traceback
from typing import Any, List, Optional, Sequence, Tuple

_SRC = os.path.dirname(os.path.abspath(__file__))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from core import image_loader, output  # noqa: E402
from core.base_provider import (INPUT_DIRECTORY, INPUT_IMAGE, INPUT_TEXT,  # noqa: E402
                                BaseProvider)
from core.exceptions import OcrError  # noqa: E402
from core.image_loader import ImageFile  # noqa: E402
from router import ServiceRouter  # noqa: E402

FLAGS = ('--json', '--text', '--copy', '--debug')


def usage(service_router: ServiceRouter) -> str:
    return ('Usage: main.py <service> [image | text] [--json] [--copy] [--debug]\n'
            'Services:\n' + service_router.describe())


def split_arguments(argv: Sequence[str]) -> Tuple[List[str], List[str]]:
    flags = [argument for argument in argv if argument in FLAGS]
    positional = [argument for argument in argv
                  if argument not in FLAGS and not argument.startswith('--')]
    return positional, flags


def resolve_payload(provider: BaseProvider,
                    positional: Sequence[str]) -> Optional[Any]:
    '''Turn the command line into whatever the provider expects.

    Returns None when there is nothing to do - a screenshot that vanished
    before we got to it is a normal race with the capture tool, and the right
    answer is silence rather than an error in the clipboard.
    '''
    if provider.input_kind == INPUT_IMAGE:
        source = positional[0] if positional else ''
        if not source:
            return None
        if source not in image_loader.CLIPBOARD_TOKENS and \
                not source.lower().startswith(image_loader.URL_PREFIXES) and \
                not os.path.isfile(source):
            return None
        return image_loader.load(source)
    if provider.input_kind == INPUT_DIRECTORY:
        return positional[0] if positional else ''
    if provider.input_kind == INPUT_TEXT:
        return ' '.join(positional)
    return None


def render_error(provider: Optional[BaseProvider], message: str,
                 as_json: bool, subtitle: str = '') -> str:
    if as_json or (provider is not None and provider.output_format == 'alfred'):
        return output.alfred_json([output.alfred_item(message, subtitle,
                                                      valid=False)])
    return message


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    positional, flags = split_arguments(argv)
    if '--debug' in flags:
        os.environ['debug'] = '1'
        from core import config
        config.reload()

    service_router = ServiceRouter()
    as_json = '--json' in flags

    if not positional:
        output.emit(usage(service_router))
        return 0

    service, arguments = positional[0], positional[1:]
    if not service_router.has(service):
        output.emit(render_error(None, 'Invalid API selector.', as_json))
        return 0

    provider = service_router.resolve(service)
    payload = None
    try:
        payload = resolve_payload(provider, arguments)
        if payload is None and provider.input_kind == INPUT_IMAGE:
            return 0
        text = provider.run(payload).render()
    except OcrError as error:
        output.emit(render_error(provider, error.message, as_json,
                                 ' '.join(arguments)))
        return 0
    except Exception:  # noqa: BLE001 - a traceback must never reach the clipboard
        traceback.print_exc(file=sys.stderr)
        output.emit(render_error(provider, 'Error: unexpected failure!', as_json))
        return 0
    finally:
        if isinstance(payload, ImageFile):
            payload.discard()

    if '--copy' in flags:
        output.copy_to_clipboard(text)
    if as_json or provider.output_format == 'alfred':
        text = output.alfred_json([output.alfred_item(
            text, ' '.join(arguments) or provider.summary)])
    output.emit(text)
    return 0


if __name__ == '__main__':
    sys.exit(main())

'''
 ________
< rabbit >
 --------
        \\   ^__^
         \\  (oo)\\_______
            (__)\\       )\\/\
                ||----w |
                ||     ||
'''
