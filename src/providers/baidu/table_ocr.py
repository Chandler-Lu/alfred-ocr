'''Baidu table recognition, emitted as TSV so it pastes into Excel.'''
# -*- coding: UTF-8 -*-
from __future__ import annotations

from typing import Any, Mapping, Sequence

from core.base_provider import BaseProvider, OcrResult
from core.formatter import format_text
from core.image_loader import ImageFile
from providers.baidu import client


def to_tsv(body: Sequence[Mapping[str, Any]]) -> str:
    '''Lay the cells out on a grid and join them with tabs.'''
    cells = [cell for cell in body
             if isinstance(cell.get('row_start'), int)
             and isinstance(cell.get('col_start'), int)]
    if not cells:
        return ''
    rows = max(cell['row_start'] for cell in cells) + 1
    columns = max(cell['col_start'] for cell in cells) + 1
    grid = [[''] * columns for _ in range(rows)]
    for cell in cells:
        # A newline or tab inside a cell would shift every later column.
        text = str(cell.get('words', '')).replace('\n', ' ').replace('\t', ' ')
        grid[cell['row_start']][cell['col_start']] = format_text(text)
    return '\n'.join('\t'.join(row) for row in grid)


class BaiduTableOcr(BaseProvider):
    name = 'baidu-table'
    aliases = ('table', 'ooe')
    selector = 3
    summary = 'Baidu table recognition (tab separated, paste into Excel)'
    required_credentials = ('baidu_api_key', 'baidu_secret_key')
    max_bytes_setting = 'baidu_table_max_image_bytes'

    def recognize(self, payload: ImageFile) -> OcrResult:
        response = client.request('baidu_table_api', payload, self.max_bytes)
        tables = [to_tsv(table.get('body') or [])
                  for table in response.get('tables_result') or []]
        return OcrResult.raw(
            '\n\n'.join(table for table in tables if table)).or_raise()
