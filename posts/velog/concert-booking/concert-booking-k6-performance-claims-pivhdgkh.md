# [콘서트 예매 시스템] k6 성능 결과를 어디까지 주장할 수 있을까

## 이 글의 위치

콘서트 예매 시스템 시리즈는 `정합성 문제 발견 -> 동시성 제어 -> 이벤트 유실 방지 -> 성능/운영 경계` 순서로 읽으면 흐름이 가장 자연스럽다.

1. 좌석은 왜 두 번 팔리면 안 되는가 - 이전 흐름
2. 같은 좌석을 100명이 동시에 잡으면 어떻게 될까 - 이전 흐름
3. 비관적 락, 낙관적 락, Redis 분산 락을 비교해보았다 - 이전 흐름
4. 대기열 토큰은 왜 예매 트랜잭션 앞에서 검증해야 할까 - 이전 흐름
5. 결제, 만료, 중복 요청이 동시에 오면 상태는 어떻게 지킬까 - 이전 흐름
6. Outbox와 Kafka로 이벤트 유실 구간 줄이기 - 이전 흐름
7. Redis stock은 왜 최종 기준 데이터가 아니어야 할까 - 이전 흐름
8. k6 성능 결과를 어디까지 주장할 수 있을까 - 현재 글
9. 운영자가 볼 수 있는 지표와 알림 만들기 - 다음 흐름
10. 면접에서 이 프로젝트를 어떻게 설명할까 - 다음 흐름

## 코드 또는 검증 근거

성능 글에서는 실행 가능한 시나리오와 아직 운영 성능으로 주장하지 않는 범위를 분리했다. `k6/run-all.sh`에서도 기본 실행은 공개 측정 완료 항목인 scenario A/B/C로 제한하고, D/E/F는 명시적으로 포함할 때만 실행하도록 구분했다.

```bash
# 기본 실행은 공개 측정 완료 항목인 scenario-a/b/c만 실행합니다.
# scenario-d/e/f는 smoke, targeted run, formal local repeat 기록이 있으며
# 재실행할 때는 명시적으로 INCLUDE_PENDING=1을 줍니다.
#
# scenario-d/e/f까지 포함:
#   INCLUDE_PENDING=1 bash k6/run-all.sh
```

그래서 글의 결론도 “운영 환경에서 이 TPS를 보장한다”가 아니라, 로컬 Docker 환경에서 어떤 경계까지 확인했고 어떤 주장은 하지 않는지로 제한했다.

## 들어가며

부하 테스트 결과를 글에 넣을 때 가장 조심한 부분은 숫자 자체보다 숫자의 해석이었다.

예를 들어 "100명이 동시에 같은 좌석을 예매했고 성공 1, 실패 99, overselling 0"이라는 결과는 분명 의미가 있다. 하지만 이것을 곧바로 운영 성능이나 수용량 근거처럼 말하면 안 된다.

로컬 Docker 단일 실행은 운영 환경이 아니다. 반복 통계도 아니고, 네트워크나 실제 결제 연동도 없다. 그러면 이 수치는 어디까지 말할 수 있을까?

이 글은 `concert-booking`에서 k6 결과를 어떻게 측정값과 주장하지 않는 범위로 분리했는지 정리한 글이다.

Repository는 [sjh9714/concert-booking](https://github.com/sjh9714/concert-booking)이다.

## 먼저 claim boundary를 정했다

`docs/PERF_RESULT.md`는 첫 문장에서 이 문서의 경계를 정한다.

새 수치를 만들지 않고, k6로 실제 측정한 값과 아직 측정하지 않은 시나리오를 분리해서 기록한다는 것이다.

이 프로젝트에서 성능 관련 기록은 크게 두 종류로 나눴다.

| 구분 | 의미 |
| --- | --- |
| measured | k6로 수치를 측정했고 표에 기록한 로컬 결과 |
| verified | Testcontainers 통합 테스트 또는 제한된 k6 run으로 정책/분기/threshold를 확인한 결과 |

이 구분이 중요했다.

모든 k6 실행이 성능 측정은 아니다. 어떤 실행은 branch가 제대로 통과하는지 확인하기 위한 시나리오 검증이다. 그 둘을 섞으면 글이 과장된다.

## Scenario A/B/C는 로컬 Docker 단일 실행

성능 수치로 기록한 것은 A/B/C 세 가지다.

| Scenario | 목적 |
| --- | --- |
| A | 동일 좌석 100명 동시 예매 |
| B | 50명이 서로 다른 좌석 예매 |
| C | 70% 조회 + 30% 예매 혼합 부하 |

README에는 다음 결과가 정리되어 있다.

| 항목 | 결과 |
| --- | --- |
| 동일 좌석 100 concurrent requests | success 1, fail 99, overselling 0 |
| 50명/50좌석 분산 예매 | 비관적 50/50, 낙관적 20/50, Redis 분산 락 50/50 |
| 혼합 부하 테스트 | 총 RPS: 비관적 969, 낙관적 993, Redis 분산 락 1,005 |

이 숫자는 프로젝트 설명에 도움이 된다.

특히 Scenario A는 예매 시스템에서 가장 중요한 질문을 직접 보여준다.

```text
같은 좌석을 100명이 동시에 잡으려 해도
한 좌석은 한 번만 팔리는가?
```

하지만 이 결과는 운영 환경의 처리량이나 SLO 근거가 아니다.

문서에서는 계속 "로컬 Docker 단일 실행"이라고 제한했다. 평균, 표준편차, 신뢰구간도 계산하지 않았다. 따라서 이 숫자는 성능 benchmark라기보다 정합성 중심의 로컬 부하 검증으로 보는 편이 맞다.

## Scenario D/E/F는 성능 비교가 아니다

다음 시나리오들은 이름만 보면 k6 성능 테스트처럼 보일 수 있다.

| Scenario | 검증 대상 |
| --- | --- |
| D | 결제/만료 race |
| E | idempotency replay/conflict |
| F | queue token abuse |

하지만 이 프로젝트에서는 D/E/F를 운영 성능 비교로 쓰지 않았다.

이 시나리오들의 목적은 branch와 threshold 검증이었다.

- 결제와 만료가 동시에 들어올 때 하나의 방향만 이기는가
- 같은 idempotency key replay와 다른 payload conflict가 구분되는가
- token 없음, 다른 사용자 token, 다른 schedule token, 만료 token이 차단되는가

`docs/evidence/SCENARIO_D_E_F_FORMAL_2026-05-22.md`에는 세 전략 x 3회 formal local repeat 결과가 남아 있다.

| Scenario | 결과 |
| --- | --- |
| D | 216/216 passed |
| E | 234/234 passed |
| F | 144/144 passed |

이 결과는 의미가 있다.

하지만 의미는 "latency가 얼마다"가 아니라 "정의한 branch와 threshold가 반복 실행에서 깨지지 않았다"에 가깝다.

## 왜 수치를 과장하면 안 되나

성능 숫자는 포트폴리오에서 강하게 보인다.

그래서 더 조심해야 한다.

로컬 Docker 단일 실행에서 나온 RPS를 그대로 "초당 1,000건 처리"처럼 쓰면 읽는 사람이 오해할 수 있다. 실제 운영 환경에서는 DB 크기, 인덱스 상태, network, container resource, JVM warm-up, 결제 연동, tracing, 로그, 배포 토폴로지에 따라 결과가 달라진다.

이 프로젝트의 결제도 mock payment 즉시 성공 구조다. 외부 PG latency, 승인 실패, webhook 흐름은 포함하지 않는다.

따라서 k6 수치는 이렇게 설명하는 것이 안전했다.

```text
로컬 Docker 환경에서 같은 fixture로 실행한 단일 검증 결과다.
운영 성능, SLO, 수용량 근거로 사용하지 않는다.
```

이 한 문장이 글의 신뢰도를 지킨다.

## Testcontainers와 k6의 역할을 나눴다

이 프로젝트에서는 Testcontainers 통합 테스트와 k6를 서로 다른 용도로 사용했다.

Testcontainers는 도메인 불변식을 더 정확히 검증한다.

- 같은 reservation row가 동시에 confirmed/expired가 되지 않는지
- idempotency key가 replay와 conflict를 구분하는지
- Redis stock이 실패 경로에서 복원되는지
- Outbox와 DLT 흐름이 기대 상태로 전이되는지

k6는 API 경계에서 여러 요청을 넣어 aggregate 결과를 본다.

- 같은 좌석에 동시에 요청이 몰릴 때 overselling이 0인지
- abuse branch가 실제 HTTP 요청으로 차단되는지
- final summary에서 duplicate row가 생기지 않는지

둘 중 하나만 있으면 부족했다.

단위나 통합 테스트는 상태 전이를 자세히 보기 좋고, k6는 실제 API 형태로 여러 요청이 들어오는 상황을 보기 좋다. 대신 k6 결과는 수치 해석을 제한해야 했다.

## 문서에 남긴 한계

`docs/LIMITATIONS.md`에는 현재 주장하지 않는 항목을 따로 적었다.

- 세 시나리오 장기 반복 통계
- 세 시나리오 운영 성능 비교
- 대기열 token abuse 부하 성능
- 운영형 observability
- Outbox exactly-once
- Redis 최종 기준 데이터
- production 성능

이 문서가 있는 이유는 단순하다.

포트폴리오 프로젝트에서 "무엇을 했다"만큼 "무엇은 아직 주장하지 않는다"도 중요하기 때문이다.

기술 글을 쓰다 보면 자신이 만든 것을 더 크게 보이게 말하고 싶어진다. 하지만 유지보수자나 면접관은 수치보다 해석의 정직함을 더 중요하게 볼 수 있다.

## 배운 점

k6를 쓰면 숫자를 얻을 수 있다.

하지만 좋은 성능 글은 숫자를 많이 나열하는 글이 아니라, 숫자가 어떤 조건에서 나온 것인지 설명하는 글이라고 느꼈다.

이 프로젝트에서는 A/B/C를 로컬 Docker 단일 실행 결과로 남겼고, D/E/F는 branch/threshold 검증으로 분리했다. 이 구분 덕분에 숫자를 쓰면서도 과장하지 않을 수 있었다.

결국 부하 테스트 결과의 핵심은 "얼마나 빠른가"만이 아니었다.

어떤 조건에서, 어떤 fixture로, 어떤 실패를 확인했고, 어디까지는 말하지 않는지가 함께 있어야 했다.

## 포트폴리오 메모

k6 Scenario A/B/C로 동일 좌석 경합, 분산 좌석 예약, 혼합 부하를 로컬 Docker 단일 실행 기준으로 검증하고 결과를 문서화했다. Scenario D/E/F는 운영 성능 비교가 아니라 결제/만료 race, idempotency replay/conflict, queue token abuse branch와 threshold 검증으로 분리했으며, `docs/PERF_RESULT.md`, `docs/TESTING.md`, `docs/LIMITATIONS.md`에 측정값과 주장하지 않는 범위를 명확히 기록했다.
