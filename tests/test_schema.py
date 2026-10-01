import pytest

from infrafit.schema import SchemaError, validate

META = {"run_id": "r1", "stage": "S0", "input_hash": "sha256:x"}


def test_valid_intake_passes():
    validate("Intake", {
        "meta": META, "repo": "x", "commit": "abc", "files_total": 1,
        "files_scanned": 1, "excluded": [], "languages": {"python": 1.0},
    })


def test_missing_field_raises_with_path():
    with pytest.raises(SchemaError) as exc:
        validate("Intake", {"meta": META, "repo": "x"})
    assert "Intake" in str(exc.value)
    assert "commit" in str(exc.value)


def test_unknown_def_raises():
    with pytest.raises(SchemaError):
        validate("NoSuchDef", {})
