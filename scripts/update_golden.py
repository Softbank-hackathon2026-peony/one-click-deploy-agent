"""픽스처마다 S0~S1을 돌려 골든 스냅샷과 F2 단계별 예시를 갱신한다."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from infrafit.pipeline import analyze  # noqa: E402
from infrafit.run import dump_json  # noqa: E402


def normalize(data: dict) -> dict:
    out = {k: v for k, v in data.items() if k != "meta"}
    if "repo" in out:
        out["repo"] = "<repo>"
    return out


def main() -> None:
    for repo in sorted((ROOT / "fixtures").glob("*/repo")):
        fixture = repo.parent
        with tempfile.TemporaryDirectory() as tmp:
            ctx = analyze(str(repo), Path(tmp), until="S1", run_id="golden")
            golden = fixture / "golden"
            golden.mkdir(exist_ok=True)
            for name in ("intake", "inventory"):
                data = json.loads((ctx.out_dir / f"{name}.json").read_text(encoding="utf-8"))
                (golden / f"{name}.json").write_text(dump_json(normalize(data)), encoding="utf-8")
        print(f"updated {fixture.name}")
    examples = ROOT / "schemas" / "examples" / "f2-sqlite-erp"
    examples.mkdir(parents=True, exist_ok=True)
    for name in ("intake", "inventory"):
        data = json.loads((ROOT / "fixtures" / "f2-sqlite-erp" / "golden" / f"{name}.json").read_text(encoding="utf-8"))
        data["meta"] = {"run_id": "example", "stage": "S0" if name == "intake" else "S1",
                        "input_hash": "sha256:example"}
        (examples / f"{name}.json").write_text(dump_json(data), encoding="utf-8")
    shutil.rmtree(ROOT / "out" / ".cache", ignore_errors=True)


if __name__ == "__main__":
    main()
