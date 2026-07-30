import pytest

from benchmark_lab.runner import (
    CampaignError,
    _edit_content,
    _edits,
    _expected_blame_ranges,
)


def test_edit_fixture_has_exact_size_and_replacement_counts() -> None:
    edits = _edits("fixture", 0, 2)

    before, expected, counts = _edit_content(4096, 0.5, edits)

    assert len(before.encode()) == 4096
    assert len(expected.encode()) == 4096
    assert before != expected
    assert sum(counts.values()) == 31
    assert all(edit["old_string"] not in expected for edit in edits)


def test_edit_fixture_rejects_density_that_cannot_place_every_edit() -> None:
    with pytest.raises(CampaignError, match="density"):
        _edit_content(4096, 0.01, _edits("fixture", 0, 2))


def test_expected_blame_ranges_preserve_exact_owners_and_remainder() -> None:
    assert _expected_blame_ranges(5, 2, ["event.0", "event.1"]) == [
        {
            "start_line": 1,
            "line_count": 3,
            "owner": "operation:event.1",
        },
        {
            "start_line": 4,
            "line_count": 2,
            "owner": "operation:event.0",
        },
    ]
