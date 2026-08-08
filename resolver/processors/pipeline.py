# processors/pipeline.py
import logging
from typing import Callable, Dict, Any

from core.models import PostProcessorConfig

logger = logging.getLogger(__name__)


class Pipeline:
    def __init__(self, config: PostProcessorConfig):
        self.config = config
        self.stages = config.pipeline_stages

    def execute(self, text: str, stage_handlers: Dict[str, Callable]) -> Dict[str, Any]:
        stats = {}
        for stage in self.stages:
            handler = stage_handlers.get(stage)
            if handler:
                text, change = handler(text)
                stats[stage] = change
            else:
                logger.warning("unknown_pipeline_stage", extra={"stage": stage})
        return {"text": text, "stats": stats}