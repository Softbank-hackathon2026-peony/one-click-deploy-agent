from infrafit import kb
from infrafit.kb_lint import _lint_catalog, _lint_images, _lint_secrets, lint


def test_knowledge_files_pass_lint():
    assert lint() == []


def test_catalog_contains_ids_used_by_fixtures():
    for cid in ["ds:local/sqlite/wal", "cp:vercel/functions/unspecified-plan",
                "nw:app/uvicorn/default", "nw:aws/alb/default"]:
        assert cid in kb.catalog()


def test_catalog_lint_checks_recommendable():
    base = {"id": "qu:lib/x/default", "family": "qu", "name": "x", "source": "docs/x.md"}
    assert _lint_catalog([dict(base, recommendable=False, reason="근거 절이 C 출처뿐")]) == []
    assert _lint_catalog([dict(base, recommendable=True)]) == []
    assert _lint_catalog([dict(base, recommendable="no")]) == ["catalog: qu:lib/x/default의 recommendable이 불리언이 아님"]
    assert _lint_catalog([dict(base, recommendable=False)]) == ["catalog: qu:lib/x/default가 recommendable: false인데 reason 없음"]


def test_not_recommendable_components_stay_in_catalog():
    flagged = {cid for cid, c in kb.catalog().items() if c.get("recommendable") is False}
    assert {"cp:fly/machines/default", "cp:render/web/unspecified-plan", "rt:lib/ws/default"} <= flagged
    assert all(kb.catalog()[cid].get("reason") for cid in flagged)


def test_iter_conditions_flattens_tree():
    cond = {"any": [{"dependency": "pg"}, {"all": [{"dependency": "x"}, {"code": {"glob": "*", "regex": "a"}}]}]}
    leaves = list(kb.iter_conditions(cond))
    assert {"dependency": "pg"} in leaves
    assert len(leaves) == 3


def test_kb_version_is_short_hash():
    assert len(kb.kb_version()) == 12


def test_component_id_constants_in_detect_code_exist_in_catalog():
    import re
    from pathlib import Path

    import infrafit.detect

    rx = re.compile(r"""["']((?:cp|ds|ca|qu|sc|rt|fs|nw):[a-z0-9._-]+/[a-z0-9._-]+/[a-z0-9._-]+)["']""")
    found = {(path.name, cid) for path in Path(infrafit.detect.__file__).parent.glob("*.py")
             for cid in rx.findall(path.read_text(encoding="utf-8"))}
    assert len(found) > 20  # 정규식이 실제로 상수를 찾는지
    assert sorted((name, cid) for name, cid in found if cid not in kb.catalog()) == []


def test_secrets_and_image_port_lint():
    assert _lint_secrets({"key": ["KEY"], "value": ["("]})[0].startswith("secrets: value 정규식 오류")
    assert _lint_secrets({"key": [], "value": ["x"]}) == ["secrets: key 정규식 목록이 비었음"]
    issues = _lint_images([{"match": ["pg"], "role": "datastore", "port": "5432"}])
    assert issues == ["image pg: port는 1~65535 정수여야 함 '5432'"]
