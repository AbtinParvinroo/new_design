from __future__ import annotations
from backward_compatibility import FuzzySearcher
import json

if __name__ == "__main__":
    queries = [
        "softwere ingineer",
        "data scientest",
        "product manajer",
        "software engineer",
        "software-engineer",
        "software  engineer",
        "",
        "quantum potato architect"
    ]

    with FuzzySearcher(
        "config.json"
    ) as searcher:

        print(
            "\n"
            + "=" * 80
        )

        print(
            "OCCUPATION RESOLVER "
            "PRODUCTION SMOKE TEST"
        )

        print(
            "=" * 80
        )

        print(
            "\n[Running batch resolution...]"
        )

        batch_results = searcher.resolve_many(
            queries
        )

        for query, result in zip(
            queries,
            batch_results
        ):
            print(
                f"\nINPUT: {query!r}"
                f" --> STATUS: {result['status']}"
                f" ({result['match_type']})"
            )

            print(
                f"STANDARDIZED: "
                f"{result['standardized']}"
            )

            print(
                f"SIMILARITY: "
                f"{result['similarity']}"
            )

            print(
                f"CONFIDENCE: "
                f"{result['confidence']}"
            )

            print(
                f"MARGIN: "
                f"{result['margin']}"
            )

            if result["alternatives"]:
                print(
                    "ALTERNATIVES:"
                )

                for alternative in result[
                    "alternatives"
                ]:
                    print(
                        f"  - "
                        f"{alternative['standardized']} "
                        f"("
                        f"{alternative['weighted_score']}"
                        f")"
                    )

        print(
            "\n[Metrics]"
        )

        print(
            json.dumps(
                searcher.service.get_metrics(),
                indent=2,
                ensure_ascii=False
            )
        )