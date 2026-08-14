from __future__ import annotations
from fuzzy_searcher.data_models import CandidateMatch, ResolutionDecision, ResolutionResult
from fuzzy_searcher.matchers import ExactMatcher, AliasMatcher, FuzzyMatcher
from fuzzy_searcher.normalization import OccupationNormalizer
from fuzzy_searcher.enums import ResolutionStatus, MatchType
from fuzzy_searcher.confidence import ConfidencePolicy
from fuzzy_searcher.validation import InputValidator
from fuzzy_searcher.scoring import ScorerRegistry
from fuzzy_searcher.matrics import MetricsTracker
from fuzzy_searcher.index import OccupationIndex
from fuzzy_searcher.config import ConfigManager
from typing import Any, Dict, Optional

class OccupationResolver:
    def __init__(
        self,
        normalizer: OccupationNormalizer,
        validator: InputValidator,
        index: OccupationIndex,
        config: ConfigManager,
        metrics: MetricsTracker
    ):
        self.normalizer = normalizer
        self.validator = validator
        self.index = index
        self.config = config
        self.metrics = metrics

        scorer_registry = ScorerRegistry(
            config
        )

        self.exact_matcher = ExactMatcher(
            index
        )

        self.alias_matcher = AliasMatcher(
            index
        )

        self.fuzzy_matcher = FuzzyMatcher(
            index,
            normalizer,
            scorer_registry,
            config
        )

        self.confidence_policy = ConfidencePolicy(
            config
        )

    def resolve(
        self,
        raw_title: str,
        threshold: float,
        limit: int
    ) -> ResolutionResult:
        validated = self.validator.validate(
            raw_title
        )

        if not validated:
            result = self._unresolved(
                raw_title
            )

            self.metrics.increment(
                "status_unresolved"
            )

            return result

        normalized = self.normalizer.normalize(
            validated
        )

        if not normalized:
            result = self._unresolved(
                raw_title,
                normalized
            )

            self.metrics.increment(
                "status_unresolved"
            )

            return result

        exact_matches = self.exact_matcher.match(
            normalized
        )

        if exact_matches:
            self.metrics.increment(
                "exact_match"
            )

            decision = self.confidence_policy.decide(
                exact_matches
            )

            return self._build_result(
                validated,
                normalized,
                decision
            )

        alias_matches = self.alias_matcher.match(
            normalized
        )

        if alias_matches:
            self.metrics.increment(
                "alias_match"
            )

            decision = self.confidence_policy.decide(
                alias_matches
            )

            return self._build_result(
                validated,
                normalized,
                decision
            )

        fuzzy_matches = self.fuzzy_matcher.match(
            normalized,
            threshold,
            limit
        )

        if fuzzy_matches:
            self.metrics.increment(
                "fuzzy_match"
            )
        else:
            self.metrics.increment(
                "no_match"
            )

        decision = self.confidence_policy.decide(
            fuzzy_matches
        )

        return self._build_result(
            validated,
            normalized,
            decision
        )

    def _build_result(
        self,
        raw_title: str,
        normalized_input: str,
        decision: ResolutionDecision
    ) -> ResolutionResult:
        self.metrics.increment(
            f"status_{decision.status.value}"
        )

        if decision.status == ResolutionStatus.AMBIGUOUS:
            alternatives = tuple(
                self._candidate_to_dict(
                    candidate
                )
                for candidate in decision.alternatives
            )

            return ResolutionResult(
                input=raw_title,
                normalized_input=normalized_input,
                status=ResolutionStatus.AMBIGUOUS.value,
                standardized=None,
                uri=None,
                isco_code=None,
                definition=None,
                taxonomy=None,
                source=None,
                similarity=round(
                    decision.similarity,
                    2
                ),
                confidence=0.0,
                margin=0.0,
                match_type=MatchType.AMBIGUOUS.value,
                matched_field=None,
                matched_text=None,
                second_best_similarity=0.0,
                second_best_score=0.0,
                alternatives=alternatives
            )

        if decision.best_match is None:
            return self._unresolved(
                raw_title,
                normalized_input
            )

        best = decision.best_match
        occupation = best.occupation

        second_best_similarity = (
            decision.alternatives[0].similarity
            if decision.alternatives
            else 0.0
        )

        second_best_score = (
            decision.alternatives[0].weighted_score
            if decision.alternatives
            else 0.0
        )

        alternatives = tuple(
            self._candidate_to_dict(
                candidate
            )
            for candidate in decision.alternatives
        )

        return ResolutionResult(
            input=raw_title,
            normalized_input=normalized_input,
            status=decision.status.value,
            standardized=occupation.preferred_label,
            uri=occupation.uri,
            isco_code=occupation.isco_code,
            definition=occupation.definition,
            taxonomy=occupation.taxonomy,
            source=occupation.source,
            similarity=round(
                decision.similarity,
                2
            ),
            confidence=decision.confidence,
            margin=round(
                decision.margin,
                2
            ),
            match_type=best.match_type.value,
            matched_field=best.matched_field,
            matched_text=best.matched_text,
            second_best_similarity=round(
                second_best_similarity,
                2
            ),
            second_best_score=round(
                second_best_score,
                2
            ),
            alternatives=alternatives
        )

    @staticmethod
    def _candidate_to_dict(
        candidate: CandidateMatch
    ) -> Dict[str, Any]:
        occupation = candidate.occupation

        return {
            "standardized": occupation.preferred_label,
            "uri": occupation.uri,
            "isco_code": occupation.isco_code,
            "definition": occupation.definition,
            "taxonomy": occupation.taxonomy,
            "source": occupation.source,
            "similarity": round(
                candidate.similarity,
                2
            ),
            "weighted_score": round(
                candidate.weighted_score,
                2
            ),
            "match_type": candidate.match_type.value,
            "matched_field": candidate.matched_field,
            "matched_text": candidate.matched_text
        }

    @staticmethod
    def _unresolved(
        raw_title: Optional[str],
        normalized_input: str = ""
    ) -> ResolutionResult:
        return ResolutionResult(
            input=raw_title or "",
            normalized_input=normalized_input,
            status=ResolutionStatus.UNRESOLVED.value,
            standardized=None,
            uri=None,
            isco_code=None,
            definition=None,
            taxonomy=None,
            source=None,
            similarity=0.0,
            confidence=0.0,
            margin=0.0,
            match_type=MatchType.UNRESOLVED.value,
            matched_field=None,
            matched_text=None,
            second_best_similarity=0.0,
            second_best_score=0.0,
            alternatives=()
        )