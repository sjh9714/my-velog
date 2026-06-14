# [콘서트 예매 시스템] 운영자가 볼 수 있는 지표와 알림 만들기

## 이 글의 위치

콘서트 예매 시스템 시리즈는 `정합성 문제 발견 -> 동시성 제어 -> 이벤트 유실 방지 -> 성능/운영 경계` 순서로 읽으면 흐름이 가장 자연스럽다.

1. 좌석은 왜 두 번 팔리면 안 되는가 - 이전 흐름
2. 같은 좌석을 100명이 동시에 잡으면 어떻게 될까 - 이전 흐름
3. 비관적 락, 낙관적 락, Redis 분산 락을 비교해보았다 - 이전 흐름
4. 대기열 토큰은 왜 예매 트랜잭션 앞에서 검증해야 할까 - 이전 흐름
5. 결제, 만료, 중복 요청이 동시에 오면 상태는 어떻게 지킬까 - 이전 흐름
6. Outbox와 Kafka로 이벤트 유실 구간 줄이기 - 이전 흐름
7. Redis stock은 왜 최종 기준 데이터가 아니어야 할까 - 이전 흐름
8. k6 성능 결과를 어디까지 주장할 수 있을까 - 이전 흐름
9. 운영자가 볼 수 있는 지표와 알림 만들기 - 현재 글
10. 면접에서 이 프로젝트를 어떻게 설명할까 - 다음 흐름

## 들어가며

예매 시스템은 실패하지 않는 것만큼 실패를 볼 수 있는 것도 중요하다.

좌석 overselling이 없어야 하고, 대기열 token 우회가 막혀야 하고, Outbox와 Kafka 이벤트가 처리되어야 한다. 그런데 장애가 생겼을 때 어디서부터 봐야 할까?

이 프로젝트에서는 Spring Boot Actuator, Micrometer, Prometheus metric contract, synthetic alert rule test를 통해 로컬 검증용 관측 지표를 만들었다.

다만 이 글에서 말하는 관측성은 운영형 SLO나 실제 alert firing을 완성했다는 뜻이 아니다. 어디까지 검증했고 어디부터는 아직 주장하지 않는지 함께 정리한다.

Repository는 [sjh9714/concert-booking](https://github.com/sjh9714/concert-booking)이다.

## 무엇을 보고 싶었나

예매 시스템에서 보고 싶은 지표는 단순한 HTTP 요청 수만이 아니었다.

도메인 관점에서 다음 질문에 답해야 했다.

- 예매 시도가 성공했는가, 실패했다면 어떤 이유인가
- queue token 검증 실패가 갑자기 늘었는가
- Outbox relay가 backlog를 만들고 있는가
- Outbox event가 `DEAD` 상태로 쌓이고 있는가
- Redis stock reconciliation에서 mismatch가 발생했는가

이 질문들은 장애 대응 순서와도 연결된다.

예를 들어 reservation 실패가 늘었을 때, sold out이 정상적으로 발생한 것인지, queue token abuse가 늘어난 것인지, Redis stock mismatch가 생긴 것인지 구분해야 한다.

## Actuator 접근 정책

먼저 Actuator endpoint 접근 정책을 나눴다.

| Endpoint | 접근 정책 |
| --- | --- |
| `/actuator/health` | 인증 없이 조회 가능 |
| `/actuator/info` | 인증 없이 조회 가능 |
| `/actuator/metrics` | `ROLE_ADMIN` 필요 |
| `/actuator/prometheus` | `ROLE_ADMIN` 필요 |

health와 info는 기본 상태 확인용으로 열어두고, metrics와 Prometheus scrape endpoint는 관리자 권한이 필요하도록 했다.

`ActuatorSecurityIntegrationTest`는 metrics와 prometheus endpoint가 admin 권한을 요구하는지 확인한다.

로컬 Prometheus harness에서는 `local-monitoring` profile로 ADMIN JWT 기반 scrape를 실험할 수 있게 했다. 이것도 production 인증 방식이라고 주장하지 않고, 로컬 검증용 profile로 제한했다.

## Micrometer metric

대표 metric은 도메인 흐름에 맞춰 나눴다.

예매 관련 metric:

```text
concert.booking.reservation.attempts
concert.booking.reservation.success
concert.booking.reservation.failures
concert.booking.reservation.latency
```

Queue token 관련 metric:

```text
concert.booking.queue.token.issued
concert.booking.queue.token.validation.failures
concert.booking.queue.token.inflight.conflicts
```

Outbox relay 관련 metric:

```text
concert.booking.outbox.published
concert.booking.outbox.failed
concert.booking.outbox.dead
concert.booking.outbox.publish.latency
concert.booking.outbox.events
```

Stock reconciliation 관련 metric:

```text
concert.booking.stock.reconciliation.runs
concert.booking.stock.reconciliation.mismatches
concert.booking.stock.reconciliation.repairs
```

`BookingMetricsTest`는 reservation, queue token, Outbox, reconciliation metric이 의도한 분류로 기록되는지 확인한다.

## Outbox gauge는 snapshot으로 노출했다

Outbox 상태 count는 자주 보고 싶은 지표다.

하지만 Prometheus scrape가 올 때마다 DB를 조회하게 만들면, 관측 자체가 DB 부하가 될 수 있다.

그래서 Outbox gauge는 scheduled snapshot 방식으로 갱신했다.

```text
scheduled refresh
→ outbox_events count by status
→ AtomicLong gauge update
→ Prometheus scrape reads gauge
```

`OutboxMetricsSnapshotSchedulingIntegrationTest`는 pending/failed count가 scheduling으로 갱신되는지 확인한다.

이 구조는 운영형 최적화라기보다, scrape 시점 DB 조회를 피하는 방향을 로컬 검증으로 고정한 것이다.

## Prometheus metric contract

Prometheus와 Grafana 템플릿에서 참조하는 metric 이름이 실제 actuator output에 없으면 템플릿은 있어도 쓸 수 없다.

그래서 `PrometheusScrapeContractIntegrationTest`를 두었다.

이 테스트는 `monitoring/alert-rules.yml`과 Grafana dashboard가 참조하는 Prometheus metric name이 보호된 `/actuator/prometheus` 응답에 노출되는지 확인한다.

Micrometer 이름은 Prometheus scrape에서 형식이 바뀐다.

예를 들어 counter는 `_total` suffix가 붙고, dot은 underscore로 변환된다.

```text
concert.booking.queue.token.validation.failures
→ concert_booking_queue_token_validation_failures_total
```

이 mapping이 템플릿과 어긋나면 alert rule은 조용히 의미를 잃을 수 있다. 그래서 metric name contract를 테스트로 고정했다.

## Alert rule은 synthetic test로만 검증했다

`monitoring/alert-rules.yml`에는 로컬 검증용 alert rule이 있다.

대표적으로 다음 alert를 둔다.

- `OutboxDeadEventsPresent`
- `StockMismatchDetected`
- `QueueTokenValidationFailuresHigh`

그리고 `monitoring/alert-rules.test.yml`로 synthetic time series에서 rule expression과 annotation이 맞는지 검증한다.

여기서도 경계를 명확히 했다.

이 테스트는 실제 운영 alert firing을 검증한 것이 아니다. Prometheus rule expression이 의도한 metric과 조건을 참조하는지 보는 단위 검증에 가깝다.

실제 운영에서는 alert routing, silence, notification channel, runbook drill이 필요하다. 이 프로젝트는 그 단계까지 주장하지 않는다.

## Local Prometheus evidence

로컬 Prometheus server scrape artifact도 남겼다.

`docs/evidence/monitoring/prometheus-20260522T155512Z/capture-summary.json`은 다음을 검산한다.

- local Prometheus target 1개가 `up`인지
- 필수 alert rule이 로딩되었는지
- Outbox query series가 존재하는지

이 artifact는 한 단계 더 실제적인 근거다.

하지만 이것도 production observability는 아니다. README와 monitoring 문서에는 이 점을 반복해서 적었다.

```text
local Prometheus server scrape evidence
not alert firing, dashboard operation, tracing, or SLO readiness
```

관측성은 특히 과장하기 쉬운 영역이다. dashboard JSON과 alert rule 파일이 있다고 해서 운영 중인 관측 체계가 있는 것은 아니다.

## Runbook과 연결하기

Metric은 보는 방법이 있어야 의미가 있다.

`docs/RUNBOOK.md`는 대표적인 장애 상황을 기준으로 확인 순서를 적었다.

Outbox DEAD가 늘면:

- `/actuator/prometheus`에서 outbox 관련 metric 확인
- `outbox_events`의 status, event_type, aggregate_id, retry_count, last_error 확인
- Kafka broker와 topic 접근 가능 여부 확인
- consumer 실패라면 DLT topic과 payload 확인

Redis stock mismatch가 생기면:

- reconciliation dry-run으로 DB available seat count와 Redis stock 비교
- 분산 락 실패, consumer 실패, 수동 fixture reset 여부 확인
- 필요하면 DB 기준으로 repair 후 다시 dry-run

Queue token validation failure가 늘면:

- 실패 사유별 log와 metric 확인
- userId, scheduleId binding이 깨진 요청인지 확인
- abuse가 의심되면 별도 운영 계층의 rate limit이나 차단 정책을 고려

Metric, alert, runbook은 따로 쓰면 약하다. 어떤 지표를 보고 어떤 조치를 할지 연결되어야 한다.

## 배운 점

관측성은 "Prometheus를 붙였다"로 끝나지 않았다.

무엇을 metric으로 볼지, 그 metric 이름이 템플릿과 맞는지, alert rule이 어떤 조건을 보는지, 그 alert를 받으면 어떤 순서로 확인할지까지 이어져야 했다.

다만 이 프로젝트에서는 로컬 검증용 관측성까지만 주장했다. 실제 alert firing, dashboard 운영, tracing, SLO 체계는 별도 운영 경험과 증거가 필요하다.

오히려 그 한계를 명시하는 것이 글의 신뢰도를 높인다고 느꼈다.

## 포트폴리오 메모

Spring Boot Actuator와 Micrometer로 reservation, queue token, Outbox, stock reconciliation 지표를 노출하고, Prometheus metric name contract와 synthetic alert rule test로 로컬 관측성 경계를 검증했다. Outbox gauge는 scheduled snapshot으로 갱신해 scrape 시점 DB 조회를 피했고, local Prometheus scrape artifact와 runbook으로 Outbox DEAD, Redis stock mismatch, queue token validation failure 대응 흐름을 정리했다. 실제 alert firing, dashboard 운영, tracing, SLO는 아직 주장하지 않는 범위로 분리했다.
