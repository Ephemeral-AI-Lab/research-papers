import math
from collections.abc import Sequence
from typing import Literal

from pydantic import Field

from .models import StrictModel


STATISTICS_SCHEMA_VERSION = 1
BOOTSTRAP_RESAMPLES = 10_000
_MASK_64 = (1 << 64) - 1


class StatisticsError(ValueError):
    pass


class ConfidenceInterval(StrictModel):
    level: Literal[0.95] = 0.95
    lower: float
    upper: float
    method: Literal["percentile_bootstrap_median"] = "percentile_bootstrap_median"
    resamples: Literal[10_000] = BOOTSTRAP_RESAMPLES


class PearsonConfidenceInterval(StrictModel):
    level: Literal[0.95] = 0.95
    lower: float
    upper: float
    method: Literal["percentile_bootstrap_pearson"] = "percentile_bootstrap_pearson"
    resamples: Literal[10_000] = BOOTSTRAP_RESAMPLES
    valid_resamples: int = Field(ge=0, le=BOOTSTRAP_RESAMPLES)


class PearsonConfidenceEstimate(StrictModel):
    interval: PearsonConfidenceInterval | None
    omission: Literal[
        "insufficient_n", "zero_variance", "insufficient_valid_resamples"
    ] | None


class SampleStatistics(StrictModel):
    schema_version: Literal[1] = STATISTICS_SCHEMA_VERSION
    count: int = Field(ge=0)
    minimum: float | None
    maximum: float | None
    mean: float | None
    sample_standard_deviation: float | None
    median: float | None
    median_absolute_deviation: float | None
    p25: float | None
    p75: float | None
    p95: float | None
    coefficient_of_variation: float | None
    median_confidence_interval: ConfidenceInterval | None
    confidence_interval_omission: Literal["insufficient_n"] | None
    p95_exploratory: bool
    outlier_indices: list[int]
    distribution: dict[str, object]


class _SplitMix64:
    def __init__(self, seed: int) -> None:
        if not 0 <= seed <= _MASK_64:
            raise StatisticsError("bootstrap seed must be an unsigned 64-bit integer")
        self._state = seed

    def index(self, length: int) -> int:
        return self._next() % length

    def _next(self) -> int:
        self._state = (self._state + 0x9E3779B97F4A7C15) & _MASK_64
        value = self._state
        value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & _MASK_64
        value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & _MASK_64
        return value ^ (value >> 31)


def summarize(samples: Sequence[float], bootstrap_seed: int) -> SampleStatistics:
    values = _finite_values(samples)
    if not values:
        return SampleStatistics(
            count=0,
            minimum=None,
            maximum=None,
            mean=None,
            sample_standard_deviation=None,
            median=None,
            median_absolute_deviation=None,
            p25=None,
            p75=None,
            p95=None,
            coefficient_of_variation=None,
            median_confidence_interval=None,
            confidence_interval_omission="insufficient_n",
            p95_exploratory=True,
            outlier_indices=[],
            distribution={"kind": "empty"},
        )

    ordered = sorted(values)
    count = len(ordered)
    mean = sum(ordered) / count
    deviation = None
    if count > 1:
        deviation = math.sqrt(sum((value - mean) ** 2 for value in ordered) / (count - 1))
    median = _quantile(ordered, 0.5)
    deviations = sorted(abs(value - median) for value in ordered)
    p25 = _quantile(ordered, 0.25)
    p75 = _quantile(ordered, 0.75)
    interquartile_range = p75 - p25
    lower_fence = p25 - 1.5 * interquartile_range
    upper_fence = p75 + 1.5 * interquartile_range
    interval = _bootstrap_median_interval(ordered, bootstrap_seed) if count >= 5 else None

    distribution: dict[str, object]
    if count < 30:
        distribution = {"kind": "raw_points", "values": values}
    else:
        distribution = {
            "kind": "histogram_ecdf",
            "histogram": _histogram(ordered, p25, p75),
            "ecdf": [
                {"value": value, "cumulative_probability": (index + 1) / count}
                for index, value in enumerate(ordered)
            ],
        }

    return SampleStatistics(
        count=count,
        minimum=ordered[0],
        maximum=ordered[-1],
        mean=mean,
        sample_standard_deviation=deviation,
        median=median,
        median_absolute_deviation=_quantile(deviations, 0.5),
        p25=p25,
        p75=p75,
        p95=_quantile(ordered, 0.95),
        coefficient_of_variation=(deviation / mean if deviation is not None and mean != 0 else None),
        median_confidence_interval=interval,
        confidence_interval_omission="insufficient_n" if count < 5 else None,
        p95_exploratory=count < 20,
        outlier_indices=[
            index
            for index, value in enumerate(values)
            if value < lower_fence or value > upper_fence
        ],
        distribution=distribution,
    )


def bootstrap_median_difference_interval(
    reference: Sequence[float], candidate: Sequence[float], seed: int
) -> ConfidenceInterval | None:
    reference_values = _finite_values(reference)
    candidate_values = _finite_values(candidate)
    if len(reference_values) < 5 or len(candidate_values) < 5:
        return None
    rng = _SplitMix64(seed)
    differences = []
    for _ in range(BOOTSTRAP_RESAMPLES):
        reference_sample = sorted(
            reference_values[rng.index(len(reference_values))]
            for _ in reference_values
        )
        candidate_sample = sorted(
            candidate_values[rng.index(len(candidate_values))]
            for _ in candidate_values
        )
        differences.append(
            _quantile(candidate_sample, 0.5) - _quantile(reference_sample, 0.5)
        )
    differences.sort()
    return ConfidenceInterval(
        lower=_quantile(differences, 0.025), upper=_quantile(differences, 0.975)
    )


def pearson(pairs: Sequence[tuple[float, float]]) -> float | None:
    values = _finite_pairs(pairs)
    if len(values) < 2:
        return None
    mean_left = sum(left for left, _ in values) / len(values)
    mean_right = sum(right for _, right in values) / len(values)
    numerator = sum(
        (left - mean_left) * (right - mean_right) for left, right in values
    )
    left_variance = sum((left - mean_left) ** 2 for left, _ in values)
    right_variance = sum((right - mean_right) ** 2 for _, right in values)
    denominator = math.sqrt(left_variance * right_variance)
    return numerator / denominator if denominator > 0 else None


def bootstrap_pearson_interval(
    pairs: Sequence[tuple[float, float]], seed: int
) -> PearsonConfidenceEstimate:
    values = _finite_pairs(pairs)
    if len(values) < 5:
        return PearsonConfidenceEstimate(interval=None, omission="insufficient_n")
    if pearson(values) is None:
        return PearsonConfidenceEstimate(interval=None, omission="zero_variance")

    rng = _SplitMix64(seed)
    coefficients = []
    for _ in range(BOOTSTRAP_RESAMPLES):
        coefficient = pearson([values[rng.index(len(values))] for _ in values])
        if coefficient is not None:
            coefficients.append(coefficient)
    if len(coefficients) < BOOTSTRAP_RESAMPLES // 2:
        return PearsonConfidenceEstimate(
            interval=None, omission="insufficient_valid_resamples"
        )
    coefficients.sort()
    return PearsonConfidenceEstimate(
        interval=PearsonConfidenceInterval(
            lower=_quantile(coefficients, 0.025),
            upper=_quantile(coefficients, 0.975),
            valid_resamples=len(coefficients),
        ),
        omission=None,
    )


def _bootstrap_median_interval(samples: list[float], seed: int) -> ConfidenceInterval:
    rng = _SplitMix64(seed)
    medians = []
    for _ in range(BOOTSTRAP_RESAMPLES):
        resampled = sorted(samples[rng.index(len(samples))] for _ in samples)
        medians.append(_quantile(resampled, 0.5))
    medians.sort()
    return ConfidenceInterval(
        lower=_quantile(medians, 0.025), upper=_quantile(medians, 0.975)
    )


def _histogram(ordered: list[float], p25: float, p75: float) -> dict[str, object]:
    minimum, maximum = ordered[0], ordered[-1]
    if minimum == maximum:
        return {
            "method": "single_value",
            "edges": [minimum, maximum],
            "counts": [len(ordered)],
        }
    interquartile_range = p75 - p25
    width = 2 * interquartile_range / math.cbrt(len(ordered))
    if interquartile_range > 0 and math.isfinite(width) and width > 0:
        method = "freedman_diaconis"
        bin_count = max(1, math.ceil((maximum - minimum) / width))
    else:
        method = "sturges"
        bin_count = math.ceil(math.log2(len(ordered))) + 1
    bin_width = (maximum - minimum) / bin_count
    edges = [
        maximum if index == bin_count else minimum + bin_width * index
        for index in range(bin_count + 1)
    ]
    counts = [0] * bin_count
    for value in ordered:
        index = bin_count - 1 if value == maximum else math.floor((value - minimum) / bin_width)
        counts[min(index, bin_count - 1)] += 1
    return {"method": method, "edges": edges, "counts": counts}


def _quantile(ordered: Sequence[float], probability: float) -> float:
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _finite_values(samples: Sequence[float]) -> list[float]:
    values = [float(value) for value in samples]
    for index, value in enumerate(values):
        if not math.isfinite(value):
            raise StatisticsError(f"sample at index {index} is not finite")
    return values


def _finite_pairs(pairs: Sequence[tuple[float, float]]) -> list[tuple[float, float]]:
    values = [(float(left), float(right)) for left, right in pairs]
    for index, (left, right) in enumerate(values):
        if not math.isfinite(left) or not math.isfinite(right):
            raise StatisticsError(f"sample at index {index} is not finite")
    return values
