# -*- coding: UTF-8 -*-
import pytest

from core.base_provider import BaseProvider, OcrResult
from core.exceptions import RoutingError
from providers.baidu import BaiduGeneralOcr
from router import PROVIDER_CLASSES, ServiceRouter


@pytest.fixture
def router():
    return ServiceRouter()


def test_every_legacy_selector_still_resolves(router):
    selectors = {provider.selector for provider in router.providers()}
    assert {0, 1, 2, 3, 4, 5, 6, 7, 8, 99} <= selectors


@pytest.mark.parametrize('token', ['1', 'baidu', 'oob', 'BAIDU', ' baidu '])
def test_a_provider_answers_to_number_name_and_keyword(router, token):
    assert isinstance(router.resolve(token), BaiduGeneralOcr)


def test_unknown_service(router):
    with pytest.raises(RoutingError):
        router.resolve('nope')
    assert not router.has('nope')


def test_tokens_are_unique_across_providers():
    seen = {}
    for provider_class in PROVIDER_CLASSES:
        for token in provider_class().keys:
            assert token.lower() not in seen, (
                '%s clashes with %s on %r' %
                (provider_class.__name__, seen.get(token.lower()), token))
            seen[token.lower()] = provider_class.__name__


def test_registering_a_clashing_token_fails_loudly():
    class Clashing(BaseProvider):
        name = 'baidu'

        def recognize(self, payload):
            return OcrResult.raw('')

    with pytest.raises(RuntimeError):
        ServiceRouter([BaiduGeneralOcr, Clashing])


def test_a_provider_without_a_name_is_rejected():
    class Nameless(BaseProvider):
        def recognize(self, payload):
            return OcrResult.raw('')

    with pytest.raises(RuntimeError):
        ServiceRouter([Nameless])


def test_router_can_be_built_from_a_custom_set():
    router = ServiceRouter([BaiduGeneralOcr])
    assert len(router.providers()) == 1
    assert router.has('oob')
    assert not router.has('tencent')


def test_describe_lists_selectors_and_keywords(router):
    text = router.describe()
    assert 'baidu' in text
    assert 'translate' in text
    assert '99' in text


def test_every_provider_declares_its_metadata(router):
    for provider in router.providers():
        assert provider.name
        assert provider.summary
        assert provider.input_kind in ('image', 'directory', 'text', 'none')
