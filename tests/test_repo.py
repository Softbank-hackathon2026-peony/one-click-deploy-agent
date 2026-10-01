from infrafit.evidence import evidence, grep_lines, line_of
from infrafit.repo import language_ratios, match_glob, open_snapshot


def _make(tmp_path):
    (tmp_path / "app.py").write_text("import sqlite3\nconn = sqlite3.connect('x.db')\n")
    (tmp_path / "web").mkdir()
    (tmp_path / "web" / "index.ts").write_text("export const a = 1\n")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "x.js").write_text("x\n")
    (tmp_path / "logo.png").write_bytes(b"\x89PNG")
    return open_snapshot(str(tmp_path), tmp_path / "_work")


def test_match_glob_handles_root_and_nested():
    assert match_glob("package.json", "**/package.json")
    assert match_glob("a/b/package.json", "**/package.json")
    assert match_glob("app/api/x/route.ts", "**/app/**/route.ts")
    assert not match_glob("app/api/x/page.ts", "**/app/**/route.ts")


def test_snapshot_excludes_dirs_and_binaries(tmp_path):
    snap = _make(tmp_path)
    assert snap.files == ["app.py", "web/index.ts"]
    assert snap.excluded == ["node_modules/"]
    assert snap.files_total == 3
    assert snap.commit.startswith("tree-")


def test_commit_is_deterministic(tmp_path):
    assert _make(tmp_path).commit == open_snapshot(str(tmp_path), tmp_path / "_w2").commit


def test_language_ratios():
    assert language_ratios(["a.py", "b.py", "c.ts", "README.md"]) == {"python": 0.667, "typescript": 0.333}


def test_evidence_and_search(tmp_path):
    snap = _make(tmp_path)
    assert line_of(snap, "app.py", "sqlite3.connect") == 2
    assert grep_lines(snap, "app.py", r"sqlite3") == [1, 2]
    ev = evidence(snap, "app.py", 2, kind="tech")
    assert ev == {"path": "app.py", "line": 2, "snippet": "conn = sqlite3.connect('x.db')", "kind": "tech"}
    assert evidence(snap, "app.py") == {"path": "app.py", "line": None, "snippet": "app.py"}


def test_snapshot_skips_symlinks(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "real.py").write_text("print('real')\n")
    # Create a dangling symlink file
    (repo / "broken_link").symlink_to(repo / "nonexistent.txt")
    # Create a symlink to a file outside the repo
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n")
    (repo / "external_link").symlink_to(outside)
    snap = open_snapshot(str(repo), tmp_path / "_work")
    assert snap.files == ["real.py"]
    assert "broken_link" not in snap.files
    assert "external_link" not in snap.files
    # Verify it doesn't crash on dangling symlinks
    assert snap.commit.startswith("tree-")
