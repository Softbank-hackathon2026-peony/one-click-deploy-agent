from infrafit.detect.artifacts import parse_artifacts
from infrafit.repo import open_snapshot

K8S = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  replicas: 2
  template:
    spec:
      terminationGracePeriodSeconds: 45
      containers:
        - name: api
          image: example/api:1
          command: ["uvicorn", "main:app"]
          args: ["--timeout-keep-alive", "75"]
          readinessProbe: {httpGet: {path: /healthz, port: 8000}}
          lifecycle: {preStop: {exec: {command: ["sleep", "10"]}}}
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web
  annotations:
    alb.ingress.kubernetes.io/load-balancer-attributes: idle_timeout.timeout_seconds=120
spec:
  ingressClassName: alb
  rules:
    - http:
        paths:
          - backend: {service: {name: api, port: {number: 80}}}
"""

TF = """provider "aws" {
  region = "ap-northeast-2"
}

resource "aws_db_instance" "main" {
  engine   = "postgres"
  multi_az = true
}

resource "google_sql_database_instance" "pg" {
  database_version = "POSTGRES_16"
  settings {
    availability_type = "REGIONAL"
  }
}
"""


def _snap(tmp_path):
    (tmp_path / "k8s").mkdir()
    (tmp_path / "k8s" / "app.yaml").write_text(K8S)
    (tmp_path / "k8s" / "not-k8s.yaml").write_text("foo: bar\n")
    (tmp_path / "main.tf").write_text(TF)
    return open_snapshot(str(tmp_path), tmp_path / "_w")


def test_k8s_settings(tmp_path):
    arts = {a.path: a for a in parse_artifacts(_snap(tmp_path))}
    assert "k8s/not-k8s.yaml" not in arts
    k = arts["k8s/app.yaml"]
    assert k.kind == "k8s"
    assert k.get("Deployment/api.replicas") == 2
    assert k.get("Deployment/api.terminationGracePeriodSeconds") == 45
    assert k.get("Deployment/api.command") == "uvicorn main:app --timeout-keep-alive 75"
    assert k.get("Deployment/api.readinessProbe") is True
    assert k.get("Deployment/api.livenessProbe") is False
    assert k.get("Deployment/api.preStop") is True
    assert k.get("Ingress/web.ingressClassName") == "alb"
    assert k.get("Ingress/web.backends") == ["api"]
    assert k.get("Ingress/web.annotations.alb.ingress.kubernetes.io/load-balancer-attributes") == \
        "idle_timeout.timeout_seconds=120"


def test_terraform_settings(tmp_path):
    arts = {a.path: a for a in parse_artifacts(_snap(tmp_path))}
    t = arts["main.tf"]
    assert t.kind == "terraform" and t.parsed
    assert t.get("aws_db_instance.main.engine") == "postgres"
    assert t.get("aws_db_instance.main.multi_az") is True
    assert t.get("google_sql_database_instance.pg.settings.availability_type") == "REGIONAL"
    assert t.get("provider.aws.region") == "ap-northeast-2"
    assert ("aws_db_instance", "main") in [(o[0], o[1]) for o in t.objects]


def test_k8s_malformed_fields_do_not_crash(tmp_path):
    (tmp_path / "bad.yaml").write_text(
        "apiVersion: apps/v1\nkind: Deployment\nmetadata: x\nspec:\n  template:\n    spec:\n"
        "      containers:\n        - just-a-string\n---\n"
        "apiVersion: networking.k8s.io/v1\nkind: Ingress\nmetadata:\n  name: i\n  annotations: [a]\n"
        "spec:\n  rules: [1, {http: 3}]\n"
    )
    (tmp_path / "broken.yaml").write_text("kind: [\n")
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    arts = {a.path: a for a in parse_artifacts(snap)}
    assert "broken.yaml" not in arts
    assert arts["bad.yaml"].get("Ingress/i.backends") == []
