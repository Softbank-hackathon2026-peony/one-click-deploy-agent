# 계획 1 구현 기록: 판정과 후속 과제

- 작성일: 2026-10-02
- 계획: docs/superpowers/plans/2026-10-02-infrafit-1-foundation-s0-s1.md
- 브랜치: feat/infrafit-plan1

구현 중 내린 판정(Ruling)과, 다음 계획에서 다뤄야 할 미해결 항목이다. 각 줄은 '판정 — 이유 — 틀렸을 때의 비용' 형식이다.

## 판정
- Ruling: R1 every task commit appends trailer `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>` (use a second -m) — Global Constraints override the plan's shorter commit commands — cost if wrong: none (message text only)
- Ruling: R2 work on branch feat/infrafit-plan1 in place instead of a git worktree — user approved execution; branch keeps main untouched; no native worktree consent asked — cost if wrong: switching to a worktree later is trivial
- Ruling: R3 implementers must not create or read any file of expected outputs for fixtures; golden files are engine snapshots only — user explicitly forbade recording expectations — cost if wrong: none
- Ruling: R4 RunContext.cached() must validate the cached data against the schema before writing; a cache entry that fails validation is treated as a miss (return None, write nothing) — Global Constraint "검증을 통과해야만 파일로 쓴다" binds over the plan's cached() code — cost if wrong: one extra validation per cache hit
- Ruling: R5 code_version() also hashes schemas/infrafit.schema.json so a schema change invalidates caches — cache must not replay outputs made under another schema — cost if wrong: caches invalidate on schema edits (desired)
- Ruling: R6 snapshot walk skips symlinks (files and dirs) instead of following them — dangling symlinks crash the walk and links outside the repo leak files into analysis — cost if wrong: symlinked source files are not analyzed
- Ruling: R7 invalid or non-mapping infrafit.yaml makes S0 raise a ValueError naming the file and the problem (no silent drop) — user overrides must not vanish silently — cost if wrong: a user with a broken file must fix it before analysis
- Ruling: R8 the work directory is pruned during the walk so files_total excludes it, and is not listed in `excluded` — S0 must be deterministic across re-runs — cost if wrong: none
- Ruling: R9 commit messages need a blank line between subject and trailer (trailer otherwise parsed as part of the subject) — controller-confirmed gap on 80ff296 — cost if wrong: none
- Ruling: R10 `open_snapshot(source, workdir, exclude=None)`: `exclude` is the analyze out root; `_walk` prunes only the directory whose relative path equals exclude exactly (never its ancestors); pipeline passes `exclude=out_root`. workdir stays ctx.out_dir (clone destination) — prunes all runs under the out root without dropping unrelated repo files — cost if wrong: none
- Ruling: R11 package.json parsing guards: skip files whose JSON root is not an object; treat non-object dependencies/devDependencies/scripts sections as empty — one odd manifest must not crash S1 — cost if wrong: none
- Ruling: R12 requirements parsing: skip lines that are URLs/VCS/paths (contain "://" before a name, or start with "git+", ".", "/"); for "name @ url" take the name — bogus deps would create false signature matches — cost if wrong: URL-only requirements are not recognised as deps
- Ruling: R13 compose/CI/platform parsers return parsed=False when the YAML/JSON/TOML root is not a mapping; non-mapping `services`/`jobs` are treated as empty; a job whose steps are not a list is skipped — one odd file must not abort the artifact scan — cost if wrong: none
- Ruling: R14 Dockerfile base_image skips leading `--flag` tokens of FROM (e.g. --platform=...) — multi-arch FROM is common and base_image feeds later stages — cost if wrong: none
- Ruling: R15 task-brief extraction merged Task 9 and 9b; split into task-9-brief.md and task-9b-brief.md (dispatched separately) — cost if wrong: none
- Ruling: R16 defaults.py must use the same non-dict guards as artifacts.py (metadata, containers, spec) — S1 must not crash on malformed k8s objects that the parser passes through — cost if wrong: none
- Ruling: R17 workloads found only in a kustomize-rendered artifact use the real kustomization.yaml path (strip '#build', line None) as entrypoint evidence — evidence must point to an existing file (consistency check) — cost if wrong: less precise evidence line
- Ruling: R18 find_unmapped needs tests (positive: watchlist dep with no signature condition is reported with manifest evidence; negative: dep covered by a signature is not reported) — plan omitted coverage for a public function — cost if wrong: none
- Ruling: R19 hop evidence from a kustomize-rendered Ingress uses the real kustomization.yaml path (strip '#build', line None); artifacts iterated sorted by path — evidence must reference existing files — cost if wrong: less precise evidence
- Ruling: F1 S1 cache key uses a content digest of all scanned files (always computed, independent of git HEAD) plus kustomize binary path/version; `commit` stays for display — dirty trees must not replay stale inventories — cost if wrong: digest cost per run
- Ruling: F2 platform configs attach only to code/Dockerfile workloads whose code_root (or app_dir) is equal to or under the config's directory (code_root None → only repo-root configs); never to k8s/compose workloads; edge hop only for workloads whose compute came from that config. Terraform refinement/EKS-GKE mapping stays repo-wide but is `confirmed` only when the repo has a single Terraform root directory and exactly one matching resource, otherwise `candidate` — infra dirs are conventionally separate, so ancestry cannot link them — cost if wrong: some correct Terraform links shown as candidate
- Ruling: F3 Dockerfile settings come from the final stage only; `*.dockerignore` is not a Dockerfile; when the final stage has no USER, record `user_inherited_from` = final base image instead of a defaulted root (remove the dockerfile user default from knowledge/defaults.yaml) — base images may set non-root users — cost if wrong: S3 must resolve inherited users itself
- Ruling: F4 kustomize build runs with timeout 60s; TimeoutExpired/OSError → parsed False; leaves whose kustomization tree references remote sources (contains "://", starts with "github.com/" or "git@") are not built (parsed False); without a binary every leaf is emitted parsed False; F1 golden test skips when kustomize is missing — no network beyond git clone, no hangs, visible gaps — cost if wrong: remote-based overlays not rendered
- Ruling: F5 endpoint assignment also scores code_root (like app_dir); endpoints assigned by the all-zero fallback get status candidate; datastores whose used_by fell back to all backend workloads get status candidate — spec §6: guesses must be candidate — cost if wrong: more candidate facts for S2 to confirm
- Ruling: F6 cached() treats a non-JSON cache file as a miss; a shared `is_build_path(path)` (endswith '#build') replaces ad-hoc '#' checks in workloads.py and paths.py
- Ruling: F7 goldens are regenerated with scripts/update_golden.py after these intended behaviour changes; the re-review inspects the golden diff for unintended changes

## 보류된 항목 (다음 계획에서 처리)
- Task 14: parked — request paths do not model a reverse-proxy workload in front of other workloads (f1: LB → nginx → auth/board uvicorn); auth/board paths lack the LB and nginx hops — Ruling: real gap, not a defect in this task's code (brief matches Ingress backend by name only); carry to follow-up: parse nginx/envoy proxy configs (proxy_pass/upstream targets) to chain workloads, needed before S3 path rules run on F1
- Task 14: parked — several Ingresses (aws and gcp overlays) front the same workload; only the first by path is reported — Ruling: overlays represent environments/clouds; keep first for now, carry to follow-up with environment modelling (spec §9.8)
- Task 14: complete (commits 210cb09..a13b705, 2 parked)
- Final: parked — single backend workload still yields candidate datastore used_by — Ruling: keep candidate; datastores can be used by non-workload code (scripts, tools), unlike route handlers; S2 confirms usage — cost: one extra candidate for S2
- Final: parked — zero backend workloads make confirmed datastores candidate (status mixes existence and usage) — Ruling: acceptable for now; revisit when S2 adds a separate usage confidence — cost: none for S1
- Final: parked — FROM ${BASE} records literal ${BASE} as user_inherited_from — Ruling: S3 resolves inherited users — cost: none

## 미뤄 둔 작은 항목
- Task 1: minor (deferred): report padded with unchecked claims (cosmetic)
- Task 2: minor (deferred): parameter name input_hash shadows module function in run.py; cache filename from hash not sanitized beyond ':'; non-atomic writes; read_text without encoding in tests; KeyError on unknown stage
- Task 2: minor (deferred): cached() raises JSONDecodeError on a non-JSON cache file instead of treating it as a miss
- Task 3: minor (deferred): git clone failure surfaces without stderr; CLI prints traceback for missing path; pipeline `until` stub (S1 added in Task 15); test gaps for git-clone/HEAD branches and CLI analyze; dirs named out/build excluded at any depth
- Task 3: minor (deferred): out root equal to repo root is not excluded (exclude '.' never matches)
- Task 5: minor (deferred): line_of substring can pick wrong line; PEP 503 '.' folding; optional/group deps not read; Procfile name validation; Node line-number assertions missing
- Task 6: minor (deferred): kb_lint uses private kb._load; malformed KB YAML raises instead of lint issue; refine.status not linted; lint has no negative tests; kb_version hashes *.yaml only; broad regexes writeFile/send_message
- Task 7: minor (deferred): thin matcher tests (all-match, dependency evidence, cap, refine status); MULTILINE no-op; duplicate evidence on refine; regex recompiled per call
- Task 8: minor (deferred): comment lines inside a continued instruction are concatenated; trailing backslash at EOF drops instruction; tab after instruction keyword; compose image evidence first-match only; missing tests for parsed=False/railway.ts/to_dict
- Task 9: minor (deferred): malformed-input test asserts little; 'Kind/?' prefix collision; no provider-alias unit test; k8s/terraform facts have no evidence lines
- Task 9b: minor (deferred): kustomize build has no timeout and does not catch OSError; remote resources could hit network (global constraint) — triage in final review; '.' mapping untested
- Task 10: minor (deferred): 'Kind/?' key collision for unnamed objects; malformed defaults entries raise KeyError; missing CronJob/multi-resource tests
- Task 10: minor (deferred): CronJob int-spec branch untested in regression test
- Task 11: minor (deferred): '#' in path treated as build artifact (use endswith('#build')); inline imports in tests; dead setup in kustomize test; compose guard test asserts only non-empty
- Task 12: minor (deferred): endpoint belongs to exactly one workload; workloads sharing an image/code_root (f1 auth + auth-verify) get endpoints only on one — revisit in plan 2 (per-endpoint scopes); include_router prefixes not applied; pages/api line 1; untested _express app-route skip and app_dir branch
- Task 13: minor (deferred): merged evidence not deduplicated (f2 db.py twice); Dockerfile/terraform loops rely on parse_artifacts order; _refine_hosting picks first matching resource
- Task 14: minor (deferred): _edge relies on parse_artifacts order (sorted anyway); private _d imported across modules; missing tests for gce/unknown class/annotation class/non-Vercel edges
- Task 15: minor (deferred): check_run traceback on missing/corrupt intake.json; O(n^2) duplicate check; inline import in CLI; '..' evidence paths not rejected

# 계획 1b: 판정과 후속 과제

계획: docs/superpowers/plans/2026-10-02-infrafit-1b-proxy-environments.md

## 판정
- Ruling: P1 LocationInfo (T3) fields: modifier, pattern, internal, order, proxies: list[tuple[str|None, str|None]] (target workload id, uri) per resolved upstream server, subrequests: list[str], children: list[LocationInfo]; ProxyServer.locations holds top-level locations — T4's select_location and exposure need these — cost if wrong: small refactor in T4
- Ruling: P2 golden and schema-example tests may fail between Task 2 and Task 5 only because of intended new fields; Task 5 regenerates them via the script — goldens are snapshots, not expectations — cost if wrong: masked regression until Task 5, caught by its golden-diff audit
- Ruling: P3 a mapping link (rule 2/3) counts only if the container path is under /etc/nginx/ or the workload is nginx-based (image or final-chain FROM contains "nginx"); otherwise the file stays unlinked and rule 5's fallback may apply — `COPY . .` in app images must not turn apps into proxies — cost if wrong: custom nginx paths on non-nginx-named images missed
- Ruling: P4 (T4 concern 1) shared-code endpoints go to the workloads whose matching root (app_dir or code_root) is the deepest; ties all get the endpoint — nested roots mean the inner workload owns the file — cost if wrong: an outer workload misses endpoints
- Ruling: P5 (T4 concern 3) reverse-proxy hop settings: fill defaults per route for keys that route lacks, then merge distinct values — a route without an explicit value really runs with the default — cost if wrong: extra SettingFacts
- Ruling: P6 (T4 concern 4) every subrequest of an externally selectable location (not internal, not named) is reached regardless of known endpoints; its forwarded path marks the target endpoint routed — any request matching that location triggers the subrequest — cost if wrong: none
- Ruling: P7 (T4 review Important, plan-mandated rule 10 defect) select_location keeps internal locations as candidates (only `@` named excluded); a selected internal location reaches nothing for external requests (nginx returns 404) — nginx semantics; rule 9 already assumed this — cost if wrong: none
- Ruling: P8 (found in T4 review, Task 2 gap) environments = kustomize leaves ∪ kustomization dirs with an ancestor directory named `overlays` whose own directory name is not base/common/shared and whose kind is not Component; build_overlays builds all of these — an overlay that is deployed directly can also be a base for another overlay (f1-like `local` ← `local-loadtest`) — cost if wrong: an intermediate overlay that is never applied shows as an environment
- Ruling: F1 exposure also tries reverse-mapped external paths: for each external (non-internal, non-named) prefix location L proxying to W with uri U where endpoint path r starts with U, candidate request = L.pattern + r[len(U):]; then the normal select_location + forwarded-path check — prefix-stripping proxies are the most common compose shape — cost if wrong: none (still verified by selection)
- Ruling: F2 every parsable nginx-named file mapped under /etc/nginx/ (or mapped into an nginx-based workload) is linked regardless of proxy directives; the proxy-directive filter applies only to the rule-5 unlinked fallback; when /etc/nginx/nginx.conf is mapped it is the single entry (its includes bring in conf.d) — http-level settings live there — cost if wrong: none
- Ruling: F3 build-context candidates: compose service build.context first (when the workload comes from that compose service), then Dockerfile dir, then repo root
- Ruling: F4 compose services with `build` and no `command` take the CMD/ENTRYPOINT of their Dockerfile (final chain) as workload command — pre-existing gap that removes the app-server hop on the commonest shape — cost if wrong: none
- Ruling: F5 one shared workload-object matcher (environments.workload_in's rule) used by nginx.py; make `_d`, `_final_chain`, `_stages`, `_dockerfile_for_image` public names (keep old private aliases only if needed internally)

## 보류된 항목 (다음 계획에서 처리)
- Final: parked — exposure has no own status when only candidate routes contribute (F-minor 4); exposure is a union across environments (6); compose topology dropped when k8s also defines workloads (7); namePrefix overlays split workloads (8) — all need schema/workload-model decisions; carry to plan 2
- Final: parked — exact (=) locations with uri not reverse-mapped; uri without trailing slash builds odd candidates (verified by selection, worst case false not-routed); compose `entrypoint:` key ignored for command

## 미뤄 둔 작은 항목
- Task 1: minor (deferred): `import pkg.routes` without alias and non-Name owners (app.router) unhandled
- Task 2: minor (deferred): collision-fallback and `root` naming untested; env_slug collisions (a/b vs a-b) — duplicate path ids are already caught by check_s1's duplicate scope id check; import order
- Task 3: minor (deferred): env-null raw k8s may read overlay patches; mutually-including entries vanish; proxy_pass inside if/limit_except; module split and private helper imports
- Task 4: minor (deferred): no multi-proxy chaining (proxy behind proxy)
- Task 4: minor (deferred): Django nested-paren groups and ^ inside char classes in request-path normalisation

# 계획 1c: 판정과 후속 과제

계획: docs/superpowers/plans/2026-10-02-infrafit-1c-compose-env-exposure-chains.md

1c로 해소된 1b 보류 항목: 환경을 합친 exposure(→ 환경별 exposure), k8s가 있을 때 compose 구성 소실(→ compose 환경), 다단 프록시 미지원(→ 체인).

## 판정
- Ruling: P1 (T1 concern 1) a k8s-sourced workload that is in no kustomize environment keeps its environment-null path from the plain manifests even when it is also in a compose environment; null scope for compose/code workloads stays "in no environment" — plain manifests are a deployment of their own — cost if wrong: an extra null path
- Ruling: P2 (T1 concern 2) app-server hop evidence follows where the command came from: compose environment → the compose file line holding the service `command` (or the Dockerfile CMD/ENTRYPOINT line when taken from the Dockerfile); kustomize environment → the kustomization.yaml of that environment (build_source) when the rendered command differs from w.command, else w.entrypoint — evidence must point at the fact's source — cost if wrong: none
- Ruling: P3 cycle handling skips proxies already in the chain and continues with the next-lowest id (instead of stopping) — paths and exposure agree; strictly more information — cost if wrong: none
- Ruling: F1 a variant file creates an environment only if it parsed and contributes ≥1 service
- Ruling: F2 compose merge follows docker: `volumes` merged by container path, `ports`/`expose` appended unique, `environment` by variable name, other keys replaced
- Ruling: F3 (changes plan 1c rule 2) variant environment = base + variant (no override file); the override merges only into the plain base environment — matches `docker compose -f base -f variant`; overrides hold dev settings — cost if wrong: none
- Ruling: F4 compose workloads take facts from base files first, then override, then variants (environments' naming rules decide the order); workload kind classification is token-based: worker iff a non-option token equals `worker` or ends with `.worker`, `/worker`, `:worker`, `worker.py`, `worker.js`, `worker.ts` (option tokens starting with `-` and option values like `uvicorn.workers.UvicornWorker` never count) — `--workers 4` and gunicorn worker classes are not worker processes — cost if wrong: some real workers classified web
- Ruling: F5 args-only kustomize overlays: when the container has no `command`, prefix the image's final-chain ENTRYPOINT; with neither args nor command use CMD
- Ruling: F6 one proxy-graph module (`infrafit/detect/proxy_graph.py`) holds chain finding, fronted proxies and caps used by both paths and endpoints; one compose `environment` parser; one container selection helper
- Ruling: F7 no environment from `.devcontainer/` compose files, and no compose environment with zero matched workloads; dash-named `docker-compose-<x>.yml` are variants named like dot variants; `compose.override.*` merges only onto `compose.*` bases and `docker-compose.override.*` only onto `docker-compose.*` bases
- Ruling: F8 add the mixed null-scope + compose exposure test
- Ruling: F4a workload names also signal worker: a name segment (split on - _ .) equal to worker or workers makes it a worker (k8s/compose deployments named e.g. email-worker often run generic commands) — cost if wrong: an oddly named web service classified worker

## 보류된 항목 (다음 계획에서 처리)
- Final: parked — inner proxy server selection by listen/server_name (union of server blocks may over-report routed); compose `profiles:` ignored; compose `entrypoint:` key ignored; namePrefix overlays split workloads; nginx.py size
- 워크로드 kind 판정이 이름·명령 토큰 규칙에 의존한다(S2에서 확정 필요)

## 미뤄 둔 작은 항목
- Task 1: minor (deferred): nginx.py size
- Task 2: minor (deferred): no test mixing null scope with named environments for one workload

# 계획 1d: 판정과 후속 과제

계획: docs/superpowers/plans/2026-10-02-infrafit-1d-real-repo-fixes-spring.md (실제 저장소 12개로 검증)

## 판정
- Ruling: P1 (T1 concern 3) compose workload entrypoint evidence uses the same service-key line lookup as image services (not a plain `name:` search) — evidence must hit the real definition line — cost: f1 golden evidence lines may change (regenerated in T4)
- Ruling: P2 (T1 concern 5) rule 7 links the single unlinked Dockerfile only when the image-only app workloads needing a link all share one image name (or there is just one); otherwise no link — different images mean different code — cost if wrong: a missed link
- Ruling: P3 (T1 concerns 1,2,4) accepted as reported
- Ruling: P4 rules 6–7 ignore dev/test Dockerfiles: a name part (from `Dockerfile.<x>`, `<x>.Dockerfile`, `<x>.dockerfile`) among dev, test, tests, ci, local, debug, e2e, or a path segment among test, tests, __tests__, e2e, spec — such images are not deployed — cost if wrong: a real app built only from Dockerfile.local missed
- Ruling: P5 endpoints owned through the single-web rule stay confirmed even when the code_root link was guessed — ownership was not decided by the guess — cost: none
- Ruling: P6 (T2 deviation) only code_root "" counts as repo root (app_dir "" means unknown) — accepted
- Ruling: P7 parameter-derived server names: drop `api` and `instance` from the list; a route from a parameter-derived server must start with `/` and the server name is scoped to the function that declares it (from the parameter's function to the end of that function's body, or to the end of the file for top-level arrow bodies when the end cannot be found) — axios-style clients share these names — cost: some plugin routes with unusual param names missed
- Ruling: P8 route calls are matched over the whole file text (multi-line prettier style), line from the match start — same as _route_objects
- Ruling: P9 (T3 concern 1) compose/k8s workloads get `framework` from the build file under their code_root (Gradle/Maven deps of that module) so Spring apps deployed through compose/k8s get the Tomcat app-server hop — common shape — cost: none
- Ruling: P10 (T3 concern 2) a Spring module counts as a workload only if it has a `@SpringBootApplication` class (Java/Kotlin, non-test) under its directory or applies the Boot plugin (not `apply false`); library modules are skipped — cost if wrong: a boot app without the annotation and plugin missed
- Ruling: P11 T3 deviations 1–6 accepted
- Ruling: P12 Gradle version catalogs: read gradle/libs.versions.toml ([libraries] `module = "g:a"` or `group`/`name`; [plugins] `id`), resolve `libs.<alias>` (dots/dashes/underscores equivalent) and `alias(libs.plugins.<alias>)` in build files to coordinates/plugin ids; evidence = the build-file line — common modern Gradle shape — cost: none
- Ruling: FA1 restore image coverage in images.yaml (bitnami/mongodb, mongodb*, redis-stack*, redis/redis-stack*, mysql/mysql-server, minio/*, timescaledb*, pgvector/*, gce-proxy, cloudsql-proxy variants; dev-tool: mongo-express, redis-commander, redisinsight, phpmyadmin) + regression test listing all old token-covered names
- Ruling: FA2 Gradle subprojects/allprojects blocks: their plugins/dependencies never apply to the root module; dependencies there are attributed to each child build dir that exists; Spring configs limited to files whose owning build dir is the workload's dir
- Ruling: FA3 single web workload → endpoints confirmed regardless of guessed root; otherwise guessed root → candidate
- Ruling: FA4 module split: detect/images.py (classify_image, image services), detect/jvm.py (masking, bracket matching, Gradle/Maven, Spring detection), one shared `nearest_dir(...)` helper and one `line_at` with precomputed offsets; dedupe XML comment regex and nginx component constant
- Ruling: FA5 a test asserts every component-ID constant in infrafit/detect exists in the catalog; images lint flags shadowed/duplicate patterns, family/role mismatch (datastore→ds:, cache→ca:, queue→qu:, reverse-proxy→nw:) and unknown keys
- Ruling: FA6 DEV_DOCKERFILE_PARTS += development, testing; manifests and build dirs under test paths do not create workloads
- Ruling: FA7 spec §2 workload kinds += reverse-proxy (note: may be a static SPA served by nginx); §3 knowledge table += images.yaml
- Ruling: FB1 app_server parses commands: split `sh -c "..."`/`bash -c`, `&&`, `;`, take each simple command; recognise `python -m uvicorn|gunicorn|flask run`, `flask ... run`, `npx`/`exec` prefixes; the last recognised server wins
- Ruling: FB2 Dockerfile-recovered workloads: build context = repo root when every COPY/ADD source (excluding --from) exists relative to the repo root but not relative to the Dockerfile dir; code_root follows the context
- Ruling: FB3 dependency-only matches become candidate for SIG-DS-SUPABASE (confirmed refine only with `.from(`/`.rpc(`/supabase DB URL) and JVM SQS (confirmed only with SqsClient/SqsTemplate/@SqsListener usage)
- Ruling: FB4 static-frontend: vercel.json/netlify.toml do not map to functions compute (compute `unmapped` instead); static-frontend workloads get a request path with the platform edge hop when a platform config applies; a static-frontend whose build output dir (dist/build/out) is COPYed into another workload's Dockerfile is not a separate workload; compute root-Dockerfile fallback never applies to static-frontend
- Ruling: FB5 signature evidence ordering: files under scripts/, qa/, tools/, examples/, bench/ sort after other files before the 5-item cap
- Ruling: FB6 code workload names come from the directory only (`server`, `worker`), single-root keeps `web`; kind via is_worker(name, command)
- Ruling: FB7 env_command_evidence falls back to the linked Dockerfile CMD/ENTRYPOINT line before w.entrypoint
- Ruling: FB8 manifests read pyproject optional-dependencies (all groups) and Dockerfile `RUN pip install ...`/`npm install|i ...`/`yarn add`/`pnpm add` package names (flags and version pins stripped), evidence = Dockerfile line
- Ruling: FB9 SIG-DS-POSTGRES code condition: `postgres(ql)?(\+\w+)?://` in py/js/ts/yml/yaml/env.example/toml; SIG-FS-LOCAL widened (Python open(...,'w'|'a'), json.dump, Path.write_text, fs.writeFile*) as candidate
- Ruling: FB10 images.yaml: `*-exporter`, `*_exporter`, prom/*, grafana/*, otel/* collectors → role infra (unmapped label); Kotlin `apply(plugin = "...")` and `configure(subprojects)`/`configure(allprojects)` blocks handled like FA2
- Ruling: FB11 a code workload detected from a web-framework dependency stays web unless its command is a recognised worker command (is_worker on the command tokens); the name alone does not make it a worker (FA4a name rule stays for k8s/compose) — shipchajang worker serves HTTP — cost: a framework-based worker named *worker with an HTTP-free command still web
- Ruling: FB12 matches whose evidence lies only in auxiliary dirs (scripts/, qa/, tools/, examples/, bench/) do not create scopes; they only add evidence to scopes created elsewhere
- Ruling: FC1 `_owned_by_other` drops a route only when the web workload has a root and another non-web workload's root is strictly deeper and contains the file; a web workload without roots never loses routes this way
- Ruling: FC2 Supabase refine requires a receiver whose name contains `supabase` (case-insensitive), across line breaks; `.storage` chains excluded across line breaks; otherwise stays candidate (safe direction)
- Ruling: FC3 exporter patterns restricted to known publishers: prom/*, prometheuscommunity/*, oliver006/redis_exporter, quay.io-style */postgres-exporter, bitnami/*-exporter, */node-exporter; user images named *-exporter stay apps
- Ruling: FC4 shell.simple_commands also splits on `&` and `|`; FB8 ignores dev/test Dockerfiles

## S2 설계로 넘긴 것
- Deferred (S2 design): external services/SaaS, deploy targets from CI/README (Cloud Run, EC2/SSM), batch/CLI workloads, STOMP realtime, framework-implicit routes, multi-target environments (render.yaml beside compose), Temporal as orchestrator component

## 미뤄 둔 작은 항목
- Task 1: minor (deferred): unparsed proxy path does not follow chains; compose evidence can feed _users location check
- Task 3: minor (deferred): root module reads submodule application configs; `${X:20s}` placeholders not resolved; RED evidence for one test missing

# 계획 1e: 판정과 후속 과제

계획: docs/superpowers/plans/2026-10-02-infrafit-1e-external-deploy-targets.md (작업 2개 병렬 구현, 최종 리뷰 1회)

## 판정
- Python 라우트의 framework는 파일이 import하는 웹 프레임워크(fastapi, flask)로 적는다(자동 라우트와 일치).
- socket.io `ns.Server(`는 ns가 socket.io를 가져온 이름일 때만 엔드포인트로 본다(`new http.Server(` 오탐 제거).
- Firebase env 조건에서 `GOOGLE_APPLICATION_CREDENTIALS`를 뺀다(GCP 공용 자격 증명).
- 예시 env 파일(.env.example 등)의 자리표시자만 근거인 외부 서비스는 만들지 않는다(아직 구현되지 않은 기능일 수 있음).
- platform·ci-deploy 환경은 출력에만 더하고, 요청 경로·exposure·nginx 범위는 기존 환경 목록을 쓴다.

## 후속 과제
- 요청 경로를 platform·ci-deploy 환경에도 만들지(예: Cloud Run 앞단 구간).
- pydantic Settings 필드 이름을 env 이름으로 읽기.
- GitHub Actions `${VAR}` 치환은 휴리스틱(워크플로·job·step env, 앞 step의 `X=`·`GITHUB_ENV`).
- STOMP 규칙은 `@EnableWebSocketMessageBroker`만으로 simple broker로 본다(외부 브로커 릴레이 구분 없음).
