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
