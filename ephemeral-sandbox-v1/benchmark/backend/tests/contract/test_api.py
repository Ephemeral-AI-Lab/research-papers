import asyncio
import json
import shutil
from pathlib import Path

import httpx
import pytest

from benchmark_lab.api import create_app
from benchmark_lab.artifacts import ArtifactId, ArtifactStore
from benchmark_lab.paths import BenchmarkRoots
from benchmark_lab.runner import CampaignRunner
from benchmark_lab.service import CampaignService, _ActiveRun


ROOT = Path(__file__).resolve().parents[3]
GOLDEN = ROOT / "tests/fixtures/golden/rust/quick-smoke-completed"
AUTHORITY = "127.0.0.1:7891"
HISTORICAL_RUN_ID = "019f554f-50c5-7a10-87c6-83523317dcb2"


def _roots(tmp_path: Path) -> BenchmarkRoots:
    test = tmp_path / "test"
    product = tmp_path / "product"
    (test / "benchmark/defaults").mkdir(parents=True)
    shutil.copytree(ROOT / "defaults", test / "benchmark/defaults", dirs_exist_ok=True)
    shutil.copytree(ROOT / "presets", test / "benchmark/presets")
    binaries = product / "bin"
    binaries.mkdir(parents=True)
    return BenchmarkRoots.resolve(test, product, binaries, initialize=True)


def _client(service: CampaignService) -> httpx.AsyncClient:
    app = create_app(service, authority=AUTHORITY, check_product_on_startup=False)
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url=f"http://{AUTHORITY}"
    )


def _mark_product_ready(service: CampaignService) -> None:
    catalog = json.loads((ROOT / "tests/fixtures/golden/catalog/product-catalog-v1.json").read_text())
    service._catalog_operations = frozenset(
        operation["name"]
        for domain in catalog["domains"].values()
        for operation in domain["operations"]
    )


def _mutation(service: CampaignService) -> dict[str, str]:
    return {
        "Origin": f"http://{AUTHORITY}",
        "X-EOS-Benchmark-Nonce": service.nonce,
        "Content-Type": "application/json",
    }


@pytest.mark.asyncio
async def test_api_security_and_definition_contract(tmp_path: Path) -> None:
    service = CampaignService(_roots(tmp_path))
    async with _client(service) as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store"
        assert "access-control-allow-origin" not in response.headers

        definitions = (await client.get("/api/v1/definitions")).json()
        assert definitions["schema_version"] == 1
        assert len(definitions["catalog"]["operations"]) == 7
        assert {item["configuration_base"]["scope"] for item in definitions["defaults"]} == {
            "all", "command", "files", "workspace", "layerstack"
        }
        operations_by_scope = {
            item["configuration_base"]["scope"]: {
                operation["operation"] for operation in item["operations"]
            }
            for item in definitions["defaults"]
        }
        assert operations_by_scope == {
            "all": {
                "exec_command", "file_read", "file_write", "file_edit", "file_blame",
                "create_workspace", "squash_layerstack",
            },
            "command": {"exec_command"},
            "files": {"file_read", "file_write", "file_edit", "file_blame"},
            "workspace": {"create_workspace"},
            "layerstack": {"squash_layerstack"},
        }
        assert {item["name"] for item in definitions["defaults"]} == {"standard-local"}

        denied = await client.post("/api/v1/plans/validate", json={"plan": {}})
        assert denied.status_code == 403
        assert denied.json()["error"]["code"] == "invalid_origin"

        wrong_host = await client.get(
            "http://attacker.invalid/api/v1/health", headers={"Host": "attacker.invalid"}
        )
        assert wrong_host.status_code == 400
        assert wrong_host.json()["error"]["code"] == "invalid_host"


@pytest.mark.asyncio
async def test_plan_validation_requires_nonce_origin_json_and_reviewed_hash(tmp_path: Path) -> None:
    service = CampaignService(_roots(tmp_path))
    _mark_product_ready(service)
    plan = service.definitions()["presets"][0]["plan"]
    headers = _mutation(service)
    async with _client(service) as client:
        validated = await client.post(
            "/api/v1/plans/validate", headers=headers, json={"plan": plan, "starting_preset": None}
        )
        assert validated.status_code == 200, validated.text
        expanded = validated.json()
        assert expanded["runnable"]

        mismatch = await client.post(
            "/api/v1/runs",
            headers=headers,
            json={
                "plan": plan, "plan_hash": "sha256:wrong", "client_request_id": "request-1",
                "starting_preset": None,
            },
        )
        assert mismatch.status_code == 409
        assert mismatch.json()["error"]["code"] == "plan_hash_mismatch"


@pytest.mark.asyncio
async def test_admitted_run_is_readable_before_first_manifest_write(tmp_path: Path) -> None:
    service = CampaignService(_roots(tmp_path))
    _mark_product_ready(service)
    plan = service.definitions()["presets"][0]["plan"]
    expanded = service.validate_plan(plan)
    run_id = service._uuid7()
    service._active = _ActiveRun(
        run_id,
        expanded,
        CampaignRunner(service.roots),
    )
    service.roots.results.joinpath(run_id).mkdir()

    async with _client(service) as client:
        response = await client.get(f"/api/v1/runs/{run_id}")
        listing = await client.get("/api/v1/runs")

    assert response.status_code == 200, response.text
    assert response.json()["manifest"]["state"] == "queued"
    assert listing.status_code == 200, listing.text
    assert listing.json()["runs"] == []


def _copy_run(store: ArtifactStore) -> None:
    run_id = HISTORICAL_RUN_ID
    destination = store._results_root / run_id
    destination.mkdir()
    for path in GOLDEN.iterdir():
        if path.is_file():
            destination.joinpath(path.name).write_bytes(path.read_bytes())


@pytest.mark.asyncio
async def test_historical_run_artifacts_and_sse_resume(tmp_path: Path) -> None:
    service = CampaignService(_roots(tmp_path))
    _copy_run(service.store)
    async with _client(service) as client:
        projected = await client.get(f"/api/v1/runs/{HISTORICAL_RUN_ID}")
        assert projected.status_code == 200, projected.text
        latest = projected.json()["latest_sequence"]
        assert latest > 2

        index = (await client.get(f"/api/v1/runs/{HISTORICAL_RUN_ID}/artifacts")).json()
        assert any(item["artifact_id"] == "report" for item in index["artifacts"])
        content = (await client.get(f"/api/v1/runs/{HISTORICAL_RUN_ID}/artifacts/report")).json()
        assert content["encoding"] == "utf-8"

        stream = service.events(HISTORICAL_RUN_ID, latest - 2)
        first = await anext(stream)
        second = await anext(stream)
        await stream.aclose()
        assert [first["sequence"], second["sequence"]] == [latest - 1, latest]

        invalid = await client.get(
            f"/api/v1/runs/{HISTORICAL_RUN_ID}/events", headers={"Last-Event-ID": "bad"}
        )
        assert invalid.status_code == 400


@pytest.mark.asyncio
async def test_event_sink_never_blocks_campaign_on_slow_browser(tmp_path: Path) -> None:
    service = CampaignService(_roots(tmp_path))
    queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=1)
    service._subscribers["run"] = {queue}
    sink = service._event_sink("run")
    await sink({"sequence": 1, "data": {"kind": "log"}})
    await sink({"sequence": 2, "data": {"kind": "log"}})
    assert service._subscribers["run"] == set()
