from __future__ import annotations
from data_models import CandidateMatch, ResolutionDecision
from enums import ResolutionStatus, MatchType
from config import ConfigManager
from typing import Sequence

class ConfidencePolicy:
    def __init__(
        self,
        config: ConfigManager
    ):
        fuzzy_config = config.fuzzy()

        self.accept_threshold = float(
            fuzzy_config.get(
                "accept_threshold",
                90
            )
        )

        self.review_threshold = float(
            fuzzy_config.get(
                "review_threshold",
                75
            )
        )

        self.accept_margin = float(
            fuzzy_config.get(
                "accept_margin",
                8
            )
        )

        self.review_margin = float(
            fuzzy_config.get(
                "review_margin",
                3
            )
        )

    def decide(
        self,
        matches: Sequence[CandidateMatch]
    ) -> ResolutionDecision:
        if not matches:
            return ResolutionDecision(
                status=ResolutionStatus.UNRESOLVED,
                confidence=0.0,
                similarity=0.0,
                margin=0.0,
                best_match=None,
                alternatives=()
            )

        ordered_matches = sorted(
            matches,
            key=lambda candidate: (
                candidate.weighted_score,
                candidate.similarity
            ),
            reverse=True
        )

        best = ordered_matches[0]

        if best.match_type == MatchType.AMBIGUOUS:
            return ResolutionDecision(
                status=ResolutionStatus.AMBIGUOUS,
                confidence=0.0,
                similarity=best.similarity,
                margin=0.0,
                best_match=None,
                alternatives=tuple(
                    ordered_matches
                )
            )

        second_score = (
            ordered_matches[1].weighted_score
            if len(ordered_matches) > 1
            else 0.0
        )

        margin = (
            best.weighted_score
            - second_score
        )

        if best.match_type in {
            MatchType.EXACT,
            MatchType.ALIAS
        }:
            return ResolutionDecision(
                status=ResolutionStatus.ACCEPTED,
                confidence=1.0,
                similarity=best.similarity,
                margin=margin,
                best_match=best,
                alternatives=tuple(
                    ordered_matches[1:]
                )
            )

        confidence = self._calculate_confidence(
            best.weighted_score,
            margin
        )

        if (
            best.weighted_score >= self.accept_threshold
            and margin >= self.accept_margin
        ):
            status = ResolutionStatus.ACCEPTED

        elif (
            best.weighted_score >= self.review_threshold
            and margin >= self.review_margin
        ):
            status = ResolutionStatus.REVIEW

        else:
            status = ResolutionStatus.UNRESOLVED

        return ResolutionDecision(
            status=status,
            confidence=confidence,
            similarity=best.similarity,
            margin=margin,
            best_match=best,
            alternatives=tuple(
                ordered_matches[1:]
            )
        )

    @staticmethod
    def _calculate_confidence(
        score: float,
        margin: float
    ) -> float:
        score_factor = max(
            0.0,
            min(
                score / 100.0,
                1.0
            )
        )

        margin_factor = max(
            0.0,
            min(
                margin / 20.0,
                1.0
            )
        )

        confidence = (
            score_factor * 0.75
            + margin_factor * 0.25
        )

        return round(
            max(
                0.0,
                min(
                    confidence,
                    1.0
                )
            ),
            4
        )