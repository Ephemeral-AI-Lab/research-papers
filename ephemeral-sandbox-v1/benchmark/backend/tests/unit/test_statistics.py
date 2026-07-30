import json
from pathlib import Path

import pytest

from benchmark_lab.statistics import (
    StatisticsError,
    bootstrap_median_difference_interval,
    bootstrap_pearson_interval,
    pearson,
    summarize,
)


GOLDEN = Path(__file__).parents[3] / "tests/fixtures/golden/statistics/vectors-v1.json"


def test_statistics_match_frozen_golden_vectors() -> None:
    vectors = json.loads(GOLDEN.read_text())["data"]

    summary = summarize(vectors[0]["samples"], vectors[0]["seed"]).model_dump(mode="json")
    assert summary.pop("schema_version") == 1
    assert summary == vectors[0]["expected"]

    projection = summarize(vectors[1]["samples"], vectors[1]["seed"]).distribution
    expected_projection = vectors[1]["expected_projection"]
    assert projection["kind"] == expected_projection["kind"]
    assert projection["histogram"] == expected_projection["histogram"]
    assert projection["ecdf"][-1] == expected_projection["last_ecdf"]

    difference = bootstrap_median_difference_interval(
        vectors[2]["reference"], vectors[2]["candidate"], vectors[2]["seed"]
    )
    assert difference is not None
    assert difference.model_dump(mode="json") == vectors[2]["expected"]

    pairs = [tuple(pair) for pair in vectors[3]["pairs"]]
    assert pearson(pairs) == pytest.approx(1.0)
    interval = bootstrap_pearson_interval(pairs, vectors[3]["seed"]).interval
    assert interval is not None
    lower, upper = vectors[3]["expected_bounds"]
    assert lower <= interval.lower <= interval.upper <= upper


def test_statistics_preserve_omissions_and_original_outlier_indices() -> None:
    assert summarize([], 1).distribution == {"kind": "empty"}
    small = summarize([1, 2, 3, 4], 1)
    assert small.median_confidence_interval is None
    assert small.confidence_interval_omission == "insufficient_n"
    assert summarize([100, 1, 2, 3, 4, 5], 1).outlier_indices == [0]
    assert bootstrap_median_difference_interval([1] * 4, [2] * 5, 1) is None
    assert bootstrap_pearson_interval([(1, 1)] * 5, 1).omission == "zero_variance"


def test_statistics_reject_non_finite_values() -> None:
    with pytest.raises(StatisticsError, match="index 1"):
        summarize([1, float("nan")], 1)
    with pytest.raises(StatisticsError, match="index 0"):
        pearson([(1, float("inf"))])
