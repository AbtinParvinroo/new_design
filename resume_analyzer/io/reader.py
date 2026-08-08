from __future__ import annotations
import csv
import json
import logging
import sys
from io import StringIO
import yaml
from core.config import ResumeAnalyzerConfig
from models.input_models import ResumeInput

logger = logging.getLogger(__name__)

def read_input(config: ResumeAnalyzerConfig) -> ResumeInput:
    raw = sys.stdin.read(config.max_input_size + 1)

    if len(raw) > config.max_input_size:
        raise ValueError("Input size exceeded limits.")

    try:
        parsed_data = yaml.safe_load(raw) or {}
        events_csv_str = parsed_data.get("events_csv", "").strip()
        events_list = []
        if events_csv_str:
            reader = csv.DictReader(StringIO(events_csv_str))
            for row in reader:
                event_data = {k: (v if v and v.strip() != "" else None) for k, v in row.items()}
                payload_str = event_data.get("payload")
                if payload_str:
                    try:
                        event_data["payload"] = json.loads(payload_str)
                    except json.JSONDecodeError:
                        event_data["payload"] = {}
                else:
                    event_data["payload"] = {}
                events_list.append(event_data)

        return ResumeInput(events=events_list)
    except Exception as exc:
        logger.exception("input_validation_failed")
        raise ValueError("Invalid Input Format. Expected YAML with 'events_csv' key.") from exc