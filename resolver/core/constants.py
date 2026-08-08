# core/constants.py
from typing import Dict, List, Any

ALLOWED_TYPES: Dict[str, Dict[str, List[Any]]] = {
    "pdf": {
        "extensions": [".pdf"],
        "magic": [b"%PDF"]
    },
    "docx": {
        "extensions": [".docx"],
        "magic": [b"PK\x03\x04"]
    }
}