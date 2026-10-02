import subprocess

import pytest

from infrafit.detect.artifacts import build_overlays, environment_dirs, kustomize_binary, kustomize_leaves
from infrafit.repo import open_snapshot

BASE = """apiVersion: apps/v1
kind: Deployment
metadata: {name: api}
spec:
  template:
    spec:
      containers: [{name: api, image: acme/api:1}]
"""
PATCH = """apiVersion: apps/v1
kind: Deployment
metadata: {name: api}
spec:
  template:
    spec:
      terminationGracePeriodSeconds: 45
"""


def _tree(tmp_path):
    files = {
        "k8s/base/kustomization.yaml": "resources: [api.yaml]\n",
        "k8s/base/api.yaml": BASE,
        "k8s/components/extra/kustomization.yaml": "apiVersion: kustomize.config.k8s.io/v1alpha1\nkind: Component\n",
        "k8s/overlays/prod/kustomization.yaml": "resources: [../../base]\npatches: [{path: patch.yaml}]\n",
        "k8s/overlays/prod/patch.yaml": PATCH,
        "k8s/overlays/dev/kustomization.yaml": "resources: [../../base]\ncomponents: [../../components/extra]\n",
    }
    for rel, text in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    return open_snapshot(str(tmp_path), tmp_path / "_w")


def test_leaves_exclude_referenced_dirs(tmp_path):
    assert kustomize_leaves(_tree(tmp_path)) == ["k8s/overlays/dev", "k8s/overlays/prod"]


def test_leaves_tolerate_malformed_kustomization(tmp_path):
    files = {
        "a/kustomization.yaml": "- just\n- a list\n",
        "b/kustomization.yaml": "resources: not-a-list\nbases: 5\ncomponents: {x: 1}\n",
        "c/kustomization.yaml": "resources: [../a, 7, null]\n",
    }
    for rel, text in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    assert kustomize_leaves(snap) == ["b", "c"]


def test_build_failure_is_recorded(tmp_path):
    class Failed:
        returncode = 1
        stdout = ""

    arts = build_overlays(_tree(tmp_path), runner=lambda *a, **k: Failed())
    assert [(a.path, a.parsed) for a in arts] == LEAVES_FAILED


LEAVES_FAILED = [("k8s/overlays/dev/kustomization.yaml#build", False),
                 ("k8s/overlays/prod/kustomization.yaml#build", False)]


@pytest.mark.parametrize("exc", [subprocess.TimeoutExpired(["kustomize"], 60), OSError("exec failed")])
def test_runner_errors_are_recorded(tmp_path, monkeypatch, exc):
    monkeypatch.setattr("infrafit.detect.artifacts.kustomize_binary", lambda: ["kustomize", "build"])
    seen = []

    def runner(*a, **k):
        seen.append(k.get("timeout"))
        raise exc

    arts = build_overlays(_tree(tmp_path), runner=runner)
    assert [(a.path, a.parsed) for a in arts] == LEAVES_FAILED
    assert seen == [60, 60]


def test_missing_binary_records_every_leaf(tmp_path, monkeypatch):
    monkeypatch.setattr("infrafit.detect.artifacts.kustomize_binary", lambda: None)

    def runner(*a, **k):
        raise AssertionError("should not run")

    arts = build_overlays(_tree(tmp_path), runner=runner)
    assert [(a.path, a.parsed) for a in arts] == LEAVES_FAILED


@pytest.mark.parametrize("remote", [
    "https://github.com/acme/deploy//base?ref=v1",
    "github.com/acme/deploy/base",
    "git@github.com:acme/deploy.git//base",
])
def test_remote_resources_are_not_built(tmp_path, monkeypatch, remote):
    monkeypatch.setattr("infrafit.detect.artifacts.kustomize_binary", lambda: ["kustomize", "build"])
    files = {
        "remote-base/kustomization.yaml": f"resources:\n  - {remote}\n",
        "overlays/a/kustomization.yaml": "resources: [../../remote-base]\n",
        "overlays/b/kustomization.yaml": "resources: [api.yaml]\n",
        "overlays/b/api.yaml": BASE,
    }
    for rel, text in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    built = []

    class Ok:
        returncode = 0
        stdout = BASE

    def runner(cmd, **k):
        built.append(cmd[-1])
        return Ok()

    arts = build_overlays(open_snapshot(str(tmp_path), tmp_path / "_w"), runner=runner)
    assert [(a.path, a.parsed) for a in arts] == [("overlays/a/kustomization.yaml#build", False),
                                                  ("overlays/b/kustomization.yaml#build", True)]
    assert built == [str(tmp_path / "overlays/b")]


@pytest.mark.skipif(kustomize_binary() is None, reason="kustomize 없음")
def test_build_renders_patched_objects(tmp_path):
    arts = {a.path: a for a in build_overlays(_tree(tmp_path))}
    prod = arts["k8s/overlays/prod/kustomization.yaml#build"]
    assert prod.parsed
    assert prod.get("Deployment/api.terminationGracePeriodSeconds") == 45
    assert prod.get("Deployment/api.image") == "acme/api:1"


def test_environment_dirs_include_referenced_overlays(tmp_path):
    files = {
        "k8s/base/kustomization.yaml": "resources: [api.yaml]\n",
        "k8s/base/api.yaml": BASE,
        "k8s/overlays/local/kustomization.yaml": "resources: [../../base]\n",
        "k8s/overlays/local-loadtest/kustomization.yaml": "resources: [../local, ../shared]\ncomponents: [../extra]\n",
        "k8s/overlays/aws/base/kustomization.yaml": "resources: [../../../base]\n",
        "k8s/overlays/aws/prod/kustomization.yaml": "resources: [../base]\n",
        "k8s/overlays/shared/kustomization.yaml": "resources: [../../base]\n",
        "k8s/overlays/extra/kustomization.yaml": "apiVersion: kustomize.config.k8s.io/v1alpha1\nkind: Component\n",
    }
    for rel, text in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    dirs = ["k8s/overlays/aws/prod", "k8s/overlays/local", "k8s/overlays/local-loadtest"]
    assert environment_dirs(snap) == dirs  # aws/base·shared·Component는 참조되므로 환경이 아니다

    class Failed:
        returncode = 1
        stdout = ""

    built = [a.path for a in build_overlays(snap, runner=lambda *a, **k: Failed())]
    assert "k8s/overlays/local/kustomization.yaml#build" in built
    assert "k8s/overlays/aws/base/kustomization.yaml#build" not in built
