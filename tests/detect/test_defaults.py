from infrafit.detect.artifacts import ParsedArtifact
from infrafit.detect.defaults import apply_defaults, hop_settings

SRC = {"ref": "docs/x.md"}
ENTRIES = (
    {"artifact": "dockerfile", "key": "user", "value": "root", "source": SRC},
    {"artifact": "k8s", "match_kind": "Deployment", "key": "terminationGracePeriodSeconds", "value": 30, "source": SRC},
    {"artifact": "terraform", "resource": "aws_db_instance", "key": "multi_az", "value": False, "source": SRC},
    {"artifact": "hop", "component": "nw:app/uvicorn/default", "key": "timeout_keep_alive", "value": 5, "source": SRC},
)


def test_dockerfile_default_added_only_when_missing():
    a = ParsedArtifact("dockerfile", "Dockerfile", True, settings=[])
    b = ParsedArtifact("dockerfile", "b/Dockerfile", True,
                       settings=[{"key": "user", "value": "app", "defaulted": False}])
    apply_defaults([a, b], ENTRIES)
    assert a.settings == [{"key": "user", "value": "root", "defaulted": True, "default_source": SRC}]
    assert b.get("user") == "app"


def test_k8s_default_only_for_full_objects():
    full = {"kind": "Deployment", "metadata": {"name": "api"},
            "spec": {"template": {"spec": {"containers": [{"name": "api", "image": "acme/api:1"}]}}}}
    patch = {"kind": "Deployment", "metadata": {"name": "web"},
             "spec": {"template": {"spec": {"containers": [{"name": "web", "resources": {}}]}}}}
    a = ParsedArtifact("k8s", "k.yaml", True, objects=[full, patch])
    apply_defaults([a], ENTRIES)
    assert a.get("Deployment/api.terminationGracePeriodSeconds") == 30
    assert a.get("Deployment/web.terminationGracePeriodSeconds") is None


def test_terraform_default_per_resource():
    a = ParsedArtifact("terraform", "main.tf", True, objects=[("aws_db_instance", "main", {})])
    apply_defaults([a], ENTRIES)
    assert a.get("aws_db_instance.main.multi_az") is False


def test_hop_settings_mix_explicit_and_default():
    assert hop_settings("nw:app/uvicorn/default", {}, ENTRIES) == [
        {"key": "timeout_keep_alive", "value": 5, "defaulted": True, "default_source": SRC}]
    assert hop_settings("nw:app/uvicorn/default", {"timeout_keep_alive": 75}, ENTRIES) == [
        {"key": "timeout_keep_alive", "value": 75, "defaulted": False}]
