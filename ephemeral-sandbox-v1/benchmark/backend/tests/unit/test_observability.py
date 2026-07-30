import pytest

from benchmark_lab.observability import ObservabilityError, parse_trace


def _trace() -> dict:
    return {
        "view": "trace",
        "trace": "request-1",
        "spans": [{
            "offset_ms": 0,
            "span": {
                "ts": 1,
                "trace": "request-1",
                "span": "root",
                "name": "layerstack.squash",
                "dur_ms": 1.0,
                "status": "completed",
                "attrs": {},
            },
            "children": [],
            "events": [],
        }],
    }


def test_trace_accepts_the_product_root_span_with_omitted_parent() -> None:
    parsed = parse_trace(_trace(), "request-1")

    assert parsed.spans[0].span.parent is None


def test_trace_still_rejects_an_explicit_wrong_root_parent() -> None:
    value = _trace()
    value["spans"][0]["span"]["parent"] = "not-a-root"

    with pytest.raises(ObservabilityError, match="tree contract"):
        parse_trace(value, "request-1")
