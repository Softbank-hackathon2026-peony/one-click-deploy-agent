"""보조 코드(scripts/·qa/·tools/·examples/·bench/)에만 근거가 있는 시그니처는 범위를 만들지 않는다(FB12)."""

import json

from infrafit.consistency import check_run
from infrafit.pipeline import analyze

APP = "from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/h')\ndef h():\n    return 'ok'\n"


def _write(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def _inventory(tmp_path):
    ctx = analyze(str(tmp_path / "repo"), tmp_path / "out", until="S1", run_id="r")
    assert check_run(ctx.out_dir) == []
    return json.loads((ctx.out_dir / "inventory.json").read_text())


def test_aux_only_evidence_creates_no_scope(tmp_path):
    repo = tmp_path / "repo"
    _write(repo, "requirements.txt", "fastapi==0.115\n")
    _write(repo, "main.py", APP)
    _write(repo, "scripts/dump.py", "import json\njson.dump({}, open('x.json', 'w'))\n")
    _write(repo, "bench/run.py", "import sqlite3\nsqlite3.connect('b.db')\n")
    inv = _inventory(tmp_path)
    assert inv["datastores"] == []
    assert [c["scope"] for c in inv["current_components"]] == ["w-web"]


def test_aux_evidence_joins_scope_created_elsewhere(tmp_path):
    repo = tmp_path / "repo"
    _write(repo, "requirements.txt", "fastapi==0.115\n")
    _write(repo, "main.py", APP)
    _write(repo, "app/files.py", "from pathlib import Path\nPath('o.txt').write_text('x')\n")
    _write(repo, "scripts/dump.py", "import json\njson.dump({}, open('x.json', 'w'))\n")
    inv = _inventory(tmp_path)
    [ds] = inv["datastores"]
    assert (ds["id"], ds["status"]) == ("svc-container-disk", "candidate")
    assert [e["path"] for e in ds["evidence"]] == ["app/files.py", "scripts/dump.py"]
