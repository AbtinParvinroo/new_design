# processors/section_extractor.py
import re
import logging
from typing import Dict

from core.models import PostProcessorConfig
from core.exceptions import SectionExtractionError

logger = logging.getLogger(__name__)


class SectionExtractor:
    def __init__(self, config: PostProcessorConfig):
        self.config = config
        self.section_patterns = {
            name: re.compile(
                r"^\s*(?:" + "|".join(re.escape(item) for item in values) + r")\s*:?\s*$",
                flags=re.IGNORECASE,
                timeout=config.regex_timeout
            )
            for name, values in config.section_keywords.items()
        }

    def extract(self, text: str) -> Dict[str, str]:
        try:
            sections = {key: "" for key in self.config.section_keywords}
            current_section = None
            buffer: list[str] = []

            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue

                matched = None
                for name, pattern in self.section_patterns.items():
                    if pattern.match(line):
                        matched = name
                        break

                if matched:
                    if current_section and buffer:
                        sections[current_section] = "\n".join(buffer)
                    current_section = matched
                    buffer.clear()
                    continue

                if current_section:
                    buffer.append(line)

            if current_section and buffer:
                sections[current_section] = "\n".join(buffer)

            return sections

        except Exception as e:
            raise SectionExtractionError(f"Failed to extract sections: {e}") from e