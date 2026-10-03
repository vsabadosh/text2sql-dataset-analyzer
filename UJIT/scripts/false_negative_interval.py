#!/usr/bin/env python3
"""Weighted false-negative estimates and stratified-bootstrap intervals.

The manuscript labels are ``human1.verdict`` in
``false-negative-sample-350-screening.json``. Weights and stratum sizes come
from ``false-negative-sample-350-design.json``. Confirmed true-positive pairs
are counted from ``released-contradiction-verdicts-231.json``.

Each of 20,000 replicates draws items with replacement inside its own stratum
and reapplies the fixed design weights. The interval bounds are the sorted
replicates at index ``int(0.025 * DRAWS)`` and ``int(0.975 * DRAWS) - 1``.
"""

from __future__ import annotations

import collections
import json
import random
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
UJIT = REPO_ROOT / "UJIT"
SCREENING = UJIT / "false-negative-sample-350-screening.json"
DESIGN = UJIT / "false-negative-sample-350-design.json"
CENSUS = UJIT / "released-contradiction-verdicts-231.json"

DRAWS = 20_000
SEED = 7
IN_SCOPE = "FALSE_NEGATIVE_IN_SCOPE"
OUT_OF_SCOPE = "DEFECT_OUT_OF_SCOPE"


def bounds(sorted_values: list[float]) -> tuple[float, float]:
    return sorted_values[int(0.025 * DRAWS)], sorted_values[int(0.975 * DRAWS) - 1]


def pair_id(item_id: str) -> str:
    return item_id.split("#", 1)[0]


def true_positive_pairs(census: list[dict]) -> int:
    pairs = {
        pair_id(row["id"])
        for row in census
        if str(row["human_verdict"]).startswith("TRUE")
    }
    return len(pairs)


def main() -> None:
    design = json.loads(DESIGN.read_text())
    records = json.loads(SCREENING.read_text())
    census = json.loads(CENSUS.read_text())

    populations = {
        tuple(name.split("/")): stratum["population_size"]
        for name, stratum in design["strata"].items()
    }
    strata: dict[tuple[str, str, str], list[tuple[float, str]]] = collections.defaultdict(list)
    for record in records:
        sampling = record["sampling"]
        key = (sampling["corpus"], sampling["split"], sampling["outcome"])
        strata[key].append((sampling["sampling_weight"], record["human1"]["verdict"]))
    if set(strata) != set(populations):
        raise SystemExit("screening strata do not match the design file")

    def total(label: str, predicate) -> float:
        return sum(
            weight
            for key, members in strata.items()
            if predicate(key)
            for weight, verdict in members
            if verdict == label
        )

    unresolved_population = design["eligible_after_exclusions"]["unresolved_only"]
    supported_population = design["eligible_after_exclusions"]["supported_only"]
    frame = unresolved_population + supported_population
    spider_population = sum(size for key, size in populations.items() if key[0] == "spider")
    bird_population = sum(size for key, size in populations.items() if key[0] == "bird")
    in_scope = total(IN_SCOPE, lambda _key: True)
    true_positives = true_positive_pairs(census)

    point = {
        "in_scope_pairs": in_scope,
        "recall": true_positives / (true_positives + in_scope),
        "unresolved": total(IN_SCOPE, lambda key: key[2] == "unresolved_only") / unresolved_population,
        "supported": total(IN_SCOPE, lambda key: key[2] == "supported_only") / supported_population,
        "out_of_scope": total(OUT_OF_SCOPE, lambda _key: True) / frame,
        "spider_out": total(OUT_OF_SCOPE, lambda key: key[0] == "spider") / spider_population,
        "bird_out": total(OUT_OF_SCOPE, lambda key: key[0] == "bird") / bird_population,
    }

    rng = random.Random(SEED)
    replicates = {name: [] for name in point if name != "in_scope_pairs"}
    for _ in range(DRAWS):
        weighted = collections.Counter()
        for key, members in strata.items():
            for _draw in range(len(members)):
                weight, verdict = members[rng.randrange(len(members))]
                weighted[(key, verdict)] += weight
        in_scope_draw = sum(
            value for (key, verdict), value in weighted.items() if verdict == IN_SCOPE
        )
        unresolved_draw = sum(
            value
            for (key, verdict), value in weighted.items()
            if verdict == IN_SCOPE and key[2] == "unresolved_only"
        )
        supported_draw = in_scope_draw - unresolved_draw
        out_draw = sum(
            value for (key, verdict), value in weighted.items() if verdict == OUT_OF_SCOPE
        )
        spider_draw = sum(
            value
            for (key, verdict), value in weighted.items()
            if verdict == OUT_OF_SCOPE and key[0] == "spider"
        )
        replicates["recall"].append(true_positives / (true_positives + in_scope_draw))
        replicates["unresolved"].append(unresolved_draw / unresolved_population)
        replicates["supported"].append(supported_draw / supported_population)
        replicates["out_of_scope"].append(out_draw / frame)
        replicates["spider_out"].append(spider_draw / spider_population)
        replicates["bird_out"].append((out_draw - spider_draw) / bird_population)

    print(f"draws {DRAWS:,}  seed {SEED}")
    print(f"true-positive pairs            : {true_positives}")
    print(f"weighted in-scope false negatives: {point['in_scope_pairs']:.4f}")
    labels = (
        ("pair-level recall", "recall", 1),
        ("UNRESOLVED prevalence", "unresolved", 2),
        ("SUPPORTED-only prevalence", "supported", 2),
        ("out-of-scope prevalence", "out_of_scope", 2),
        ("Spider out-of-scope", "spider_out", 2),
        ("BIRD out-of-scope", "bird_out", 2),
    )
    for label, name, digits in labels:
        low, high = bounds(sorted(replicates[name]))
        estimate = point[name]
        print(
            f"{label:30}: {estimate:8.4%}   "
            f"95% CI [{low:8.4%}, {high:8.4%}]   "
            f"rounded {estimate * 100:.{digits}f} "
            f"({low * 100:.{digits}f}--{high * 100:.{digits}f})"
        )


if __name__ == "__main__":
    main()
