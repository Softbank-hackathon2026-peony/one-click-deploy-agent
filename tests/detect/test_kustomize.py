import pytest

from infrafit.detect.artifacts import build_overlays, kustomize_binary, kustomize_leaves
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
    if kustomize_binary() is None:
        assert arts == []
    else:
        assert [(a.path, a.parsed) for a in arts] == [
            ("k8s/overlays/dev/kustomization.yaml#build", False),
            ("k8s/overlays/prod/kustomization.yaml#build", False)]


@pytest.mark.skipif(kustomize_binary() is None, reason="kustomize 없음")
def test_build_renders_patched_objects(tmp_path):
    arts = {a.path: a for a in build_overlays(_tree(tmp_path))}
    prod = arts["k8s/overlays/prod/kustomization.yaml#build"]
    assert prod.parsed
    assert prod.get("Deployment/api.terminationGracePeriodSeconds") == 45
    assert prod.get("Deployment/api.image") == "acme/api:1"
