from infrafit.detect.manifests import parse_manifests
from infrafit.detect.signatures import match_signatures
from infrafit.repo import open_snapshot

SIGS = (
    {"id": "SIG-A", "component": "ds:local/sqlite/default", "role": "primary-db", "status": "confirmed",
     "when": {"any": [{"code": {"glob": "**/*.py", "regex": r"sqlite3\.connect\("}}]},
     "refine": [{"component": "ds:local/sqlite/wal",
                 "when": {"any": [{"code": {"glob": "**/*.py", "regex": "journal_mode=wal", "flags": "i"}}]}}]},
    {"id": "SIG-B", "component": "ca:unspecified/redis/default", "role": "cache", "status": "confirmed",
     "when": {"all": [{"dependency": "redis"}, {"code": {"glob": "**/*.py", "regex": "Redis\\("}}]}},
    {"id": "SIG-C", "component": "qu:lib/celery/default", "role": "queue", "status": "confirmed",
     "when": {"any": [{"dependency": "celery"}]}},
)


def _snap(tmp_path):
    (tmp_path / "requirements.txt").write_text("redis==5.0\n")
    (tmp_path / "db.py").write_text("import sqlite3\nc = sqlite3.connect('a.db')\nc.execute('PRAGMA journal_mode=WAL')\n")
    return open_snapshot(str(tmp_path), tmp_path / "_w")


def test_any_with_refine_upgrades_component(tmp_path):
    snap = _snap(tmp_path)
    matches = match_signatures(snap, parse_manifests(snap), SIGS)
    a = next(m for m in matches if m.signature == "SIG-A")
    assert a.component == "ds:local/sqlite/wal"
    assert {"path": "db.py", "line": 2, "snippet": "c = sqlite3.connect('a.db')", "kind": "tech"} in a.evidence
    assert any(e["line"] == 3 for e in a.evidence)


def test_all_requires_every_condition(tmp_path):
    snap = _snap(tmp_path)
    matches = match_signatures(snap, parse_manifests(snap), SIGS)
    assert [m.signature for m in matches] == ["SIG-A"]
