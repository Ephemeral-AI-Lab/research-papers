from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def _git(root: Path, *arguments: str) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _repository(root: Path) -> dict[str, object]:
    tracked = [
        item.decode("utf-8")
        for item in _git(root, "ls-files", "-z", "--cached").split(b"\0")
        if item
    ]
    return {
        "root": str(root),
        "commit": _git(root, "rev-parse", "HEAD").decode().strip(),
        "branch": _git(root, "branch", "--show-current").decode().strip(),
        "status_porcelain_v2": _git(
            root, "status", "--porcelain=v2", "--branch", "--untracked-files=all"
        ).decode(),
        "tracked_files": {
            relative: f"sha256:{_sha256(root / relative)}"
            for relative in sorted(tracked)
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--paper-root", type=Path, required=True)
    parser.add_argument("--product-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    output = arguments.output.resolve()
    if output.exists():
        raise SystemExit("baseline output already exists")
    payload = {
        "schema_version": 1,
        "purpose": "EXP1 pre-edit tracked-file SHA-256 baseline",
        "initial_observation": {
            "paper_status": "clean at the recorded commit before this capture script was added",
            "product_status": "clean at the recorded commit",
            "new_campaign_files": [
                "experiments/scripts/capture_exp1_baseline.py",
                "experiments/exp1-pre-edit-baseline.json",
            ],
        },
        "paper": _repository(arguments.paper_root.resolve(strict=True)),
        "product": _repository(arguments.product_root.resolve(strict=True)),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
