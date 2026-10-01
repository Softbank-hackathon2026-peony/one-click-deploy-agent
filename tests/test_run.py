import json

import pytest

from infrafit.run import RunContext, code_version, input_hash, now_iso
from infrafit.schema import SchemaError

BODY = {"repo": "x", "commit": "abc", "files_total": 1, "files_scanned": 1,
        "excluded": [], "languages": {}, "overrides": None}


def test_input_hash_is_stable_and_prefixed():
    assert input_hash("S0", "abc") == input_hash("S0", "abc")
    assert input_hash("S0", "abc") != input_hash("S0", "abd")
    assert input_hash("S0").startswith("sha256:")


def test_code_version_is_short_hash():
    assert len(code_version()) == 12


def test_write_stage_validates_and_writes(tmp_path):
    ctx = RunContext.create(tmp_path, run_id="r1")
    data = ctx.write_stage("S0", BODY, input_hash="sha256:h", started_at=now_iso())
    written = json.loads((tmp_path / "r1" / "intake.json").read_text())
    assert written == data
    assert written["meta"]["stage"] == "S0"
    assert written["meta"]["run_id"] == "r1"


def test_write_stage_rejects_invalid_body(tmp_path):
    ctx = RunContext.create(tmp_path, run_id="r1")
    with pytest.raises(SchemaError):
        ctx.write_stage("S0", {"repo": "x"}, input_hash="sha256:h", started_at=now_iso())
    assert not (tmp_path / "r1" / "intake.json").exists()


def test_cache_returns_body_with_new_meta(tmp_path):
    first = RunContext.create(tmp_path, run_id="r1")
    first.write_stage("S0", BODY, input_hash="sha256:h", started_at=now_iso())
    second = RunContext.create(tmp_path, run_id="r2")
    hit = second.cached("S0", "sha256:h")
    assert hit is not None
    assert hit["meta"]["run_id"] == "r2"
    assert hit["commit"] == "abc"
    assert second.cached("S0", "sha256:other") is None
