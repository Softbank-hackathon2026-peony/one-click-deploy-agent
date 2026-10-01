import json
import pytest

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


def test_analyze_excludes_workdir_from_counts(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "main.py").write_text("print('hi')\n")
    (repo / "helper.py").write_text("def help(): pass\n")
    # Analyze twice with different run IDs into subdirectories of the repo
    ctx1 = analyze(str(repo), repo / "results", until="S0", run_id="r1")
    intake1 = json.loads((ctx1.out_dir / "intake.json").read_text())
    ctx2 = analyze(str(repo), repo / "results", until="S0", run_id="r2")
    intake2 = json.loads((ctx2.out_dir / "intake.json").read_text())
    # Both should have the same file counts, excluding the results directory
    assert intake1["files_scanned"] == intake2["files_scanned"]
    assert intake1["files_total"] == intake2["files_total"]
    # Verify the counts are correct (2 files: main.py and helper.py)
    assert intake1["files_scanned"] == 2


def test_analyze_rejects_invalid_yaml(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "main.py").write_text("print('hi')\n")
    (repo / "infrafit.yaml").write_text("invalid: yaml: syntax: [\n")
    with pytest.raises(ValueError, match="infrafit.yaml is not valid YAML"):
        analyze(str(repo), tmp_path / "out", until="S0", run_id="r1")


def test_analyze_rejects_non_mapping_yaml(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "main.py").write_text("print('hi')\n")
    (repo / "infrafit.yaml").write_text("- item1\n- item2\n")
    with pytest.raises(ValueError, match="infrafit.yaml must be a mapping"):
        analyze(str(repo), tmp_path / "out", until="S0", run_id="r1")
