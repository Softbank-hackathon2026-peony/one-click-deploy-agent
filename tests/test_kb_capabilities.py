import copy

import pytest

from infrafit import kb
from infrafit.kb_lint import _lint_capabilities, _lint_rules

DOC = "capabilities/99-test.md"
LINES = [
    "# test",
    "| CP.request_timeout | 최대 900초 | — | https://docs.aws.amazon.com/lambda/x.html · \"900 seconds (15 minutes).\" |",
    "| CP.long_connection | 지원 | — | https://docs.aws.amazon.com/lambda/y.html · \"supports WebSockets\" ⚠️근거없음 |",
    "| CP.cost_floor | 월 $20.7 | — | [PL] AmazonEC2 ap-northeast-2 · \"$0.0208 per On Demand Linux t4g.small Instance Hour\" |",
    "| CP.x | 값 | — | https://koyeb.com/docs · \"koyeb says\" |",
    "- [PL] = `https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/{AmazonEC2}/current/ap-northeast-2/index.json`",
]
CATALOG = {"cp:aws/lambda/function-url": {"id": "cp:aws/lambda/function-url", "family": "cp"},
           "cp:aws/off/default": {"id": "cp:aws/off/default", "family": "cp", "recommendable": False}}


@pytest.fixture
def research(tmp_path):
    (tmp_path / "capabilities").mkdir()
    (tmp_path / DOC).write_text("\n".join(LINES) + "\n", encoding="utf-8")
    (tmp_path / "dimensions.md").write_text("| A1 | x |\n| A3 | y |\n| B1 | z |\n", encoding="utf-8")
    return tmp_path


def _src(line=2, url="https://docs.aws.amazon.com/lambda/x.html", quote="900 seconds (15 minutes)."):
    return {"doc": DOC, "line": line, "url": url, "quote": quote}


def _entry(**caps):
    return {"id": "cp:aws/lambda/function-url", "target": "aws_lambda", "cloud": "aws", "family": "cp",
            "capabilities": caps or {"CP.max_request_seconds": {"value": 900, "source": _src()}}}


def _lint(research, entry):
    return _lint_capabilities([entry], catalog=CATALOG, research_dir=research)


def test_valid_capability_passes(research):
    assert _lint(research, _entry()) == []


def test_price_list_alias_url_passes(research):
    src = _src(line=4, url="https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/ap-northeast-2/index.csv",
               quote="$0.0208 per On Demand Linux t4g.small Instance Hour")
    assert _lint(research, _entry(**{"COST.monthly_floor_usd": {"value": 20.7, "source": src}})) == []


def test_quote_not_on_line_fails(research):
    issues = _lint(research, _entry(**{"CP.max_request_seconds": {"value": 900, "source": _src(line=3)}}))
    assert any("인용 문구가" in i for i in issues)


def test_marked_line_fails(research):
    src = _src(line=3, url="https://docs.aws.amazon.com/lambda/y.html", quote="supports WebSockets")
    issues = _lint(research, _entry(**{"CP.websocket": {"value": True, "source": src}}))
    assert issues == [f"cp:aws/lambda/function-url#CP.websocket: {DOC}:3에 ⚠️근거없음 표시"]


def test_ineligible_host_fails(research):
    src = _src(line=5, url="https://koyeb.com/docs", quote="koyeb says")
    issues = _lint(research, _entry(**{"CP.websocket": {"value": True, "source": src}}))
    assert any("적격 발행처가 아닌 url" in i for i in issues)


def test_url_not_cited_on_line_fails(research):
    src = _src(url="https://docs.aws.amazon.com/lambda/other.html")
    issues = _lint(research, _entry(**{"CP.max_request_seconds": {"value": 900, "source": src}}))
    assert any("url이" in i for i in issues)


@pytest.mark.parametrize("field", ["doc", "line", "url", "quote"])
def test_missing_source_field_fails(research, field):
    src = _src()
    del src[field]
    issues = _lint(research, _entry(**{"CP.max_request_seconds": {"value": 900, "source": src}}))
    assert issues == [f"cp:aws/lambda/function-url#CP.max_request_seconds: source에 {field} 없음"]


def test_line_out_of_range_and_unknown_doc_fail(research):
    assert any("범위 밖" in i for i in _lint(research, _entry(**{"CP.max_request_seconds": {"value": 900, "source": _src(line=99)}})))
    bad_doc = dict(_src(), doc="../README.md")
    assert any("조사 문서 없음" in i for i in _lint(research, _entry(**{"CP.max_request_seconds": {"value": 900, "source": bad_doc}})))


def test_unknown_key_and_bad_value_fail(research):
    issues = _lint(research, _entry(**{"CP.foo": {"value": 1, "source": _src()},
                                       "CP.max_request_seconds": {"value": "900", "source": _src()}}))
    assert "cp:aws/lambda/function-url#CP.foo: 알 수 없는 능력 키" in issues
    assert "cp:aws/lambda/function-url#CP.max_request_seconds: 잘못된 값 '900'" in issues


def test_component_format_and_catalog_fail(research):
    entry = _entry()
    entry.update(id="cp:aws/nope/default", target="lambda", cloud="mars")
    issues = _lint(research, entry)
    assert "cp:aws/nope/default: catalog에 없는 구성 요소" in issues
    assert "cp:aws/nope/default: 잘못된 target lambda" in issues
    assert "cp:aws/nope/default: 잘못된 cloud mars" in issues
    off = dict(_entry(), id="cp:aws/off/default")
    assert "cp:aws/off/default: recommendable: false 구성 요소에 능력 값" in _lint(research, off)


def test_ops_burden_needs_reason_and_source(research):
    entry = dict(_entry(), ops_burden="low")
    assert "cp:aws/lambda/function-url: ops_burden에 ops_burden_source.reason 없음" in _lint(research, entry)
    entry["ops_burden_source"] = dict(_src(), reason="서버 없음")
    assert _lint(research, entry) == []


RULE = {"id": "CAP-WEBSOCKET-001", "when": {"dimension": "A3", "equals": "장시간 양방향(웹소켓)"},
        "require": {"capability": "CP.websocket", "equals": True}, "otherwise": "infeasible",
        "config_from": None, "message": "m"}


def _rule(**changes):
    r = copy.deepcopy(RULE)
    r.update(changes)
    return r


def test_valid_rules_pass(research):
    config_rule = _rule(id="CAP-MEMSTATE-002", when={"dimension": "B1", "equals": "있음"},
                        require={"capability": "CP.single_instance_config", "exists": False},
                        otherwise="config", config_from="CP.single_instance_config")
    any_rule = _rule(id="CAP-ALWAYSON-002", when={"dimension": "A1", "in": ["워커"]},
                     require={"any": [{"capability": "CP.always_on", "equals": True},
                                      {"capability": "CP.cpu_after_response", "equals": True}]})
    assert _lint_rules([RULE, config_rule, any_rule], research_dir=research) == []


def test_rule_id_must_match_schema_pattern(research):
    issues = _lint_rules([_rule(id="R-A3-WEBSOCKET")], research_dir=research)
    assert issues == ["R-A3-WEBSOCKET: 규칙 ID가 스키마 RuleId 형식이 아님"]


def test_rule_id_pattern_matches_schema():
    import json
    import re
    from pathlib import Path

    from infrafit.kb_lint import RULE_ID
    schema = json.loads((Path(kb.KB_DIR).parent / "schemas/infrafit.schema.json").read_text(encoding="utf-8"))
    assert RULE_ID.pattern == schema["$defs"]["RuleId"]["pattern"]
    assert all(re.match(RULE_ID, r["id"]) for r in kb.rules())


def test_rule_unknown_dimension_fails(research):
    issues = _lint_rules([_rule(when={"dimension": "Z9", "equals": "x"})], research_dir=research)
    assert issues == ["CAP-WEBSOCKET-001: when.dimension이 dimensions.md의 차원 ID가 아님 Z9"]


def test_rule_unknown_capability_fails(research):
    issues = _lint_rules([_rule(require={"capability": "CP.nope", "equals": True})], research_dir=research)
    assert issues == ["CAP-WEBSOCKET-001: 알 수 없는 능력 키 CP.nope"]


def test_rule_bad_otherwise_fails(research):
    issues = _lint_rules([_rule(otherwise="warn")], research_dir=research)
    assert issues == ["CAP-WEBSOCKET-001: otherwise는 infeasible 또는 config"]


def test_rule_config_needs_config_from(research):
    issues = _lint_rules([_rule(otherwise="config", config_from=None)], research_dir=research)
    assert issues == ["CAP-WEBSOCKET-001: otherwise가 config인데 config_from이 능력 키가 아님 None"]
    issues = _lint_rules([_rule(config_from="CP.websocket")], research_dir=research)
    assert issues == ["CAP-WEBSOCKET-001: otherwise가 infeasible이면 config_from은 null"]


def test_rule_bad_operator_and_duplicate_fail(research):
    issues = _lint_rules([_rule(require={"capability": "CP.websocket", "matches": True}), RULE],
                         research_dir=research)
    assert "CAP-WEBSOCKET-001: require 연산자는 ['equals', 'exists', 'gte'] 중 하나" in issues
    assert "rules: 중복 ID CAP-WEBSOCKET-001" in issues


def test_loaders_return_knowledge():
    caps = kb.capabilities()
    assert {"cp:aws/lambda/function-url", "cp:gcp/cloud-run/request-billing", "cp:gcp/cloud-run/instance-billing",
            "cp:aws/ecs-fargate/alb", "cp:aws/ec2/docker-compose", "cp:gcp/compute-engine/docker-compose",
            "ds:aws/rds-postgres/single-az", "ds:gcp/cloudsql-postgres/single", "ca:aws/elasticache/node-based",
            "ca:gcp/memorystore/redis-basic", "ds:local/sqlite/wal"} <= set(caps)
    assert {r["id"] for r in kb.rules()} >= {"CAP-TIMEOUT-001", "CAP-WEBSOCKET-001", "CAP-BGWORK-001",
                                             "CAP-MEMSTATE-001", "CAP-LOCALDISK-001", "CAP-SINGLERUN-001",
                                             "CAP-ALWAYSON-001"}


def test_rule_when_values_follow_s2_vocabulary():
    from infrafit.kb_lint import _lint_rule_vocabulary
    assert _lint_rule_vocabulary() == []
    assert _lint_rule_vocabulary([RULE]) == []
    english = _rule(when={"dimension": "A1", "in": ["워커", "worker"]})
    assert _lint_rule_vocabulary([english]) == [
        "CAP-WEBSOCKET-001: when 값 'worker'이 A1 어휘 ['웹', '워커', '정기 작업', '실시간 연결', '일회성 실행']에 없음"]
    unknown_dim = _rule(when={"dimension": "D5", "equals": "한 지역"})
    assert _lint_rule_vocabulary([unknown_dim]) == [
        "CAP-WEBSOCKET-001: when.dimension D5은 profile_detectors.yaml에 정의되지 않은 차원(S2가 내지 않음)"]


def test_when_exists_operator_is_rejected(research):
    issues = _lint_rules([_rule(when={"dimension": "B1", "exists": True})], research_dir=research)
    assert issues == ["CAP-WEBSOCKET-001: when 연산자는 ['equals', 'in'] 중 하나"]


def test_topology_keys_and_targets_pass(research):
    """계획 2b: 쿠버네티스 target, 확장·다중 워크로드·레플리카 비용·VM 안 데이터 저장소 키."""
    entry = dict(_entry(**{"CP.horizontal_scaling": {"value": True, "source": _src()},
                           "CP.multi_workload": {"value": False, "source": _src()},
                           "COST.per_replica_usd": {"value": 12.86, "source": _src()}}), target="gcp_gke")
    assert _lint(research, entry) == []
    assert _lint(research, dict(_entry(), target="aws_eks")) == []
    bad = _lint(research, _entry(**{"CP.horizontal_scaling": {"value": "yes", "source": _src()},
                                    "COST.per_replica_usd": {"value": -1, "source": _src()}}))
    assert "cp:aws/lambda/function-url#CP.horizontal_scaling: 잘못된 값 'yes'" in bad
    assert "cp:aws/lambda/function-url#COST.per_replica_usd: 잘못된 값 -1" in bad


def test_vm_datastore_keys_and_docker_hub_host(research):
    line = "| redis | DS.engine | — | — | https://hub.docker.com/_/redis · \"$ docker run --name some-redis -d redis\" |"
    (research / DOC).write_text("\n".join(LINES + [line]) + "\n", encoding="utf-8")
    hub = {"doc": DOC, "line": len(LINES) + 1, "url": "https://hub.docker.com/_/redis",
           "quote": "$ docker run --name some-redis -d redis"}
    entry = {"id": "ca:vm/compose-redis/default", "cloud": "local", "family": "ca",
             "capabilities": {"DS.engine": {"value": "redis", "source": hub},
                              "DS.colocated_vm": {"value": True, "source": hub},
                              "DS.durability": {"value": "호스트 VM 디스크", "source": hub},
                              "DS.backup_config": {"value": "사용자가 스냅샷/덤프 설정", "source": hub},
                              "COST.monthly_floor_usd": {"value": 0, "source": hub}}}
    catalog = {"ca:vm/compose-redis/default": {"id": "ca:vm/compose-redis/default", "family": "ca"}}
    assert _lint_capabilities([entry], catalog=catalog, research_dir=research) == []
    entry["capabilities"]["DS.durability"]["value"] = ""
    assert _lint_capabilities([entry], catalog=catalog, research_dir=research) == [
        "ca:vm/compose-redis/default#DS.durability: 잘못된 값 ''"]


def test_topology_components_in_knowledge():
    caps = kb.capabilities()
    gke, eks = caps["cp:gcp/gke/autopilot"], caps["cp:aws/eks/managed-node-group"]
    assert (gke["target"], eks["target"]) == ("gcp_gke", "aws_eks")
    for c in (gke, eks):
        assert c["capabilities"]["CP.horizontal_scaling"]["value"] is True
        assert c["capabilities"]["CP.multi_workload"]["value"] is True
        assert "COST.monthly_floor_usd" in c["capabilities"]
    for cid in ("ds:vm/compose-postgres/default", "ca:vm/compose-redis/default"):
        c = caps[cid]["capabilities"]
        assert c["DS.colocated_vm"]["value"] is True and c["COST.monthly_floor_usd"]["value"] == 0
        assert c["DS.backup_config"]["value"]
