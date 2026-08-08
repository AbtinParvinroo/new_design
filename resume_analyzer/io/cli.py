from __future__ import annotations
import logging
import sys
import yaml
from core.config import ResumeAnalyzerConfig
from analyzer.resume_analyzer import ResumeAnalyzer
from .reader import read_input

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main() -> int:
    try:
        config = ResumeAnalyzerConfig()
        analyzer = ResumeAnalyzer(config)
        resume = read_input(config)
        result = analyzer.analyze(resume)
        print(yaml.dump(result.model_dump(), default_flow_style=False, sort_keys=False, allow_unicode=True))
        return 0
    except Exception as exc:
        logger.exception("fatal_execution_error")
        print(yaml.dump({"status": "failed", "error": str(exc)}, default_flow_style=False))
        return 1

if __name__ == "__main__":
    sys.exit(main())