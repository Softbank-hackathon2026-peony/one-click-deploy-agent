# 응답 후 작업(A4): 플랫폼별 CPU와 프레임워크별 실행 방식

- 작성일: 2026-10-03 (모든 값의 확인일 2026-10-03)
- 요구 쪽 차원: [dimensions.md](dimensions.md) A4 "응답 후 작업"(FastAPI `BackgroundTasks`, 응답 뒤 `setTimeout`, await 안 한 Promise, Spring `@Async`, 핸들러에서 띄운 스레드)
- 능력 쪽: [capabilities/05-compute-tier1-2.md](capabilities/05-compute-tier1-2.md), [../../knowledge/capabilities.yaml](../../knowledge/capabilities.yaml) `CP.cpu_after_response`·`CP.always_on`·`CP.always_on_config`, [../../knowledge/rules.yaml](../../knowledge/rules.yaml) `CAP-BGWORK-001`·`CAP-SINGLERUN-002`
- 출처 정책: [README.md](../../README.md) §3. AWS·Google Cloud·Kubernetes·Spring·FastAPI·Starlette·Node.js·Python 공식 문서만 쓴다.

표기
- 출처는 `URL · "원문 인용" · 2026-10-03` 형식이다. 인용은 페이지 문장을 그대로 옮겼다(링크 때문에 생긴 공백만 정리).
- `공식 문서에서 명시 문장 못 찾음`: 연 공식 페이지에서 그 내용을 직접 말하는 문장을 찾지 못했다. 추측해 채우지 않았다.
- 인용에서 한 단계로 이끌어 낸 결론은 표에 넣지 않고 §4에 `정의상/유도` 항목으로 따로 적었다. 표 안에서는 `→ §4 Dn`으로 가리킨다.

## 0. 요약

| 플랫폼 | 응답 후 CPU | 근거 종류 |
|---|---|---|
| AWS Lambda (Function URL·Web Adapter) | **없음**: 호출이 끝나면 실행 환경 동결, 다음 호출 때 재개 | 명시 문장 (docs.aws.amazon.com) |
| Cloud Run 요청 기반 과금 | **없음 또는 심하게 제한**: 같은 인스턴스에 다른 요청이 들어오면 재개 | 명시 문장 (docs.cloud.google.com) |
| Cloud Run 인스턴스 기반 과금 | **있음**: 단, 유휴 인스턴스는 언제든 종료될 수 있음(min-instances로 붙잡음) | 명시 문장 (docs.cloud.google.com) |
| ECS Fargate 서비스 | 명시 문장 없음 → §4 D5에서 "있음"으로 유도 | 유도 |
| EC2 단일 VM | 명시 문장 없음 → §4 D6에서 "있음"으로 유도 | 유도 |
| Compute Engine 단일 VM | 명시 문장 없음 → §4 D7에서 "있음"으로 유도 (e2 공유 코어는 요청과 무관하게 CPU 시간 비율 제한) | 유도 |
| GKE Autopilot | 명시 문장 없음 → §4 D8에서 "있음(limit까지)"으로 유도 | 유도 |
| EKS | 명시 문장 없음 → §4 D8에서 "있음(limit까지)"으로 유도 | 유도 |

프레임워크의 동시성 모델(Spring 다중 스레드, FastAPI·Node 이벤트 루프)은 위 결과를 바꾸지 않는다. 플랫폼 문서는 CPU를 인스턴스·실행 환경 단위로 주거나 끊기 때문이다(§3, §4 D12). 모델이 바꾸는 것은 응답 후 작업이 **같은 프로세스의 다른 요청을 막는가**(성능)다.

## 1. 플랫폼별 응답 후 CPU·실행

### 1.1 AWS Lambda (Function URL / Lambda Web Adapter)

| 항목 | 값 | 조건 | 출처 (URL · 인용 · 2026-10-03) |
|---|---|---|---|
| 호출 끝난 뒤 CPU | **없음**: 런타임과 확장이 끝나면 실행 환경을 동결 | Lambda(기본) 함수. Managed Instances는 수명 모델이 다름 | https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html · "Lambda freezes the execution environment when the runtime and each extension have completed and there are no pending events." / "After the invocation completes, the execution environment is frozen." · 2026-10-03 |
| 미완료 백그라운드 작업 | 다음 호출에서 환경이 재사용될 때만 이어짐. 공식 권고는 끝나기 전에 완료할 것 | — | https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html · "Background processes or callbacks that were initiated by your Lambda function and did not complete when the function ended resume if Lambda reuses the execution environment. Make sure that any background processes or callbacks in your code are complete before the code exits." · 2026-10-03 |
| 호출 후 별도 단계 | 없음. 함수 타임아웃이 호출 단계 전체를 제한 | — | https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html · "Note that there is no independent post-invoke phase." · 2026-10-03 |
| 유휴 시 종료 | 일정 시간 유지 후 종료. 계속 호출돼도 몇 시간마다 종료 | — | https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html · "However, Lambda terminates execution environments every few hours to allow for runtime updates and maintenance—even for functions that are invoked continuously." · 2026-10-03 |
| 종료 단계 시간 | 확장 없음 0 ms, 내부 확장 500 ms, 외부 확장 2,000 ms. 넘으면 SIGKILL | — | https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html · "0 ms – A function with no registered extensions" / "If the runtime or an extension does not respond to the `Shutdown` event within the limit, Lambda ends the process using a `SIGKILL` signal." · 2026-10-03 |
| 환경당 동시 요청 | 1개. 처리 중인 환경은 다른 요청을 받지 않음 | Lambda(기본). Managed Instances는 한 환경에서 여러 호출 | https://docs.aws.amazon.com/lambda/latest/dg/lambda-concurrency.html · "During this entire process, this execution environment is busy and cannot process other requests." · 2026-10-03 |
| Node.js 콜백 핸들러 | 이벤트 루프가 빌 때까지 응답을 보내지 않고 기다림(기본). `callbackWaitsForEmptyEventLoop=false`면 즉시 응답 | 콜백 핸들러는 Node.js 22까지만 | https://docs.aws.amazon.com/lambda/latest/dg/nodejs-handler.html · "The function continues to execute until the event loop is empty or the function times out. The response isn't sent to the invoker until all event loop tasks are finished." / "Callback-based function handlers are only supported up to Node.js 22." · 2026-10-03 |
| 응답 스트리밍 | 클라이언트가 끊어도 스트리밍 응답은 멈추지 않음. Python 등은 Lambda Web Adapter로 스트리밍 가능 | — | https://docs.aws.amazon.com/lambda/latest/dg/configuration-response-streaming.html · "Streaming responses incur cost and streamed responses are not interrupted or stopped when the invoking client connection is broken." / "For other languages, including Python, you can use a custom runtime with a custom Runtime API integration to stream responses or use the Lambda Web Adapter." · 2026-10-03 |
| Lambda Web Adapter가 응답 후 작업을 어떻게 다루는가 | 공식 문서에서 명시 문장 못 찾음 (docs.aws.amazon.com은 이름만 언급) | — | — |
| 상시 실행 설정 | 공식 문서에서 명시 문장 못 찾음. 프로비저닝 동시성은 환경을 미리 초기화할 뿐, 호출 밖 CPU를 준다는 문장은 없음 | — | https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html · "Lambda also ensures that initialized execution environments are always available in advance of invocations." · 2026-10-03 |

### 1.2 Cloud Run — 요청 기반 과금(기본)

| 항목 | 값 | 조건 | 출처 (URL · 인용 · 2026-10-03) |
|---|---|---|---|
| 응답 후 CPU | **없음**: 요청 처리 중에만 CPU | 기본 과금 설정 | https://docs.cloud.google.com/run/docs/configuring/billing-settings · "With request-based billing, CPU is only allocated during request processing." · 2026-10-03 |
| 응답 후 작업 | 요청이 끝나면 CPU가 꺼지거나 심하게 제한됨. 백그라운드 스레드·루틴을 띄우지 말라고 권고 | — | https://docs.cloud.google.com/run/docs/tips/general · "If you need to set your service to request-based billing, when the Cloud Run service finishes handling a request, the instance's access to CPU will be disabled or severely limited." / "You shouldn't start background threads or routines that run outside the scope of the request handlers if you use this type of billing." · 2026-10-03 |
| 멈춘 작업 재개 | 같은 인스턴스에 다음 요청이 오면 멈춘 백그라운드 작업이 재개 | — | https://docs.cloud.google.com/run/docs/tips/general · "Running background threads with request-based billing enabled can result in unexpected behavior because any subsequent request to the same container instance resumes any suspended background activity." · 2026-10-03 |
| 다른 요청이 있을 때 | 요청을 하나라도 처리 중이면 인스턴스의 모든 컨테이너에 CPU | — | https://docs.cloud.google.com/run/docs/container-contract · "For Cloud Run services, CPU is always allocated to all containers including sidecars within an instance as long as the Cloud Run revision is processing at least one request." · 2026-10-03 |
| "응답 후 작업"의 정의 | HTTP 응답이 전달된 뒤 일어나는 모든 것 | — | https://docs.cloud.google.com/run/docs/tips/general · "Background activity is anything that happens after your HTTP response has been delivered." · 2026-10-03 |
| 유휴 인스턴스 | 최대 15분 유휴 유지 후 종료. 트래픽이 없으면 기본 0개 | — | https://docs.cloud.google.com/run/docs/about-instance-autoscaling · "To minimize cold starts, Cloud Run might keep instances idle for a a period of time after they finish handling requests (up to 15 minutes, or 10 minutes for GPUs)." / "When a revision does not receive any traffic, by default, it is scaled to zero instances." · 2026-10-03 |
| 종료 신호 | SIGTERM 후 10초 뒤 SIGKILL | — | https://docs.cloud.google.com/run/docs/container-contract · "Before shutting down an instance, Cloud Run sends a SIGTERM signal to all the containers in an instance, indicating the start of a 10 second period before the actual shutdown occurs, at which point Cloud Run sends a SIGKILL signal." · 2026-10-03 |
| 응답 후 CPU를 켜는 법 | 이 모드 안에는 없음. 인스턴스 기반 과금으로 바꿔야 함(`--no-cpu-throttling`) → §1.3 | min-instances를 쓰면 인스턴스 기반 과금이 필요 | https://docs.cloud.google.com/run/docs/container-contract · "If you have configured a number of minimum instances, you must use instance-based billing so that CPU is allocated outside of requests." · 2026-10-03 |

### 1.3 Cloud Run — 인스턴스 기반 과금

| 항목 | 값 | 조건 | 출처 (URL · 인용 · 2026-10-03) |
|---|---|---|---|
| 응답 후 CPU | **있음**: 인스턴스 수명 전체에 CPU. 응답 뒤 짧은 백그라운드 작업을 실행할 수 있음 | — | https://docs.cloud.google.com/run/docs/configuring/billing-settings · "With instance-based billing, CPU is allocated for the entire container instance lifecycle." / "Selecting instance-based billing allocates CPU even outside of request processing, letting you execute short-lived background tasks and other asynchronous processing work after returning responses." · 2026-10-03 |
| 유휴 인스턴스 종료 | 최소 인스턴스로 붙잡은 것을 포함해 언제든 종료될 수 있음. 최소 인스턴스가 아니면 15분 넘게 유휴로 남지 않음 | 오토스케일링은 이 모드에서도 작동 | https://docs.cloud.google.com/run/docs/configuring/billing-settings · "Idle instances, including those kept warm using minimum instances, can be shut down at any time." / "Even if the billing setting is set to instance-based billing, Cloud Run autoscaling is still in effect, and may terminate instances if they aren't needed to handle incoming traffic or current CPU utilization outside of requests." / "An instance will never stay idle for more than 15 minutes after processing a request unless it is kept active using minimum instances." · 2026-10-03 |
| 상시 백그라운드 처리 설정 | 인스턴스 기반 과금 + 최소 인스턴스 ≥ 1 | — | https://docs.cloud.google.com/run/docs/about-instance-autoscaling · "If your service performs other tasks even when it isn't processing requests, such as running background threads, or processing asynchronous tasks, you should set minimum instances to at least 1 to ensure that the CPU remains allocated for background processing." / https://docs.cloud.google.com/run/docs/configuring/billing-settings · "Combining instance-based billing with a number of minimum instances results in a number of instances up and running with full access to CPU resources, enabling background processing use cases." · 2026-10-03 |
| 설정 방법 | `gcloud run services update SERVICE --no-cpu-throttling` (Terraform·YAML도 있음, YAML은 `run.googleapis.com/cpu-throttling`) | — | https://docs.cloud.google.com/run/docs/configuring/billing-settings · "To set instance-based billing for a given service: gcloud run services update SERVICE --no-cpu-throttling" · 2026-10-03 |
| 최소 인스턴스의 한계 | 최소 인스턴스도 재시작될 수 있음 | — | https://docs.cloud.google.com/run/docs/container-contract · "For Cloud Run services, an idle instance can be shut down at any time, including instances kept warm due to a configured minimum number of instances." · 2026-10-03 |
| 종료 신호 | §1.2와 같음(SIGTERM 후 10초) | — | §1.2 행과 같은 출처 |

### 1.4 ECS Fargate 서비스

| 항목 | 값 | 조건 | 출처 (URL · 인용 · 2026-10-03) |
|---|---|---|---|
| 응답 후 CPU | 공식 문서에서 명시 문장 못 찾음 → §4 D5 | — | — |
| 태스크 CPU | 태스크 단위 하드 리밋(요청과 무관하게 정의됨) | 태스크 정의 `cpu` 필수 | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definition_parameters.html · "The hard limit of CPU units to present for the task." · 2026-10-03 |
| 동결·스로틀 | 요청 유무에 따른 동결·스로틀을 말하는 공식 문장 못 찾음 | — | — |
| 유휴 시 종료 | 서비스가 지정 수의 태스크를 실행·유지하고, 멈추면 대체 태스크를 띄움. 0으로 줄이려면 오토스케일링 최소 용량 0을 따로 설정 | — | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs_services.html · "If one of your tasks fails or stops, the Amazon ECS service scheduler launches another instance of your task definition to replace it." · 2026-10-03 (0으로 줄이기의 인용은 capabilities.yaml `cp:aws/ecs-fargate/alb` `CP.scale_to_zero`) |
| 종료 신호 | STOPSIGNAL(기본 SIGTERM) 후 StopTimeout 뒤 SIGKILL. StopTimeout 기본 30초, 최대 120초 | Fargate 플랫폼 1.3.0 이상 | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-lifecycle-explanation.html · "This is SIGTERM by default. Then it will send a SIGKILL after waiting the StopTimeout duration set in the task definition." / https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definition_parameters.html · "If the parameter isn't specified, then the default value of 30 seconds is used. The maximum value is 120 seconds." · 2026-10-03 |
| 상시 실행 설정 | 서비스 desired count ≥ 1(기본 동작) | — | https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs_services.html · "This helps maintain your desired number of tasks in the service." · 2026-10-03 |

### 1.5 EC2 (단일 VM)

| 항목 | 값 | 조건 | 출처 (URL · 인용 · 2026-10-03) |
|---|---|---|---|
| 응답 후 CPU | 공식 문서에서 명시 문장 못 찾음 → §4 D6 | — | — |
| 실행 상태 | running이면 사용 준비 완료, 유휴여도 과금되며 계속 실행 | — | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-lifecycle.html · "The instance is running and ready for use." / "As soon as your instance transitions to the running state, you're billed for each second, with a one-minute minimum, that you keep the instance running, even if the instance remains idle and you don't connect to it." · 2026-10-03 |
| 스로틀 | 요청과 무관. T4g·T3·T3a는 기본 Unlimited 모드라 기준선을 넘어 필요한 만큼 버스트(초과분 과금) | 버스트형 인스턴스 | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/burstable-performance-instances-unlimited-mode-concepts.html · "T8i, T4g, T3a, and T3 instances never receive launch credits because they launch in Unlimited mode by default, and therefore can burst immediately upon start." · 2026-10-03 |
| 유휴 시 종료 | 유휴여도 계속 실행(위 행) | — | 위 lifecycle 인용 |
| 상시 실행 설정 | 기본값(인스턴스를 켜 두면 됨) | — | 위 lifecycle 인용 |

### 1.6 Compute Engine (단일 VM)

| 항목 | 값 | 조건 | 출처 (URL · 인용 · 2026-10-03) |
|---|---|---|---|
| 응답 후 CPU | 공식 문서에서 명시 문장 못 찾음 → §4 D7 | — | — |
| 실행 상태·수명 | RUNNING 상태에서 실행. 수명은 사용자가 제어 | — | https://docs.cloud.google.com/compute/docs/instances/instance-lifecycle · "RUNNING state In the RUNNING state, Compute Engine is booting up the compute instance or the compute instance is running." / "Important: You control the lifecycle of your compute instances." · 2026-10-03 |
| 스로틀 | 요청과 무관. e2-small은 공유 코어로 vCPU 2개 각 25%(합계 50%) CPU 시간, 짧은 버스트 가능 | e2 공유 코어 머신 | https://docs.cloud.google.com/compute/docs/general-purpose-machines · "e2-small sustains 2 vCPUs, each at 25% of CPU time, totaling 50% CPU time." / "Shared-core machine types offer bursting capabilities that allow instances to use additional physical CPU for short periods of time." · 2026-10-03 |
| 유휴 시 종료 | 공식 문서에서 명시 문장 못 찾음(수명 문서는 "You control the lifecycle"만 말함) | — | — |
| 상시 실행 설정 | 공식 문서에서 명시 문장 못 찾음 | — | — |

### 1.7 GKE Autopilot

| 항목 | 값 | 조건 | 출처 (URL · 인용 · 2026-10-03) |
|---|---|---|---|
| 응답 후 CPU | GKE 문서에서 명시 문장 못 찾음 → §4 D8 | — | — |
| CPU 예약·상한 (Kubernetes) | request만큼 예약, limit은 커널 스로틀로 강제 | 요청(HTTP)이 아니라 컨테이너 단위 | https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/ · "The kubelet also reserves at least the request amount of that system resource specifically for that container to use." / "cpu limits are enforced by CPU throttling." · 2026-10-03 |
| Autopilot limit | requests = limits면 Guaranteed QoS. limits를 안 주면 버스트 지원 클러스터에서 여유 용량까지 버스트 | — | https://docs.cloud.google.com/kubernetes-engine/docs/concepts/autopilot-resource-requests · "requests equal to limits Pods use the Guaranteed QoS class." / "Clusters that support bursting : Pods can burst into available burstable capacity." · 2026-10-03 |
| 과금 단위 | 실행 중인 Pod가 요청한 CPU·메모리·임시 스토리지(초 단위) | 범용 Autopilot Pod | https://cloud.google.com/kubernetes-engine/pricing · "In the Pod-based billing model, you are charged in one-second increments for the CPU, memory, and ephemeral storage resources that your running Pods request in the Pod resource requests, with no minimum duration." · 2026-10-03 |
| 유휴 시 종료 | Deployment가 레플리카 수를 유지(capabilities.yaml `CP.always_on` 인용). 0으로 줄이기는 HPA 별도 설정 | — | capabilities.yaml `cp:gcp/gke/autopilot` 참조 |
| 종료 신호 | TERM 후 유예 기본 30초, 남은 프로세스는 SIGKILL | Kubernetes 공통 | https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/ · "By default, all deletes are graceful within 30 seconds." / "The container runtime sends SIGKILL to any processes still running in any container in the Pod." · 2026-10-03 |

### 1.8 EKS

| 항목 | 값 | 조건 | 출처 (URL · 인용 · 2026-10-03) |
|---|---|---|---|
| 응답 후 CPU | EKS 문서에서 명시 문장 못 찾음 → §4 D8 | — | — |
| CPU 예약·상한 | §1.7 Kubernetes 행과 같음 | — | §1.7 kubernetes.io 인용 |
| 유휴 시 종료 | 매니페스트의 레플리카 수를 유지 | — | https://docs.aws.amazon.com/eks/latest/userguide/sample-deployment.html · "Kubernetes maintains the number of replicas that are specified in the manifest." · 2026-10-03 |
| 종료 신호 | §1.7 Kubernetes 행과 같음(기본 30초) | — | §1.7 kubernetes.io 인용 |

## 2. 프레임워크별 응답 후 작업 방식

| 방식 | 어디서 실행되나 | 다른 요청을 막나 | 프로세스 종료 시 | 출처 (URL · 인용 · 2026-10-03) |
|---|---|---|---|---|
| FastAPI `BackgroundTasks` | 응답을 보낸 뒤, **같은 프로세스** 안. Starlette 클래스를 그대로 씀 | `def` 작업은 스레드 풀(기본 40개, FastAPI의 sync 의존성과 공유), `async def` 작업은 이벤트 루프. 이벤트 루프에서 CPU를 오래 쓰면 다른 작업·I/O가 모두 늦어짐 | FastAPI 문서에 명시 문장 못 찾음. 무거운 작업은 같은 프로세스가 아니어도 되면 Celery 같은 도구 권고 → §4 D9 | https://fastapi.tiangolo.com/tutorial/background-tasks/ · "You can define background tasks to be run after returning a response." / "The class BackgroundTasks comes directly from starlette.background." / "If you need to perform heavy background computation and you don't necessarily need it to be run by the same process (for example, you don't need to share memory, variables, etc), you might benefit from using other bigger tools like Celery." · 2026-10-03 |
| Starlette `BackgroundTask(s)` | 프로세스 안(in-process), 응답 전송 뒤. 여러 작업은 순서대로, 하나가 예외를 내면 뒤 작업은 실행 안 됨 | 동기 작업은 스레드 풀에서(이벤트 루프를 막지 않으려고), 풀 기본 40 토큰 | 공식 문서에서 명시 문장 못 찾음 → §4 D9 | https://starlette.dev/background/ · "Starlette includes a BackgroundTask class for in-process background tasks." / "A background task should be attached to a response, and will run only once the response has been sent." / "The tasks are executed in order." / https://starlette.dev/threadpool/ · "When running synchronous background tasks with BackgroundTask" / "The default thread pool size is only 40 tokens." · 2026-10-03 |
| Python `asyncio.create_task` (await 안 함) | 같은 이벤트 루프 | CPU 작업이면 루프 전체를 막음(위 행) | 참조를 저장하지 않으면 끝나기 전에 GC로 사라질 수 있음 | https://docs.python.org/3/library/asyncio-task.html · "The event loop only keeps weak references to tasks. A task that isn’t referenced elsewhere may get garbage collected at any time, even before it’s done." / https://docs.python.org/3/library/asyncio-dev.html · "For example, if a function performs a CPU-intensive calculation for 1 second, all concurrent asyncio Tasks and IO operations would be delayed by 1 second." · 2026-10-03 |
| Python `threading.Thread` (핸들러에서 시작) | 같은 프로세스의 별도 스레드 | 공식 문서에서 명시 문장 못 찾음(GIL 관련 문장은 조사 범위 밖) | 데몬 스레드는 종료 시 갑자기 멈춤. 데몬만 남으면 프로그램 종료 | https://docs.python.org/3/library/threading.html · "The significance of this flag is that the entire Python program exits when only daemon threads are left." / "Daemon threads are abruptly stopped at shutdown." · 2026-10-03 |
| Spring `@Async` | 호출자는 바로 반환, 실제 실행은 TaskExecutor에 제출된 작업. Boot 자동 설정은 ThreadPoolTaskExecutor(코어 8개, 부하에 따라 늘고 줆), 가상 스레드 켜면 SimpleAsyncTaskExecutor | 요청 스레드(Tomcat 기본 최대 200)와 다른 실행기 풀에서 돈다. 같은 JVM의 CPU는 공유 | `spring.task.execution.shutdown.await-termination` 기본 false(종료 시 남은 작업을 기다리지 않음). 웹 서버 graceful shutdown은 기본 켜짐이지만 대상은 "기존 요청" | https://docs.spring.io/spring-framework/reference/integration/scheduling.html · "In other words, the caller returns immediately upon invocation, while the actual execution of the method occurs in a task that has been submitted to a Spring TaskExecutor." / https://docs.spring.io/spring-boot/reference/features/task-execution-and-scheduling.html · "When a ThreadPoolTaskExecutor is auto-configured, the thread pool uses 8 core threads that can grow and shrink according to the load." / https://docs.spring.io/spring-boot/appendix/application-properties/index.html · "spring.task.execution.shutdown.await-termination Whether the executor should wait for scheduled tasks to complete on shutdown. false" / "server.tomcat.threads.max Maximum amount of worker threads. Doesn't have an effect if virtual threads are enabled. 200" / https://docs.spring.io/spring-boot/reference/web/graceful-shutdown.html · "This stop processing uses a timeout which provides a grace period during which existing requests will be allowed to complete but no new requests will be permitted." · 2026-10-03 |
| Node.js await 안 한 Promise·`res.send` 뒤 `setTimeout` | 콜백은 요청 처리와 **같은 Event Loop 스레드** | 콜백이 오래 걸리면 그동안 다른 클라이언트 요청을 처리하지 못함 | `process.exit()`·`exit` 이벤트 뒤 큐에 남은 작업은 버려짐. SIGTERM 기본 핸들러는 프로세스를 끝냄 | https://nodejs.org/en/learn/asynchronous-work/dont-block-the-event-loop · "Node.js runs JavaScript code in the Event Loop (initialization and callbacks), and offers a Worker Pool to handle expensive tasks like file I/O." / "Because Node.js handles many clients with few threads, if a thread blocks handling one client's request, then pending client requests may not get a turn until the thread finishes its callback or task." / https://nodejs.org/api/process.html · "Calling process.exit() will force the process to exit as quickly as possible even if there are still asynchronous operations pending that have not yet completed fully" / "The Node.js process will exit immediately after calling the 'exit' event listeners causing any additional work still queued in the event loop to be abandoned." / "'SIGTERM' and 'SIGINT' have default handlers on non-Windows platforms that reset the terminal mode before exiting with code 128 + signal number." · 2026-10-03 |

## 3. 프레임워크 동시성 모델이 플랫폼 결과를 바꾸는가

**결론: 플랫폼 결과(응답 후 CPU가 있나·작업이 끝나나)는 바꾸지 않는다. 바꾸는 것은 성능(응답 후 작업이 같은 인스턴스의 다른 요청을 막는가)이다.** 모두 §4의 유도이며, "프레임워크와 무관하다"고 직접 말한 공식 문장은 찾지 못했다.

| 질문 | 답 | 근거 |
|---|---|---|
| 스레드냐 이벤트 루프냐에 따라 Lambda 동결이 달라지나 | 아니다. 동결 대상은 실행 환경 전체 | §4 D12 (Lambda "freezes the execution environment") |
| Cloud Run 요청 기반에서 Spring `@Async` 스레드는 CPU를 받나 | 다른 요청이 그 인스턴스에서 처리 중일 때만. FastAPI·Node도 같음 | §4 D3, D12 (Google 문서는 "background threads or routines"를 함께 금지) |
| 인스턴스 기반 Cloud Run·Fargate·VM·k8s에서 차이가 나나 | CPU는 모두 받는다(유도). 차이는 같은 프로세스 안 경쟁: Node는 단일 Event Loop라 CPU 무거운 응답 후 작업이 다른 요청을 막고, FastAPI는 `async def` CPU 작업이 루프를 막고 `def` 작업은 스레드 풀 40개를 나눠 쓰며, Spring은 요청 스레드와 다른 실행기 풀을 쓴다 | §2 표 |
| Lambda에서 동시성 모델이 처리량을 바꾸나 | Lambda(기본)는 환경당 요청 1개라, 프로세스 안 동시성 모델로 한 환경이 여러 요청을 받지 않는다 | §1.1 "cannot process other requests", §4 D13 |
| Lambda Node.js 콜백 핸들러 | 예외: 이벤트 루프가 빌 때까지 응답을 미룬다(기본). 응답 후 작업이 "응답 전 작업"이 되어 응답이 늦어진다. Function URL + Web Adapter(Express 등)에는 해당 없음 | §1.1 nodejs-handler 인용 |
| 프로세스 종료 시 잃는가 | 모든 방식이 같은 프로세스 안이라 플랫폼이 SIGKILL하면 잃는다. Spring은 기본으로 실행기 작업을 기다리지 않고, Node는 SIGTERM 기본 핸들러로 종료, Python 데몬 스레드는 갑자기 멈춘다 | §4 D9~D11 |

## 4. 유도된 사실(정의상)

각 항목은 인용한 사실 하나(또는 같은 페이지의 두 문장)에서 한 단계만 이끌었다. 판정 규칙에 쓰기 전에 사람이 검토해야 한다.

- **D1** 정의상/유도: Lambda "Background processes or callbacks ... resume if Lambda reuses the execution environment" + "Lambda terminates execution environments every few hours" → 응답 후 작업은 환경이 다시 쓰이기 전에 종료되면 끝나지 못한다(완료 보장 없음).
- **D2** 정의상/유도: Lambda "Lambda freezes the execution environment when the runtime and each extension have completed" → 런타임이 Web Adapter든 관리형 런타임이든, 런타임이 호출 완료를 알린 뒤의 작업은 동결된다. (Web Adapter가 언제 완료를 알리는지는 공식 문서에서 명시 문장 못 찾음.)
- **D3** 정의상/유도: Cloud Run "CPU is always allocated to all containers ... as long as the Cloud Run revision is processing at least one request" + "any subsequent request to the same container instance resumes any suspended background activity" → 요청 기반 과금에서 응답 후 작업의 진행·완료 시점은 그 인스턴스에 들어오는 다른 요청 트래픽에 달려 있다.
- **D4** 정의상/유도: Cloud Run 인스턴스 기반 "Idle instances, including those kept warm using minimum instances, can be shut down at any time" → min-instances를 둬도 응답 후 작업이 끝날 때까지 인스턴스가 살아 있다는 보장은 없고, 보장되는 것은 SIGTERM 뒤 10초다.
- **D5** 정의상/유도: ECS "The hard limit of CPU units to present for the task" + 서비스가 태스크를 "run and maintain" → Fargate 태스크 CPU는 HTTP 요청이 아니라 태스크 단위로 정의되므로 응답 후에도 태스크가 실행 중이면 CPU를 쓴다. (요청 기반 동결·스로틀이 없다는 직접 문장은 없음. 이 유도는 그런 메커니즘이 문서에 없다는 점에 기댄다.)
- **D6** 정의상/유도: EC2 "you keep the instance running, even if the instance remains idle" / "The instance is running and ready for use." → VM 안 프로세스는 HTTP 응답 여부와 무관하게 실행된다.
- **D7** 정의상/유도: Compute Engine "You control the lifecycle of your compute instances." → 플랫폼이 요청 유무로 VM을 멈추지 않는다. e2 공유 코어의 CPU 시간 비율은 요청과 무관한 상시 제한이다.
- **D8** 정의상/유도: Kubernetes "The kubelet also reserves at least the request amount ... specifically for that container" / "cpu limits are enforced by CPU throttling." → GKE Autopilot·EKS의 CPU는 컨테이너 단위로 예약·제한되며, 응답 후 작업도 limit까지 CPU를 쓴다.
- **D9** 정의상/유도: Starlette "in-process background tasks" + 플랫폼의 SIGKILL(Cloud Run 10초, ECS 기본 30초, Kubernetes 기본 30초) → FastAPI·Starlette 응답 후 작업은 유예 시간 안에 끝나지 않으면 잃는다.
- **D10** 정의상/유도: Spring Boot `spring.task.execution.shutdown.await-termination` 기본 `false` → 기본 설정에서 종료 시 `@Async` 실행기의 남은 작업을 기다리지 않는다.
- **D11** 정의상/유도: Node.js SIGTERM 기본 핸들러가 "exiting with code 128 + signal number" + 'exit' 뒤 "any additional work still queued in the event loop to be abandoned" → 핸들러를 달지 않으면 SIGTERM 시 대기 중인 `setTimeout`·Promise 작업은 버려진다.
- **D12** 정의상/유도: 플랫폼 인용은 CPU를 "execution environment"(Lambda), "instance"(Cloud Run) 단위로 주거나 끊고, Google은 "background threads or routines"를 함께 다룬다 → 스레드·이벤트 루프 같은 프로세스 안 동시성 모델은 응답 후 CPU 유무를 바꾸지 않는다.
- **D13** 정의상/유도: Lambda "this execution environment is busy and cannot process other requests" → Lambda(기본)에서는 프로세스 안 동시성 모델이 한 환경의 동시 요청 수를 늘리지 않는다.
- **D14** 정의상/유도: Docker "Compose ... deploys everything to a single node" ([capabilities/05](capabilities/05-compute-tier1-2.md) 1012행, §7.1·§7.2 단일 VM + compose 구성) → VM compose 구성은 요청이 컨테이너로 직접 들어가 플랫폼이 요청 시간을 강제하지 않는다. KB `CP.platform_request_timeout: false`(EC2·Compute Engine compose)로 두고, A2 시간 규칙(`CAP-TIMEOUT-001~003`)은 이 값이 false면 통과한다. 다른 플랫폼은 `CP.max_request_seconds`와 같은 인용으로 `true`(공식). 앞에 LB를 두면 이 유도는 성립하지 않는다(LB 유휴 타임아웃이 생김).
- **D15** 정의상/유도: D1·D13(Lambda는 환경당 요청 하나, 호출이 끝나면 동결) → Lambda에는 계속 떠서 요청을 받아 넘기는 서버 프로세스(nginx 같은 리버스 프록시·게이트웨이)를 둘 수 없다. KB `CP.runs_long_lived_server: false`(Lambda), 규칙 `CAP-PROXY-001`. 나머지 플랫폼은 각 문서의 "listen for requests"(Cloud Run 05:91), 서비스·Deployment가 태스크·Pod를 "run and maintain"/유지(ECS 05:349, GKE 05:1001, EKS 05:1006), VM은 유휴여도 실행(EC2 05:928, Compute Engine 1.6행)에서 `true`로 유도했다.
- **D16** 정의상/유도: D13(실행 환경당 요청 하나, 요청에 맞춰 환경 수가 늘고 줄어듦) → Lambda에는 저장소가 밝힌 최소 레플리카(`replicas`·HPA `minReplicas`)에 대응하는 개념이 없다. 추천 비용 계산은 Lambda 비용에 최소 레플리카를 곱하지 않는다(`infrafit/fit/recommend.py` `NO_REPLICA_TARGETS`).

## 5. 엔진 규칙에 주는 시사점

[knowledge/capabilities.yaml](../../knowledge/capabilities.yaml)은 고치지 않았다. 아래는 검토용이다.

| KB 값 | 이 문서 | 판단 |
|---|---|---|
| `cp:aws/lambda/function-url` `CP.cpu_after_response: false` | §1.1 동결·"Make sure ... complete before the code exits" | **지지**. 재사용 시 재개되지만 보장되지 않음(D1) |
| `cp:gcp/cloud-run/request-billing` `CP.cpu_after_response: false` | §1.2 "disabled or severely limited", 백그라운드 스레드 금지 | **지지**. 더 직접적인 인용(tips/general)이 있다. 다른 요청이 있으면 재개되지만 보장되지 않음(D3) |
| request-billing에 `CP.cpu_after_response_config` 없음(일부러) | §1.2: 켜는 방법은 `--no-cpu-throttling`, 즉 인스턴스 기반 과금 | **지지**. KB 주석의 "켜는 방법은 다른 후보"와 같음 |
| `cp:gcp/cloud-run/instance-billing` `CP.cpu_after_response: true` | §1.3 | **지지**. 단 문서는 "short-lived background tasks"라고 한정하고 유휴 인스턴스는 언제든 종료(D4) |
| instance-billing `CP.always_on: false` | §1.3 "can be shut down at any time" | **지지** |
| instance-billing `CP.always_on_config: "min-instances ≥ 1"` (인용 "allocates CPU even outside of request processing") | §1.3 about-instance-autoscaling "you should set minimum instances to at least 1 to ensure that the CPU remains allocated for background processing" | **값은 지지, 인용은 교체 후보**. 현재 인용은 min-instances를 말하지 않는다. 이 문장이 값을 직접 뒷받침한다(05 문서에 줄 추가 필요) |
| `cp:aws/ecs-fargate/alb` `CP.cpu_after_response` 생략(unknown) | §1.4 명시 문장 없음, D5 유도만 | **지지(생략 유지)**. 값을 넣으려면 D5를 사람이 승인해야 함 |
| EC2·Compute Engine `CP.cpu_after_response` 생략 | §1.5·1.6 명시 문장 없음, D6·D7 유도 | **지지(생략 유지)**. 같은 이유 |
| GKE Autopilot·EKS `CP.cpu_after_response` 생략 | §1.7·1.8 클라우드 문서 명시 문장 없음, Kubernetes 문서로 D8 유도 | **지지(생략 유지)**. kubernetes.io 인용은 적격이므로 D8을 승인하면 근거로 쓸 수 있음 |
| `rules.yaml` `CAP-SINGLERUN-002`: `CP.cpu_after_response: true`만으로 앱 안 스케줄러 통과 | §1.3 "An instance will never stay idle for more than 15 minutes after processing a request unless it is kept active using minimum instances." | **주의**. 인스턴스 기반 Cloud Run은 응답 후 CPU가 있어도 요청이 없으면 15분 안에 인스턴스가 사라져 스케줄러가 멈춘다. 같은 차원(B3)의 `CAP-SINGLERUN-001`이 수동 확장(`--scaling=1`)을 요구하므로 함께 적용될 때만 맞다. 단독 통과는 근거와 어긋난다 |
| `dimensions.md` 138행 "요청 밖 CPU 미할당 ⚠️근거없음" | §1.2 tips/general 인용 | **근거 생김**. 해당 줄에 인용을 달 수 있다 |
| (없는 키) 종료 유예 시간 | §1.2·1.4·1.7: Cloud Run 10초, ECS 기본 30초(최대 120초), Kubernetes 기본 30초, Lambda 종료 단계 0 ms(확장 없음) | 응답 후 작업의 유실 위험을 판정하려면 새 능력 키 후보 |

KB 값과 **정면으로 모순되는 공식 문장은 찾지 못했다.**

## 6. 반영 (2026-10-03, 유도 사실 승인 후)

사람이 "유도 사실"을 공급자 인용 값과 따로 적어 쓰도록 승인했다([README.md](../../README.md) §3). [knowledge/capabilities.yaml](../../knowledge/capabilities.yaml)에 아래를 `source.basis: derived`(전제 인용 `from` + `reasoning`)로 넣었다. 판정 결과(fit.json·recommendation.json)의 근거에는 `basis: derived`와 reasoning이 붙고, 설명 문구에 "정의상/유도"가 들어간다.

| KB 값 | 유도 |
|---|---|
| ECS Fargate·EC2·Compute Engine·GKE Autopilot·EKS `CP.cpu_after_response: true` | D5·D6·D7·D8 (전제: 이 문서 1.4~1.7절 행) |
| EC2·Compute Engine compose `CP.platform_request_timeout: false` | D14 |
| `CP.runs_long_lived_server` (Lambda false, 나머지 true) | D15 |
| Lambda 비용에 최소 레플리카를 곱하지 않음 | D16 (코드 규칙) |

같이 바꾼 것(§5 표의 판단을 따름):
- `CAP-SINGLERUN-002`: 앱 안 스케줄러는 `CP.always_on: true`이거나 붙잡아 두는 설정(`CP.always_on_config`)이 있을 때만 통과(feasible_with_config). `CP.cpu_after_response`만으로는 통과하지 않는다(§1.3 15분 유휴 종료).
- Cloud Run 인스턴스 기반 `CP.always_on_config` 인용을 about-instance-autoscaling 문장("set minimum instances to at least 1 to ensure that the CPU remains allocated for background processing")으로 바꿨다([capabilities/05](capabilities/05-compute-tier1-2.md) 1014행).
- [dimensions.md](dimensions.md) 2.2절 "요청 밖 CPU 미할당"에 §1.2 tips/general 인용을 달았다.

