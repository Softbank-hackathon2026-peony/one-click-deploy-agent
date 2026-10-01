import json

from infrafit.pipeline import analyze


def test_analyze_until_s0_writes_valid_intake(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "main.py").write_text("print('hi')\n")
    (repo / "infrafit.yaml").write_text("assumptions:\n  D2.baseline_concurrency: 200\n")
    ctx = analyze(str(repo), tmp_path / "out", until="S0", run_id="r1")
    intake = json.loads((ctx.out_dir / "intake.json").read_text())
    assert intake["files_scanned"] == 2
    assert intake["languages"] == {"python": 1.0}
    assert intake["overrides"] == {"assumptions": {"D2.baseline_concurrency": 200}}
    assert intake["meta"]["stage"] == "S0"
