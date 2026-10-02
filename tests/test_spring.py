"""Spring Boot(Gradle·Maven) 저장소: 의존성, 워크로드, 엔드포인트, 앱 서버 구간."""

import json

from infrafit import kb
from infrafit.consistency import check_run
from infrafit.detect.artifacts import parse_artifacts
from infrafit.detect.endpoints import extract_endpoints
from infrafit.detect.manifests import parse_manifests
from infrafit.detect.signatures import match_signatures
from infrafit.detect.workloads import detect_workloads
from infrafit.pipeline import analyze
from infrafit.repo import open_snapshot

GRADLE_KTS = """plugins {
    id("org.springframework.boot") version "3.3.0"
    id("io.spring.dependency-management") version "1.1.5"
    kotlin("plugin.spring") version "1.9.24"
}

dependencies {
    implementation(platform("org.springframework.boot:spring-boot-dependencies:3.3.0"))
    implementation("org.springframework.boot:spring-boot-starter-web")
    implementation("org.springframework.boot:spring-boot-starter-data-redis")
    runtimeOnly("org.postgresql:postgresql")
    testImplementation("org.springframework.boot:spring-boot-starter-test")
}
"""

USER_CONTROLLER_KT = """package com.example.users

import org.springframework.web.bind.annotation.*

// @GetMapping("/commented") 주석 안의 어노테이션
@RestController
@RequestMapping("/api/v1/users")
class UserController(private val service: UserService) {

    @GetMapping("/{id}")
    fun get(@PathVariable id: Long): User = service.find(id)

    @PostMapping
    fun create(@RequestBody body: User): User = service.save(body)
}
"""

POM = """<?xml version="1.0" encoding="UTF-8"?>
<project>
  <modelVersion>4.0.0</modelVersion>
  <parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.3.0</version>
  </parent>
  <groupId>com.example</groupId>
  <artifactId>shop-api</artifactId>
  <dependencies>
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    <dependency>
      <groupId>com.mysql</groupId>
      <artifactId>mysql-connector-j</artifactId>
      <scope>runtime</scope>
    </dependency>
    <dependency>
      <groupId>com.h2database</groupId>
      <artifactId>h2</artifactId>
      <scope>test</scope>
    </dependency>
  </dependencies>
</project>
"""

ITEM_CONTROLLER_JAVA = """package com.example;

import org.springframework.web.bind.annotation.*;

@RestController
public class ItemController {

    @RequestMapping(value = {"/a", "/b"}, method = RequestMethod.GET)
    public String list() {
        return "ok";
    }
}
"""


def _write(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def _detect(root):
    snap = open_snapshot(str(root), root / "_w")
    manifests = parse_manifests(snap)
    artifacts = parse_artifacts(snap)
    workloads = detect_workloads(snap, manifests, artifacts)
    return snap, manifests, workloads, extract_endpoints(snap, workloads, manifests=manifests)


def _inventory(tmp_path, run_id="r"):
    ctx = analyze(str(tmp_path / "repo"), tmp_path / "out", until="S1", run_id=run_id)
    assert check_run(ctx.out_dir) == []
    return json.loads((ctx.out_dir / "inventory.json").read_text())


def _kotlin_repo(root):
    _write(root, "settings.gradle.kts", 'rootProject.name = "user-service"\n')
    _write(root, "build.gradle.kts", GRADLE_KTS)
    _write(root, "src/main/kotlin/com/example/users/UserController.kt", USER_CONTROLLER_KT)


def test_gradle_dependencies_and_plugin(tmp_path):
    _kotlin_repo(tmp_path)
    _write(tmp_path, "lib/build.gradle", "apply plugin: 'org.springframework.boot'\n"
                                         "dependencies {\n"
                                         "    compileOnly group: 'org.projectlombok', name: 'lombok', version: '1.18'\n"
                                         "    testRuntimeOnly 'org.junit.platform:junit-platform-launcher'\n"
                                         "}\n")
    snap = open_snapshot(str(tmp_path), tmp_path / "_w")
    m = parse_manifests(snap)
    assert m.deps["org.springframework.boot"] == ("build.gradle.kts", 2)
    assert m.deps["org.springframework.boot:spring-boot-starter-web"] == ("build.gradle.kts", 9)
    assert m.deps["org.postgresql:postgresql"] == ("build.gradle.kts", 11)
    assert "org.springframework.boot:spring-boot-starter-test" not in m.deps
    assert "org.junit.platform:junit-platform-launcher" not in m.deps
    assert ("lib/build.gradle", 1) in m.locations["org.springframework.boot"]
    assert m.deps["org.projectlombok:lombok"] == ("lib/build.gradle", 3)


def test_kotlin_gradle_web_workload_and_endpoints(tmp_path):
    _kotlin_repo(tmp_path)
    _, _, workloads, eps = _detect(tmp_path)
    assert [(w.id, w.name, w.kind, w.status, w.code_root, w.framework) for w in workloads] == [
        ("w-user-service", "user-service", "web", "confirmed", "", "spring-mvc")]
    assert workloads[0].entrypoint["path"] == "build.gradle.kts"
    assert workloads[0].entrypoint["line"] == 9
    assert sorted((e["method"], e["route"], e["handler"]["line"], e["framework"]) for e in eps) == [
        ("GET", "/api/v1/users/{id}", 10, "spring-mvc"), ("POST", "/api/v1/users", 13, "spring-mvc")]


def test_maven_pom_parent_and_request_mapping_arrays(tmp_path):
    _write(tmp_path, "pom.xml", POM)
    _write(tmp_path, "src/main/java/com/example/ItemController.java", ITEM_CONTROLLER_JAVA)
    snap, m, workloads, eps = _detect(tmp_path)
    assert m.deps["org.springframework.boot"] == ("pom.xml", 6)
    assert m.deps["org.springframework.boot:spring-boot-starter-web"] == ("pom.xml", 14)
    assert m.deps["com.mysql:mysql-connector-j"] == ("pom.xml", 18)
    assert "com.h2database:h2" not in m.deps
    assert [(w.id, w.name, w.kind) for w in workloads] == [("w-shop-api", "shop-api", "web")]
    assert sorted((e["method"], e["route"], e["handler"]["line"]) for e in eps) == [("GET", "/a", 8), ("GET", "/b", 8)]
    comps = {x.component for x in match_signatures(snap, m, kb.signatures())}
    assert "ds:unspecified/mysql/default" in comps


def test_request_mapping_without_method_is_any_and_kotlin_arrays(tmp_path):
    _write(tmp_path, "build.gradle", "plugins {\n    id 'org.springframework.boot' version '3.3.0'\n}\n"
                                     "dependencies {\n    implementation 'org.springframework.boot:spring-boot-starter-webflux'\n}\n")
    _write(tmp_path, "src/main/kotlin/Api.kt", """@RestController
@RequestMapping(path = ["/v1", "/v2"])
class Api {
    @RequestMapping("/ping")
    fun ping() = "pong"

    @RequestMapping(value = ["/x"], method = [RequestMethod.PUT, RequestMethod.PATCH])
    fun x() = "x"

    @DeleteMapping(path = ["/d/{id}"])
    fun d() = "d"
}
""")
    _, _, workloads, eps = _detect(tmp_path)
    assert [(w.id, w.kind, w.framework) for w in workloads] == [("w-app", "web", "spring-webflux")]
    assert sorted((e["method"], e["route"]) for e in eps) == [
        ("ANY", "/v1/ping"), ("ANY", "/v2/ping"), ("DELETE", "/v1/d/{id}"), ("DELETE", "/v2/d/{id}"),
        ("PATCH", "/v1/x"), ("PATCH", "/v2/x"), ("PUT", "/v1/x"), ("PUT", "/v2/x")]
    assert {e["framework"] for e in eps} == {"spring-webflux"}


def test_boot_without_web_starter_is_worker_candidate(tmp_path):
    _write(tmp_path, "batch/build.gradle", "plugins { id 'org.springframework.boot' }\n"
                                           "dependencies { implementation 'org.springframework.boot:spring-boot-starter-batch' }\n")
    _, _, workloads, _ = _detect(tmp_path)
    assert [(w.id, w.name, w.kind, w.status, w.code_root) for w in workloads] == [
        ("w-batch", "batch", "worker", "candidate", "batch")]


def test_multi_module_web_workload_per_module(tmp_path):
    _write(tmp_path, "settings.gradle", "rootProject.name = 'shop'\ninclude 'api', 'admin', 'core'\n")
    _write(tmp_path, "build.gradle", "plugins { id 'org.springframework.boot' version '3.3.0' apply false }\n")
    for mod in ("api", "admin"):
        _write(tmp_path, f"{mod}/build.gradle", "plugins { id 'org.springframework.boot' }\n"
                                                "dependencies { implementation 'org.springframework.boot:spring-boot-starter-web' }\n")
        _write(tmp_path, f"{mod}/src/main/java/C.java",
               f'@RestController\nclass C {{\n  @GetMapping("/{mod}")\n  String x() {{ return ""; }}\n}}\n')
    _write(tmp_path, "core/build.gradle", "dependencies { implementation 'org.postgresql:postgresql' }\n")
    _, _, workloads, eps = _detect(tmp_path)
    assert [(w.id, w.code_root) for w in workloads] == [("w-admin", "admin"), ("w-api", "api")]
    assert sorted((e["workload"], e["route"]) for e in eps) == [("w-admin", "/admin"), ("w-api", "/api")]


def test_test_sources_have_no_endpoints(tmp_path):
    _kotlin_repo(tmp_path)
    _write(tmp_path, "src/test/java/com/example/FakeController.java",
           '@RestController\nclass FakeController {\n  @GetMapping("/phantom")\n  String x() { return ""; }\n}\n')
    _write(tmp_path, "src/main/java/com/example/OtherTest.java",
           '@RestController\nclass OtherTest {\n  @GetMapping("/phantom2")\n  String x() { return ""; }\n}\n')
    _, _, _, eps = _detect(tmp_path)
    assert "/phantom" not in {e["route"] for e in eps}
    assert "/phantom2" not in {e["route"] for e in eps}


def test_spring_datastores_and_app_server_default(tmp_path):
    _kotlin_repo(tmp_path / "repo")
    inv = _inventory(tmp_path)
    assert {d["id"] for d in inv["datastores"]} >= {"ds-postgresql", "svc-redis"}
    hops = inv["request_paths"][0]["hops"]
    assert [(h["kind"], h["component"]) for h in hops] == [("app-server", "nw:app/spring-boot-tomcat/default")]
    assert hops[0]["settings"] == [{"key": "keep_alive_timeout", "value": 60, "defaulted": True,
                                    "default_source": {"ref": "docs/research/capabilities/09-network-lb-ingress.md"}}]
    assert [(e["path"], e["line"]) for e in hops[0]["evidence"]] == [("build.gradle.kts", 9)]


def test_jdbc_url_in_application_yml_is_postgres(tmp_path):
    _write(tmp_path, "repo/pom.xml", POM.replace("com.mysql", "com.example").replace("mysql-connector-j", "util"))
    _write(tmp_path, "repo/src/main/resources/application.yml",
           "spring:\n  datasource:\n    url: jdbc:postgresql://db:5432/app\n")
    inv = _inventory(tmp_path)
    assert "ds-postgresql" in {d["id"] for d in inv["datastores"]}


def test_tomcat_keep_alive_from_application_yml(tmp_path):
    _kotlin_repo(tmp_path / "repo")
    _write(tmp_path, "repo/src/main/resources/application.yml",
           "server:\n  port: 8080\n  tomcat:\n    connection-timeout: 30s\n    keep-alive-timeout: 20s\n")
    inv = _inventory(tmp_path)
    hop = inv["request_paths"][0]["hops"][0]
    ev = {"path": "src/main/resources/application.yml", "line": 5, "snippet": "keep-alive-timeout: 20s"}
    assert hop["settings"] == [{"key": "keep_alive_timeout", "value": 20, "defaulted": False, "evidence": ev}]
    assert hop["evidence"] == [ev]


def test_tomcat_timeout_formats_in_properties(tmp_path):
    for value, expected in (("20000", 20), ("PT20S", 20), ("2m", 120)):
        root = tmp_path / value
        _kotlin_repo(root / "repo")
        _write(root, "repo/src/main/resources/application.properties",
               f"server.port=8080\nserver.tomcat.connection-timeout={value}\n")
        inv = _inventory(root)
        hop = inv["request_paths"][0]["hops"][0]
        assert hop["settings"][0]["value"] == expected
        assert hop["settings"][0]["evidence"]["line"] == 2


def test_webflux_app_server_is_unmapped(tmp_path):
    _write(tmp_path, "repo/build.gradle", "dependencies { implementation 'org.springframework.boot:spring-boot-starter-webflux' }\n")
    inv = _inventory(tmp_path)
    assert [h["component"] for h in inv["request_paths"][0]["hops"]] == ["unmapped"]


def test_unmapped_jvm_packages(tmp_path):
    _write(tmp_path, "repo/build.gradle", "dependencies {\n"
                                          "  implementation 'org.springframework.boot:spring-boot-starter-web'\n"
                                          "  implementation 'org.springframework.kafka:spring-kafka'\n}\n")
    inv = _inventory(tmp_path)
    assert "org.springframework.kafka:spring-kafka" in {u["label"] for u in inv["unmapped"]}


def test_broken_build_files_do_not_crash(tmp_path):
    _write(tmp_path, "repo/pom.xml", "<project><dependencies><dependency><groupId>x</groupId>\n<artifactId>")
    _write(tmp_path, "repo/a/pom.xml", "\x00\x01 not xml at all <<<>>>")
    _write(tmp_path, "repo/b/build.gradle", "dependencies { implementation(\n plugins { id(\n")
    _write(tmp_path, "repo/c/build.gradle.kts", "")
    _write(tmp_path, "repo/settings.gradle", "rootProject.name =\n")
    _write(tmp_path, "repo/src/main/java/X.java", "@RestController\n@RequestMapping(\"/x\"\nclass X { @GetMapping(\"/y\" ")
    _write(tmp_path, "repo/src/main/kotlin/Y.kt", "@RequestMapping(value = [\n@GetMapping(")
    _write(tmp_path, "repo/src/main/resources/application.yml", "server:\n  tomcat:\n    keep-alive-timeout: [1, 2]\n")
    _inventory(tmp_path)


def test_command_from_linked_dockerfile(tmp_path):
    _kotlin_repo(tmp_path)
    _write(tmp_path, "Dockerfile", "FROM gradle:8 AS build\nRUN gradle bootJar\n"
                                   "FROM eclipse-temurin:21\nENTRYPOINT [\"java\", \"-jar\", \"/app.jar\"]\n")
    _, _, workloads, _ = _detect(tmp_path)
    assert [(w.id, w.command) for w in workloads] == [("w-user-service", "java -jar /app.jar")]
