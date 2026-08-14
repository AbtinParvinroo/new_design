from __future__ import annotations
from normalization import OccupationNormalizer
from data_models import OccupationRecord
from typing import Dict, Sequence, Tuple
from collections import defaultdict

class OccupationIndex:
    def __init__(
        self,
        records: Sequence[OccupationRecord],
        normalizer: OccupationNormalizer
    ):
        self.records = tuple(records)
        self.normalizer = normalizer

        self.preferred_index: Dict[
            str,
            Tuple[OccupationRecord, ...]
        ] = {}

        self.alias_index: Dict[
            str,
            Tuple[OccupationRecord, ...]
        ] = {}

        self.candidate_index: Dict[
            str,
            Tuple[Tuple[OccupationRecord, str], ...]
        ] = {}

        self.fuzzy_candidates: Tuple[str, ...] = ()

        self._build()

    def _build(self) -> None:
        preferred_map: Dict[
            str,
            Dict[str, OccupationRecord]
        ] = defaultdict(dict)

        alias_map: Dict[
            str,
            Dict[str, OccupationRecord]
        ] = defaultdict(dict)

        candidate_map: Dict[
            str,
            Dict[Tuple[str, str], Tuple[OccupationRecord, str]]
        ] = defaultdict(dict)

        candidate_texts = set()

        for record in self.records:
            normalized_label = self.normalizer.normalize(
                record.preferred_label
            )

            if normalized_label:
                preferred_map[
                    normalized_label
                ][record.uri] = record

                candidate_map[
                    normalized_label
                ][
                    (record.uri, "preferred_label")
                ] = (
                    record,
                    "preferred_label"
                )

                candidate_texts.add(
                    normalized_label
                )

            valid_aliases = set()

            for alias in record.alt_labels:
                normalized_alias = self.normalizer.normalize(
                    alias
                )

                if (
                    normalized_alias
                    and normalized_alias != normalized_label
                ):
                    valid_aliases.add(
                        normalized_alias
                    )

            for normalized_alias in valid_aliases:
                alias_map[
                    normalized_alias
                ][record.uri] = record

                candidate_map[
                    normalized_alias
                ][
                    (record.uri, "alt_label")
                ] = (
                    record,
                    "alt_label"
                )

                candidate_texts.add(
                    normalized_alias
                )

        self.preferred_index = {
            key: tuple(values.values())
            for key, values in preferred_map.items()
        }

        self.alias_index = {
            key: tuple(values.values())
            for key, values in alias_map.items()
        }

        self.candidate_index = {
            key: tuple(values.values())
            for key, values in candidate_map.items()
        }

        self.fuzzy_candidates = tuple(
            candidate_texts
        )

    def get_preferred(
        self,
        text: str
    ) -> Tuple[OccupationRecord, ...]:
        return self.preferred_index.get(
            text,
            ()
        )

    def get_aliases(
        self,
        text: str
    ) -> Tuple[OccupationRecord, ...]:
        return self.alias_index.get(
            text,
            ()
        )

    def get_candidates(
        self,
        text: str
    ) -> Tuple[Tuple[OccupationRecord, str], ...]:
        return self.candidate_index.get(
            text,
            ()
        )