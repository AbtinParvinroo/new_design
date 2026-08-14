from __future__ import annotations
from typing import Any, Dict, Optional, Tuple
from enums import ResolutionStatus, MatchType
from dataclasses import dataclass

@dataclass(frozen=True)
class OccupationRecord:
    uri: str
    preferred_label: str
    alt_labels: Tuple[str, ...] = ()
    isco_code: str = ""
    definition: str = ""
    taxonomy: str = "esco"
    source: str = "database"

@dataclass(frozen=True)
class CandidateMatch:
    occupation: OccupationRecord
    similarity: float
    matched_text: str
    matched_field: str
    match_type: MatchType
    weighted_score: float


@dataclass(frozen=True)
class ResolutionDecision:
    status: ResolutionStatus
    confidence: float
    similarity: float
    margin: float
    best_match: Optional[CandidateMatch]
    alternatives: Tuple[CandidateMatch, ...] = ()


@dataclass(frozen=True)
class ResolutionResult:
    input: str
    normalized_input: str
    status: str
    standardized: Optional[str]
    uri: Optional[str]
    isco_code: Optional[str]
    definition: Optional[str]
    taxonomy: Optional[str]
    source: Optional[str]
    similarity: float
    confidence: float
    margin: float
    match_type: str
    matched_field: Optional[str]
    matched_text: Optional[str]
    second_best_similarity: float
    second_best_score: float
    alternatives: Tuple[Dict[str, Any], ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input": self.input,
            "normalized_input": self.normalized_input,
            "status": self.status,
            "standardized": self.standardized,
            "uri": self.uri,
            "isco_code": self.isco_code,
            "definition": self.definition,
            "taxonomy": self.taxonomy,
            "source": self.source,
            "similarity": self.similarity,
            "confidence": self.confidence,
            "margin": self.margin,
            "match_type": self.match_type,
            "matched_field": self.matched_field,
            "matched_text": self.matched_text,
            "second_best_similarity": self.second_best_similarity,
            "second_best_score": self.second_best_score,
            "alternatives": list(self.alternatives)
        }