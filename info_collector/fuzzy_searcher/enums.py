from __future__ import annotations
from enum import Enum

class ResolutionStatus(str, Enum):
    ACCEPTED = "accepted"
    REVIEW = "review"
    UNRESOLVED = "unresolved"
    AMBIGUOUS = "ambiguous"

class MatchType(str, Enum):
    EXACT = "exact"
    ALIAS = "alias"
    FUZZY = "fuzzy"
    UNRESOLVED = "unresolved"
    AMBIGUOUS = "ambiguous"