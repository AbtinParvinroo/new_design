# extractors/docx/elements.py
import logging
import re
import unicodedata
from typing import List, Iterator, Tuple

from docx.document import Document as WordDocument
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

from core.models import WordResolverConfig

logger = logging.getLogger(__name__)


class WordElementExtractor:
    def __init__(self, config: WordResolverConfig, doc: WordDocument):
        self.config = config
        self.doc = doc

    def _normalize_text(self, text: str) -> str:
        if not text:
            return ""

        if self.config.normalize_unicode:
            text = unicodedata.normalize("NFKC", text)

        if self.config.normalize_whitespace:
            text = text.replace("\r\n", "\n").replace("\r", "\n")
            text = re.sub(r"[ \t]+", " ", text)
            text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    def _extract_hyperlinks(self, paragraph: Paragraph) -> List[str]:
        urls = []
        try:
            for hyperlink in paragraph._element.xpath('.//w:hyperlink'):
                r_id = hyperlink.get(qn('r:id'))
                if r_id and r_id in paragraph.part.rels:
                    target = paragraph.part.rels[r_id].target_ref
                    if target and target not in urls:
                        urls.append(target)
        except Exception as e:
            logger.debug(f"Failed to extract hyperlinks from paragraph: {e}")
        return urls

    def _iter_body_elements(self) -> Iterator[Paragraph | Table]:
        for element in self.doc.element.body:
            if element.tag == qn("w:p"):
                yield Paragraph(element, self.doc)
            elif element.tag == qn("w:tbl"):
                yield Table(element, self.doc)

    def extract_body(self) -> Tuple[List[str], int, int, int]:
        chunks: List[str] = []
        paragraph_count = 0
        non_empty_paragraph_count = 0
        table_count = 0

        for element in self._iter_body_elements():
            if isinstance(element, Paragraph):
                paragraph_count += 1
                norm_text = self._normalize_text(element.text)
                hyperlinks = self._extract_hyperlinks(element)
                if hyperlinks and norm_text:
                    link_str = " | ".join(hyperlinks)
                    norm_text = f"{norm_text} [Links: {link_str}]"
                elif hyperlinks and not norm_text:
                    norm_text = f"[Links: {' | '.join(hyperlinks)}]"

                if norm_text:
                    non_empty_paragraph_count += 1
                    chunks.append(norm_text)
                elif self.config.keep_empty_paragraphs:
                    chunks.append("")
            else:
                table_count += 1
                for row in element.rows:
                    values = []
                    for cell in row.cells:
                        norm_cell_text = self._normalize_text(cell.text)
                        if norm_cell_text:
                            values.append(norm_cell_text)
                    if values:
                        chunks.append(" | ".join(values))

        return chunks, paragraph_count, non_empty_paragraph_count, table_count

    def extract_headers_and_footers(self) -> List[str]:
        chunks: List[str] = []
        visited = set()

        for section_index, section in enumerate(self.doc.sections, start=1):
            for label, container in (("Header", section.header), ("Footer", section.footer)):
                texts = []
                for paragraph in container.paragraphs:
                    norm_text = self._normalize_text(paragraph.text)
                    if norm_text:
                        texts.append(norm_text)

                if not texts:
                    continue

                value = f"[{label} {section_index}] " + " ".join(texts)
                if value not in visited:
                    visited.add(value)
                    chunks.append(value)

        return chunks

    def extract_textboxes(self) -> Tuple[List[str], int]:
        namespaces = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        chunks: List[str] = []
        textbox_count = 0

        try:
            textboxes = self.doc.element.xpath(".//w:txbxContent", namespaces=namespaces)
            for textbox in textboxes:
                texts = textbox.xpath(".//w:t/text()", namespaces=namespaces)
                value = self._normalize_text(" ".join(texts))
                if value:
                    textbox_count += 1
                    chunks.append(value)
        except Exception:
            logger.exception("word_textbox_extraction_failed", extra={"file": "unknown"})

        return chunks, textbox_count