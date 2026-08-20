"""Fetch and prepare real product-page text for specification extraction."""

from __future__ import annotations

import re
from html import unescape
from html.parser import HTMLParser
from typing import Any

import httpx

from app.utils.logger import get_logger

logger = get_logger("DocumentProcessor")


class _ProductPageParser(HTMLParser):
    """Keep useful text and turn HTML specification-table rows into `key: value`."""

    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.description = ""
        self._in_title = False
        self._in_text_block = False
        self._in_row = False
        self._in_cell = False
        self._cell_text = ""
        self._row_cells: list[str] = []
        self.lines: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "title":
            self._in_title = True
        elif tag == "meta" and attributes.get("name", "").lower() == "description":
            self.description = attributes.get("content", "") or ""
        elif tag == "tr":
            self._in_row = True
            self._row_cells = []
        elif tag in {"td", "th"} and self._in_row:
            self._in_cell = True
            self._cell_text = ""
        elif tag in {"p", "li", "h1", "h2", "h3"}:
            self._cell_text = ""
            self._in_text_block = True

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
        if self._in_cell or self._in_text_block:
            self._cell_text += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        elif tag in {"td", "th"} and self._in_cell:
            cell = self._clean(self._cell_text)
            if cell:
                self._row_cells.append(cell)
            self._in_cell = False
        elif tag == "tr":
            if len(self._row_cells) >= 2:
                self.lines.append(f"{self._row_cells[0]}: {' '.join(self._row_cells[1:])}")
            self._in_row = False
        elif tag in {"p", "li", "h1", "h2", "h3"} and self._in_text_block:
            line = self._clean(self._cell_text)
            if 3 <= len(line) <= 500:
                self.lines.append(line)
            self._in_text_block = False

    @staticmethod
    def _clean(value: str) -> str:
        return re.sub(r"\s+", " ", unescape(value)).strip()

    def text(self) -> str:
        useful_lines: list[str] = []
        for line in [self.title, self.description, *self.lines]:
            cleaned = self._clean(line)
            if cleaned and cleaned not in useful_lines:
                useful_lines.append(cleaned)
        return "\n".join(useful_lines[:250])


class DocumentProcessor:
    """Retrieve a small number of safe HTML product pages for the pipeline."""

    MAX_DOCUMENTS = 2
    SKIPPED_DOMAINS = ("youtube.com", "ebay.com", "facebook.com", "instagram.com")

    async def process_documents(
        self,
        documents: list[dict[str, Any]],
        sources: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        source_by_id = {source["id"]: source for source in sources}
        ordered_documents = sorted(
            documents,
            key=lambda document: source_by_id.get(document["source_id"], {}).get("reliability_score", 0),
            reverse=True,
        )

        processed: list[dict[str, Any]] = []
        fetched = 0
        async with httpx.AsyncClient(
            timeout=8.0,
            follow_redirects=True,
            headers={"User-Agent": "ProductIntelligenceHackathon/1.0"},
        ) as client:
            for document in ordered_documents:
                source = source_by_id.get(document["source_id"], {})
                domain = source.get("domain", "").lower()
                can_fetch = fetched < self.MAX_DOCUMENTS and not any(blocked in domain for blocked in self.SKIPPED_DOMAINS)
                page_text = await self._fetch_page_text(client, document["url"]) if can_fetch else ""
                if page_text:
                    updated_document = dict(document)
                    updated_document["snippet"] = page_text
                    processed.append(updated_document)
                    fetched += 1
                else:
                    processed.append(document)
        return processed

    async def _fetch_page_text(self, client: httpx.AsyncClient, url: str) -> str:
        try:
            response = await client.get(url)
            content_type = response.headers.get("content-type", "").lower()
            if response.status_code != 200 or "text/html" not in content_type:
                return ""
            parser = _ProductPageParser()
            parser.feed(response.text)
            return parser.text()
        except (httpx.HTTPError, ValueError) as error:
            logger.info("Could not read source page %s: %s", url, error)
            return ""
