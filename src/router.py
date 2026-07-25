'''ServiceRouter: keyword or numeric selector -> provider instance.

The shipped Alfred and Quicker actions call this program with a number, so the
numeric selectors are part of the contract and are kept. Names and Alfred
keywords resolve to the same providers, which makes the actions readable:

    python src/main.py 1 shot.png
    python src/main.py baidu shot.png
    python src/main.py oob shot.png
'''
# -*- coding: UTF-8 -*-
from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Type

from core.base_provider import BaseProvider
from core.config import Settings
from core.exceptions import RoutingError
from providers.baidu import (BaiduFormulaOcr, BaiduGeneralOcr, BaiduMultiFileOcr,
                             BaiduQrReader, BaiduTableOcr)
from providers.caiyun import CaiyunTranslator
from providers.cnocr import CnOcrOffline
from providers.google import GoogleGeneralOcr
from providers.mathpix import MathpixFormulaOcr
from providers.tencent import TencentGeneralOcr
from providers.zxing import ZxingQrReader

# The registry. A new engine is one entry here plus its module.
PROVIDER_CLASSES: List[Type[BaseProvider]] = [
    CnOcrOffline,          # 0
    BaiduGeneralOcr,       # 1
    BaiduQrReader,         # 2
    BaiduTableOcr,         # 3
    TencentGeneralOcr,     # 4
    GoogleGeneralOcr,      # 5
    ZxingQrReader,         # 6
    MathpixFormulaOcr,     # 7
    BaiduFormulaOcr,       # 8
    BaiduMultiFileOcr,     # 99
    CaiyunTranslator,      # translate
]


class ServiceRouter:
    def __init__(self, provider_classes: Optional[Iterable[Type[BaseProvider]]] = None,
                 settings: Optional[Settings] = None) -> None:
        self.settings = settings
        self._by_token: Dict[str, Type[BaseProvider]] = {}
        self._registered: List[Type[BaseProvider]] = []
        for provider_class in (PROVIDER_CLASSES if provider_classes is None
                               else provider_classes):
            self.register(provider_class)

    def register(self, provider_class: Type[BaseProvider]) -> None:
        provider = provider_class(self.settings)
        if not provider.name:
            raise RuntimeError('%s has no name' % provider_class.__name__)
        for token in provider.keys:
            key = token.strip().lower()
            if key in self._by_token:
                raise RuntimeError(
                    'duplicate service token %r: %s and %s' % (
                        key, self._by_token[key].__name__, provider_class.__name__))
            self._by_token[key] = provider_class
        self._registered.append(provider_class)

    def resolve(self, token: str) -> BaseProvider:
        provider_class = self._by_token.get(str(token).strip().lower())
        if provider_class is None:
            raise RoutingError('Invalid API selector.')
        return provider_class(self.settings)

    def has(self, token: str) -> bool:
        return str(token).strip().lower() in self._by_token

    def providers(self) -> List[BaseProvider]:
        return [provider_class(self.settings)
                for provider_class in self._registered]

    def describe(self) -> str:
        rows = []
        for provider in self.providers():
            selector = '' if provider.selector is None else str(provider.selector)
            names = ', '.join([provider.name, *provider.aliases])
            rows.append('  %-4s %-46s %s' % (selector, names, provider.summary))
        return '\n'.join(rows)


router = ServiceRouter()
