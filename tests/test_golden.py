import json
import sys
from pathlib import Path

import pytest

from infrafit.consistency import check_s1
from infrafit.pipeline import analyze
from infrafit.schema import validate

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from update_golden import normalize  # noqa: E402

FIXTURES = sorted(p.parent.parent for p in (ROOT / "fixtures").glob("*/golden/inventory.json"))


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda p: p.name)
def test_matches_golden(fixture, tmp_path):
    ctx = analyze(str(fixture / "repo"), tmp_path, until="S1", run_id="t")
    for name in ("intake", "inventory"):
        actual = normalize(json.loads((ctx.out_dir / f"{name}.json").read_text()))
        golden = json.loads((fixture / "golden" / f"{name}.json").read_text())
        assert actual == golden, f"{fixture.name}/{name}: 골든과 다름. 의도한 변경이면 scripts/update_golden.py 실행"


def test_deterministic_without_cache(tmp_path):
    repo = ROOT / "fixtures" / "f2-sqlite-erp" / "repo"
    a = analyze(str(repo), tmp_path / "a", until="S1", run_id="r")
    b = analyze(str(repo), tmp_path / "b", until="S1", run_id="r")
    for name in ("intake", "inventory"):
        left = normalize(json.loads((a.out_dir / f"{name}.json").read_text()))
        right = normalize(json.loads((b.out_dir / f"{name}.json").read_text()))
        assert json.dumps(left, sort_keys=True) == json.dumps(right, sort_keys=True)


@pytest.mark.parametrize("name,def_name", [("intake", "Intake"), ("inventory", "Inventory")])
def test_examples_pass_schema_and_consistency(name, def_name):
    data = json.loads((ROOT / "schemas" / "examples" / "f2-sqlite-erp" / f"{name}.json").read_text())
    validate(def_name, data)
    if name == "inventory":
        assert check_s1(data, ROOT / "fixtures" / "f2-sqlite-erp" / "repo") == []
