"""픽스처마다 S4 순위 요약 표(QA). 사용: python scripts/qa_ranking.py [--root <infrafit 저장소>]

--root 를 주면 그 저장소의 infrafit 으로 돌린다(예: main 워크트리와 비교). 픽스처는 이 저장소의 fixtures/.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
RUNNER = """
import sys
from pathlib import Path
from infrafit import pipeline
pipeline.analyze(sys.argv[1], Path(sys.argv[2]), until="S4", run_id="qa")
"""


def run(root: Path, fixture: Path) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, "-c", RUNNER, str(fixture / "repo"), tmp], check=True, cwd=root,
                       env={"PYTHONPATH": str(root), "PATH": "/usr/bin:/bin"}, capture_output=True)
        return json.loads((Path(tmp) / "qa" / "recommendation.json").read_text(encoding="utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=HERE)
    args = ap.parse_args()
    print("| 픽스처 | 유형 | coverage | 근거 | 1~3위 (월 USD, decided_by) |")
    print("|---|---|---|---|---|")
    for fx in sorted((HERE / "fixtures").glob("f*")):
        rec = run(args.root.resolve(), fx)
        rk = rec.get("ranking") or {}
        by = "; ".join(f"{m['type']}:" + ",".join(f"{b['dimension']}@{'/'.join(b['at'][:1])}" for b in m["by"][:2])
                       for m in rk.get("matched", []))
        tops = []
        for c in rec["candidates"][:3]:
            comp = ",".join(sorted({p["component"].split("/")[1] for p in c.get("placement", [])}))
            cost = c["cost"]["monthly_baseline_usd"]
            why = (c.get("decided_by") or {}).get("criterion", "-")
            tops.append(f"{c['id']} {c.get('topology')}:{comp} ({cost}, {why})")
        print(f"| {fx.name} | {rk.get('service_type', '-')} | {rk.get('coverage', '-')} | {by or '-'} | "
              f"{'<br>'.join(tops) or rec['outcome']} |")


if __name__ == "__main__":
    main()
