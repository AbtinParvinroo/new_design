from __future__ import annotations
from fuzzy_searcher.data_models import OccupationRecord, CandidateMatch
from fuzzy_searcher.normalization import OccupationNormalizer
from fuzzy_searcher.scoring import ScorerRegistry
from fuzzy_searcher.index import OccupationIndex
from fuzzy_searcher.config import ConfigManager
from fuzzy_searcher.enums import MatchType
from typing import Dict, List
from rapidfuzz import process

class ExactMatcher:
    def __init__(
        self,
        index: OccupationIndex
    ):
        self.index = index

    def match(
        self,
        query: str
    ) -> List[CandidateMatch]:
        records = self.index.get_preferred(
            query
        )

        if not records:
            return []

        matches = [
            CandidateMatch(
                occupation=record,
                similarity=100.0,
                matched_text=query,
                matched_field="preferred_label",
                match_type=MatchType.EXACT,
                weighted_score=100.0
            )
            for record in records
        ]

        return matches


class AliasMatcher:
    def __init__(
        self,
        index: OccupationIndex
    ):
        self.index = index

    def match(
        self,
        query: str
    ) -> List[CandidateMatch]:
        records = self.index.get_aliases(
            query
        )

        if not records:
            return []

        match_type = (
            MatchType.ALIAS
            if len(records) == 1
            else MatchType.AMBIGUOUS
        )

        return [
            CandidateMatch(
                occupation=record,
                similarity=100.0,
                matched_text=query,
                matched_field="alt_label",
                match_type=match_type,
                weighted_score=100.0
            )
            for record in records
        ]

class FuzzyMatcher:
    def __init__(
        self,
        index: OccupationIndex,
        normalizer: OccupationNormalizer,
        scorer_registry: ScorerRegistry,
        config: ConfigManager
    ):
        self.index = index
        self.normalizer = normalizer
        self.scorer_registry = scorer_registry

        fuzzy_config = config.fuzzy()

        self.preferred_weight = float(
            fuzzy_config.get(
                "preferred_label_weight",
                0.70
            )
        )

        self.alias_weight = float(
            fuzzy_config.get(
                "alias_weight",
                0.30
            )
        )

        self.candidate_limit = int(
            fuzzy_config.get(
                "candidate_limit",
                20
            )
        )

        total_weight = (
            self.preferred_weight
            + self.alias_weight
        )

        self.preferred_weight /= total_weight
        self.alias_weight /= total_weight

    def match(
        self,
        query: str,
        threshold: float,
        limit: int
    ) -> List[CandidateMatch]:
        if not query:
            return []

        raw_results = process.extract(
            query,
            self.index.fuzzy_candidates,
            scorer=self.scorer_registry.scorer,
            limit=self.candidate_limit
        )

        best_by_uri: Dict[
            str,
            CandidateMatch
        ] = {}

        for matched_text, similarity, _ in raw_results:
            candidate_entries = (
                self.index.get_candidates(
                    matched_text
                )
            )

            for record, field_name in candidate_entries:
                candidate = self._build_candidate(
                    query=query,
                    matched_text=matched_text,
                    candidate_similarity=float(similarity),
                    record=record,
                    field_name=field_name
                )

                previous = best_by_uri.get(
                    record.uri
                )

                if (
                    previous is None
                    or candidate.weighted_score
                    > previous.weighted_score
                ):
                    best_by_uri[
                        record.uri
                    ] = candidate

        results = [
            candidate
            for candidate in best_by_uri.values()
            if candidate.weighted_score >= threshold
        ]

        results.sort(
            key=lambda candidate: (
                candidate.weighted_score,
                candidate.similarity,
                candidate.occupation.preferred_label
            ),
            reverse=True
        )

        return results[:limit]

    def _build_candidate(
        self,
        query: str,
        matched_text: str,
        candidate_similarity: float,
        record: OccupationRecord,
        field_name: str
    ) -> CandidateMatch:
        preferred_text = self.normalizer.normalize(
            record.preferred_label
        )

        preferred_score = (
            self.scorer_registry.score(
                query,
                preferred_text
            )
            if preferred_text
            else 0.0
        )

        best_alias_score = 0.0
        best_alias_text = ""

        for alias in record.alt_labels:
            normalized_alias = self.normalizer.normalize(
                alias
            )

            if not normalized_alias:
                continue

            alias_score = self.scorer_registry.score(
                query,
                normalized_alias
            )

            if alias_score > best_alias_score:
                best_alias_score = alias_score
                best_alias_text = normalized_alias

        weighted_score = (
            preferred_score * self.preferred_weight
            + best_alias_score * self.alias_weight
        )

        if field_name == "preferred_label":
            matched_similarity = preferred_score
        elif field_name == "alt_label":
            matched_similarity = self.scorer_registry.score(
                query,
                matched_text
            )
        else:
            matched_similarity = candidate_similarity

        selected_text = (
            preferred_text
            if field_name == "preferred_label"
            else matched_text
        )

        return CandidateMatch(
            occupation=record,
            similarity=float(matched_similarity),
            matched_text=selected_text,
            matched_field=field_name,
            match_type=MatchType.FUZZY,
            weighted_score=float(weighted_score)
        )