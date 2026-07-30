import json
import copy
from pathlib import Path

import pytest

from benchmark_lab.planning import (
    RuntimeEnvironment,
    expand_plan,
    load_preset,
    load_workspace_profiles,
)


ROOT = Path(__file__).resolve().parents[3]
GOLDEN = ROOT / "tests/fixtures/golden/rust/quick-smoke-completed/expanded-plan.json"
CATALOG = ROOT / "tests/fixtures/golden/catalog/product-catalog-v1.json"


def _catalog_operations() -> frozenset[str]:
    catalog = json.loads(CATALOG.read_text())
    return frozenset(
        operation["name"]
        for domain in catalog["domains"].values()
        for operation in domain["operations"]
    )


def test_quick_smoke_expansion_matches_sanitized_golden_contract() -> None:
    preset = load_preset(ROOT / "presets/quick-smoke.yml")
    profiles = load_workspace_profiles(ROOT / "defaults/workspace-profiles")
    environment = RuntimeEnvironment(
        test_workspace_root="/benchmark-fixture/test-repository",
        image_digest="sha256:4fbb8e6a8395de5a7550b33509421a2bafbc0aab6c06ba2cef9ebffbc7092d90",
        filesystem="/",
        free_space_bytes=548188672000,
        workspace_root_identity="sha256:3667c767cfb284ab53169bbbbbdf0d9b7c40900c2f97b7ddf198739e937f9335",
    )
    actual = expand_plan(preset.plan, environment=environment, profiles=profiles)
    expected = json.loads(GOLDEN.read_text())["data"]

    # Fixture sanitization deliberately does not recompute cryptographic review
    # hashes. Every hash input and all executable cells must still match.
    for volatile in ("plan_hash",):
        actual.pop(volatile)
        expected.pop(volatile)
    assert actual == expected


def test_expansion_is_deterministic_and_counts_requests() -> None:
    preset = load_preset(ROOT / "presets/quick-smoke.yml")
    profiles = load_workspace_profiles(ROOT / "defaults/workspace-profiles")
    environment = RuntimeEnvironment("/tmp/benchmark", None, None, None)
    first = expand_plan(preset.plan, environment=environment, profiles=profiles)
    second = expand_plan(preset.plan, environment=environment, profiles=profiles)
    assert first == second
    assert first["estimates"] | {} == first["estimates"]
    assert first["estimates"]["cell_count"] == 8
    assert first["estimates"]["trial_batch_count"] == 48
    assert first["estimates"]["issued_operation_request_count"] == 96


def test_unknown_profile_prevents_run() -> None:
    preset = load_preset(ROOT / "presets/quick-smoke.yml")
    preset.plan.operations[0].configuration.factors["workspace_profile"].values = ["missing"]
    result = expand_plan(
        preset.plan,
        environment=RuntimeEnvironment("/tmp/benchmark", None, None, None),
        profiles=load_workspace_profiles(ROOT / "defaults/workspace-profiles"),
    )
    assert result["runnable"] is False
    assert any(item["code"] == "unknown_workspace_profile" for item in result["validation"])


def test_strict_plan_rejects_unknown_fields(tmp_path: Path) -> None:
    path = tmp_path / "preset.yml"
    path.write_text("schema_version: 1\nid: x\nversion: 1\nunknown: true\nplan: {}\n")
    with pytest.raises(ValueError, match="invalid benchmark preset"):
        load_preset(path)


@pytest.mark.parametrize(
    ("mutate", "code"),
    [
        (
            lambda plan: plan.operations.append(copy.deepcopy(plan.operations[0])),
            "duplicate_operation",
        ),
        (
            lambda plan: setattr(
                plan.operations[0].configuration.factors["concurrent_requests"],
                "values",
                [1, 1],
            ),
            "duplicate_factor_value",
        ),
        (
            lambda plan: setattr(
                plan.operations[0].configuration.factors["concurrent_requests"],
                "control",
                2,
            ),
            "invalid_factor_control",
        ),
        (
            lambda plan: setattr(
                plan.operations[0].configuration.factors["concurrent_requests"],
                "values",
                [1, 257],
            ),
            "invalid_factor_value",
        ),
        (
            lambda plan: setattr(plan.environment, "image", "/tmp/product/image"),
            "unsafe_image_reference",
        ),
    ],
)
def test_plan_validation_rejects_duplicates_controls_bounds_and_unsafe_values(
    mutate, code: str
) -> None:
    preset = load_preset(ROOT / "presets/quick-smoke.yml")
    mutate(preset.plan)

    result = expand_plan(
        preset.plan,
        environment=RuntimeEnvironment("/tmp/benchmark", None, None, None),
        profiles=load_workspace_profiles(ROOT / "defaults/workspace-profiles"),
        catalog_operations=_catalog_operations(),
    )

    assert result["runnable"] is False
    assert code in {item["code"] for item in result["validation"]}


def test_product_catalog_is_an_explicit_plan_gate() -> None:
    preset = load_preset(ROOT / "presets/quick-smoke.yml")
    operations = _catalog_operations() - {"file_read"}

    result = expand_plan(
        preset.plan,
        environment=RuntimeEnvironment("/tmp/benchmark", None, None, None),
        profiles=load_workspace_profiles(ROOT / "defaults/workspace-profiles"),
        catalog_operations=operations,
    )

    assert result["runnable"] is False
    finding = next(
        item for item in result["validation"] if item["code"] == "catalog_operations_missing"
    )
    assert finding["message"] == "file_read"


def test_requested_migration_ratio_accepts_zero_but_match_density_does_not() -> None:
    preset = load_preset(ROOT / "presets/quick-smoke.yml")
    squash = next(
        item for item in preset.plan.operations if item.operation == "squash_layerstack"
    )
    squash.configuration.factors["requested_migration_ratio"].values = [0.0]
    squash.configuration.factors["requested_migration_ratio"].control = None
    valid = expand_plan(
        preset.plan,
        environment=RuntimeEnvironment("/tmp/benchmark", None, None, None),
        profiles=load_workspace_profiles(ROOT / "defaults/workspace-profiles"),
    )
    assert "invalid_factor_value" not in {
        item["code"] for item in valid["validation"]
    }

    edit = next(item for item in preset.plan.operations if item.operation == "file_edit")
    edit.configuration.factors["match_density"].values = [0.0]
    invalid = expand_plan(
        preset.plan,
        environment=RuntimeEnvironment("/tmp/benchmark", None, None, None),
        profiles=load_workspace_profiles(ROOT / "defaults/workspace-profiles"),
    )
    assert "invalid_factor_value" in {
        item["code"] for item in invalid["validation"]
    }


@pytest.mark.parametrize(
    ("factor", "values"),
    [
        ("layers_per_block", [1]),
        ("layers_per_block", [1024]),
        ("squashable_blocks", [2]),
    ],
)
def test_squash_plan_rejects_unsafe_or_unformable_topologies(
    factor: str, values: list[int]
) -> None:
    preset = load_preset(ROOT / "presets/quick-smoke.yml")
    squash = next(
        item for item in preset.plan.operations if item.operation == "squash_layerstack"
    )
    squash.configuration.factors[factor].values = values
    if factor == "layers_per_block" and values == [1024]:
        squash.configuration.factors["squashable_blocks"].values = [5]
    if factor == "squashable_blocks":
        squash.configuration.factors["live_sessions"].values = [0]
        squash.configuration.factors["requested_migration_ratio"].values = [0.0]

    result = expand_plan(
        preset.plan,
        environment=RuntimeEnvironment("/tmp/benchmark", None, None, None),
        profiles=load_workspace_profiles(ROOT / "defaults/workspace-profiles"),
    )

    assert result["runnable"] is False
    assert "invalid_squash_shape" in {
        item["code"] for item in result["validation"]
    }
