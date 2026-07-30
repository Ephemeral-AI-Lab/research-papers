import pytest
from pydantic import ValidationError

from benchmark_lab.models import RunManifestCore, StateMarker


def test_public_models_reject_unknown_fields_and_coercion() -> None:
    with pytest.raises(ValidationError):
        StateMarker.model_validate({"owner": "ephemeral-sandbox-benchmark", "role": "benchmark-state", "schema_version": 1, "extra": True})
    with pytest.raises(ValidationError):
        StateMarker.model_validate({"owner": "ephemeral-sandbox-benchmark", "role": "benchmark-state", "schema_version": "1"})
    with pytest.raises(ValidationError):
        RunManifestCore.model_validate({"schema_version": 1, "run_id": "run", "name": "name", "state": "invented", "plan_hash": "sha256:value", "failure": None})
