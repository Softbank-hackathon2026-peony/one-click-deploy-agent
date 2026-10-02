from infrafit import kb
from infrafit.kb_lint import lint


def test_knowledge_files_pass_lint():
    assert lint() == []


def test_catalog_contains_ids_used_by_fixtures():
    for cid in ["ds:local/sqlite/wal", "cp:vercel/functions/unspecified-plan",
                "nw:app/uvicorn/default", "nw:aws/alb/default"]:
        assert cid in kb.catalog()


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
