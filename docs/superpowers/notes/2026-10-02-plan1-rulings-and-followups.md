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
