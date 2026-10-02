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


def _real(tmp_path, files: dict[str, str]):
    from infrafit import kb
    for rel, text in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    return {m.signature: m for m in match_signatures(snap, parse_manifests(snap), kb.signatures())}


def test_supabase_dependency_only_is_candidate(tmp_path):
    m = _real(tmp_path / "a", {"package.json": '{"dependencies": {"@supabase/supabase-js": "2"}}\n',
                               "auth.ts": "const { data } = await supabase.auth.getUser()\n"})
    assert m["SIG-DS-SUPABASE"].status == "candidate"
    m = _real(tmp_path / "b", {"package.json": '{"dependencies": {"@supabase/supabase-js": "2"}}\n',
                               "db.ts": "const { data } = await supabase.from('posts').select('*')\n"})
    assert m["SIG-DS-SUPABASE"].status == "confirmed"
    assert any(e["path"] == "db.ts" for e in m["SIG-DS-SUPABASE"].evidence)
    m = _real(tmp_path / "c", {"requirements.txt": "supabase==2\n",
                               "x.py": "DB = 'postgresql://u:p@db.abc.supabase.co:5432/postgres'\n"})
    assert m["SIG-DS-SUPABASE"].status == "confirmed"


def test_jvm_sqs_dependency_only_is_candidate(tmp_path):
    gradle = "dependencies { implementation 'io.awspring.cloud:spring-cloud-aws-starter-sqs' }\n"
    m = _real(tmp_path / "a", {"build.gradle": gradle})
    assert m["SIG-QU-SQS"].status == "candidate"
    m = _real(tmp_path / "b", {"build.gradle": gradle, "src/main/java/L.java": "class L {\n  @SqsListener(\"q\")\n  void on(String m) {}\n}\n"})
    assert m["SIG-QU-SQS"].status == "confirmed"
    m = _real(tmp_path / "c", {"send.ts": "await client.send(new SendMessageCommand({}))\n"})
    assert m["SIG-QU-SQS"].status == "confirmed"
    assert len(m["SIG-QU-SQS"].evidence) == len(set(map(str, m["SIG-QU-SQS"].evidence)))


def test_postgres_url_code_condition(tmp_path):
    m = _real(tmp_path / "a", {"docker-compose.yml": "services:\n  api:\n    environment:\n"
                                                     "      DATABASE_URL: postgresql+asyncpg://u@db/app\n"})
    assert [(e["path"], e["line"]) for e in m["SIG-DS-POSTGRES"].evidence] == [("docker-compose.yml", 4)]
    m = _real(tmp_path / "b", {".env.example": "DATABASE_URL=postgres://u@localhost/db\n"})
    assert "SIG-DS-POSTGRES" in m
    m = _real(tmp_path / "c", {"a.py": "url = 'mysql://x'\n"})
    assert "SIG-DS-POSTGRES" not in m


def test_local_file_writes_are_candidates(tmp_path):
    for i, code in enumerate(("with open(path, 'w') as f:\n    f.write(x)\n", "json.dump(data, f)\n",
                              "Path('out.txt').write_text(s)\n", "with open(p, mode=\"a\") as f: pass\n")):
        m = _real(tmp_path / str(i), {"app.py": code})
        assert m["SIG-FS-LOCAL"].status == "candidate", code
    m = _real(tmp_path / "r", {"app.py": "with open(path) as f:\n    json.loads(f.read())\n"})
    assert "SIG-FS-LOCAL" not in m


def test_code_evidence_puts_scripts_and_qa_last(tmp_path):
    files = {f"{d}/a{i}.py": "import sqlite3\nsqlite3.connect('x')\n"
             for d in ("scripts", "qa", "tools", "examples", "bench") for i in range(2)}
    files["zz/db.py"] = "import sqlite3\nsqlite3.connect('x')\n"
    files["backend/scripts/seed.py"] = "import sqlite3\nsqlite3.connect('x')\n"
    m = _real(tmp_path, files)
    paths = [e["path"] for e in m["SIG-DS-SQLITE"].evidence]
    assert paths[0] == "zz/db.py"
    assert len(paths) == 5


def test_supabase_refine_needs_a_supabase_receiver(tmp_path):
    dep = '{"dependencies": {"@supabase/supabase-js": "2"}}\n'
    cases = {
        "buffer": ("const b = Buffer.from('abc')\nconst a = Array.from(\"xyz\")\n", "candidate"),
        "storage": ("await supabase\n  .storage\n  .from('avatars')\n  .upload(p, f)\n", "candidate"),
        "chain": ("const { data } = await supabase\n  .from('posts')\n  .select('*')\n", "confirmed"),
        "client": ("await getSupabase().rpc('delete_user')\n", "confirmed"),
    }
    for name, (code, status) in cases.items():
        m = _real(tmp_path / name, {"package.json": dep, "db.ts": code})
        assert m["SIG-DS-SUPABASE"].status == status, name
    m = _real(tmp_path / "line", {"package.json": dep, "db.ts": "\n" + cases["chain"][0]})
    assert ("db.ts", 2) in [(e["path"], e["line"]) for e in m["SIG-DS-SUPABASE"].evidence]
