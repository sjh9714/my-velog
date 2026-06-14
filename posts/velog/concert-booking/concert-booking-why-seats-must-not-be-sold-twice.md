# [콘서트 예매 시스템] 좌석은 왜 두 번 팔리면 안 되는가

## 이 글의 위치

콘서트 예매 시스템 시리즈는 `정합성 문제 발견 -> 동시성 제어 -> 이벤트 유실 방지 -> 성능/운영 경계` 순서로 읽으면 흐름이 가장 자연스럽다.

1. 좌석은 왜 두 번 팔리면 안 되는가 - 현재 글
2. 같은 좌석을 100명이 동시에 잡으면 어떻게 될까 - 다음 흐름
3. 비관적 락, 낙관적 락, Redis 분산 락을 비교해보았다 - 다음 흐름
4. 대기열 토큰은 왜 예매 트랜잭션 앞에서 검증해야 할까 - 다음 흐름
5. 결제, 만료, 중복 요청이 동시에 오면 상태는 어떻게 지킬까 - 다음 흐름
6. Outbox와 Kafka로 이벤트 유실 구간 줄이기 - 다음 흐름
7. Redis stock은 왜 최종 기준 데이터가 아니어야 할까 - 다음 흐름
8. k6 성능 결과를 어디까지 주장할 수 있을까 - 다음 흐름
9. 운영자가 볼 수 있는 지표와 알림 만들기 - 다음 흐름
10. 면접에서 이 프로젝트를 어떻게 설명할까 - 다음 흐름

## 들어가며

처음에는 예매 시스템을 단순하게 생각했다.

사용자가 좌석을 선택하면 reservation을 만들고, 결제하면 좌석 상태를 RESERVED로 바꾸면 된다고 생각했다. 화면에서 좌석을 고르고, 버튼을 누르고, 결제가 끝나면 예매가 완료되는 흐름만 보면 그렇게 보이기 쉽다.

하지만 동시에 100명이 같은 좌석을 예매하려고 한다면 이야기가 달라진다.

한 좌석은 한 명에게만 팔려야 한다. 대기열을 건너뛰고 예매 API를 직접 호출하면 안 된다. 사용자가 결제 버튼을 두 번 눌러도 결제가 두 번 처리되면 안 된다. 예약 만료 스케줄러와 결제 요청이 동시에 실행되어도 상태가 꼬이면 안 된다. DB commit 이후 Kafka publish가 실패해도 이벤트가 조용히 사라지면 안 된다.

이 프로젝트는 이런 문제를 하나씩 분리해서 검증해본 콘서트 예매 백엔드 프로젝트다.

Repository는 [sjh9714/concert-booking](https://github.com/sjh9714/concert-booking)이다.

## 왜 콘서트 예매 시스템인가

콘서트 예매는 백엔드 포트폴리오 주제로 자주 보인다. 하지만 그냥 CRUD로 만들면 보여줄 수 있는 것이 많지 않다.

진짜 중요한 부분은 "예약을 생성한다"가 아니라 "예약이 동시에 몰려도 데이터가 깨지지 않는다"에 가깝다.

예매 시스템에서 특히 위험한 상황은 이런 것들이었다.

- 같은 좌석에 동시에 여러 요청이 들어온다.
- 대기열을 통과하지 않은 사용자가 예매 API를 직접 호출한다.
- 네트워크 timeout이나 더블클릭 때문에 같은 요청이 반복된다.
- 결제 요청과 예약 만료 스케줄러가 거의 동시에 실행된다.
- DB transaction은 성공했지만 Kafka publish가 실패한다.
- Redis stock과 DB 좌석 상태가 어긋난다.

이 중 하나만 놓쳐도 사용자는 이상한 결과를 보게 된다.

좌석이 두 번 팔리거나, 대기열을 우회한 사용자가 예매에 성공하거나, 결제가 두 번 처리되거나, 취소된 좌석이 돌아오지 않을 수 있다.

그래서 이 프로젝트의 중심은 "기능을 많이 만들었다"가 아니라 "깨지기 쉬운 지점을 어디까지 검증했는가"에 두었다.

## 단순 예매 CRUD와 실제 예매 시스템의 차이

단순 CRUD라면 흐름은 간단하다.

```text
좌석 조회
→ 예약 생성
→ 결제
→ 예약 완료
```

하지만 실제 예매 시스템에 가까워질수록 이 흐름 앞뒤에 더 많은 조건이 붙는다.

```text
대기열 진입
→ 입장 토큰 발급
→ 예매 API 호출
→ 좌석 HELD + 예약 PENDING
→ 결제 요청
→ 예약 CONFIRMED + 좌석 RESERVED
→ Outbox event 저장
→ Kafka publish
```

여기서 중요한 것은 각 단계가 독립적으로 안전해야 한다는 점이다.

대기열 token은 예매 트랜잭션 앞에서 검증되어야 한다. 좌석 상태 변경과 예약 생성은 같은 트랜잭션 안에서 다뤄야 한다. 결제와 만료는 같은 예약 row를 동시에 바꾸지 못하게 해야 한다. 이벤트는 비즈니스 transaction과 publish 경계를 분리해야 한다.

결국 예매 시스템은 reservation 테이블에 row를 넣는 문제가 아니었다.

동시에 몰리는 요청 속에서 상태 전이를 지키는 문제였다.

## 이 프로젝트에서 다룬 핵심 문제

프로젝트에서 가장 먼저 지키려고 한 규칙은 "좌석은 두 번 팔리면 안 된다"였다.

이를 위해 세 가지 reservation strategy를 같은 API 계약에서 비교했다.

- 비관적 락
- 낙관적 락
- Redis 분산 락

각 전략은 장점이 다르지만, 어떤 전략이든 같은 좌석 경합에서 overselling이 발생하면 안 된다.

두 번째 문제는 대기열 우회였다.

Redis Sorted Set으로 대기열을 만들고, 입장 가능한 사용자에게 `userId + scheduleId`에 바인딩된 token을 발급했다. 예매 API는 이 token을 검증한 뒤에만 좌석 예약을 진행한다.

세 번째 문제는 중복 요청이었다.

사용자가 버튼을 두 번 누르거나 timeout 이후 같은 요청을 다시 보내면, 서버 입장에서는 같은 요청인지 다른 요청인지 구분해야 한다. 그래서 reservation과 payment에 `Idempotency-Key`를 사용했다.

네 번째 문제는 결제와 만료의 race였다.

예약은 일정 시간 동안 `PENDING` 상태로 유지된다. 그 사이 사용자가 결제하면 `CONFIRMED`가 되고, 시간이 지나면 scheduler가 `EXPIRED`로 바꿀 수 있다. 두 작업이 동시에 실행될 때 하나의 reservation이 confirmed이면서 expired인 상태가 되면 안 된다.

다섯 번째 문제는 이벤트 발행 실패였다.

DB commit 이후 Kafka publish가 실패하면, 비즈니스 데이터는 바뀌었는데 이벤트는 사라질 수 있다. 이를 줄이기 위해 Outbox table에 이벤트 발행 의도를 transaction 안에서 먼저 기록하고, 별도 relay가 Kafka로 publish하도록 했다.

## 전체 아키텍처

전체 구조는 크게 다섯 경계로 나눴다.

- 입장 제어: Redis Queue / Token
- 예매 트랜잭션: PostgreSQL
- 결제/만료 상태 전이: PostgreSQL row lock + domain guard
- 비동기 이벤트: Outbox table / Kafka
- 실패 처리: DLT / Admin replay / Redis stock reconciliation

간단히 그리면 이런 흐름이다.

```text
Client
→ Queue API
→ Reservation API
→ PostgreSQL
→ Outbox table
→ Outbox Relay
→ Kafka
→ Consumer
→ Seat release / Redis stock update
```

여기서 PostgreSQL은 좌석과 예약의 최종 기준 데이터다.

Redis는 대기열, token, stock pre-check에 사용하지만 최종 기준으로 두지 않았다. Redis stock은 빠른 보조 상태이고, 어긋날 수 있기 때문에 DB 기준 reconciliation utility를 따로 두었다.

이 점은 일부러 명확히 나눴다.

Redis를 쓰면 빠르게 실패 요청을 걸러낼 수 있지만, Redis 값이 항상 진실이라고 말할 수는 없다. 예매 도메인에서는 최종적으로 DB의 좌석 상태가 맞아야 한다.

## 검증한 것

이 프로젝트는 단순히 구조를 그리는 데서 끝내지 않고, 몇 가지 claim을 테스트와 k6로 확인했다.

대표적인 검증은 다음과 같다.

| 검증 항목 | 근거 |
| --- | --- |
| 동일 좌석 overselling 방지 | `ConcurrencyIntegrationTest`, `DistributedLockConcurrencyTest`, `OptimisticLockConcurrencyTest`, k6 Scenario A |
| 대기열 token 정책 | `QueueTokenPolicyIntegrationTest`, k6 Scenario F |
| 중복 예약/결제 방어 | `ReservationIdempotencyIntegrationTest`, `PaymentIdempotencyIntegrationTest`, k6 Scenario E |
| 결제/만료 race 방어 | `ReservationStateTransitionRaceIntegrationTest`, k6 Scenario D |
| Outbox relay / retry | `OutboxIntegrationTest` |
| Kafka DLT / replay | `KafkaDltReplayIntegrationTest` |
| Redis stock reconciliation | `StockReconciliationIntegrationTest` |

k6로 측정한 대표 수치도 있다.

동일 좌석 100 concurrent requests에서는 세 전략 모두 success 1, fail 99, overselling 0을 기록했다.

다만 이 수치는 로컬 Docker 단일 실행 기준이다. 실제 운영 환경 TPS나 SLO를 주장하기 위한 수치가 아니다. 평균, 표준편차, 신뢰구간도 계산하지 않았다.

이 프로젝트에서는 "무엇을 검증했는가"만큼 "무엇을 주장하지 않는가"도 중요하게 봤다.

## 주장하지 않는 것

이 프로젝트는 production-grade 예매 플랫폼이라고 주장하지 않는다.

특히 다음은 주장하지 않는다.

- 운영 환경 TPS
- production SLO
- 장기 반복 통계
- Outbox exactly-once
- Redis 자동 장애 복구
- production-grade observability

Outbox는 이벤트 유실 구간을 줄이기 위한 장치지만 exactly-once를 보장하지 않는다. Redis stock은 빠른 선검증용 캐시지만 최종 기준 데이터가 아니다. DLT replay와 Redis reconciliation은 자동 복구 시스템이 아니라 관리자 수동 utility다.

이렇게 한계를 분리하는 이유는 간단하다.

검증하지 않은 것을 포트폴리오에서 주장하면 오히려 신뢰가 떨어진다. 반대로 검증한 범위와 검증하지 않은 범위를 분리하면, 설계 판단을 더 안전하게 설명할 수 있다.

## 앞으로의 시리즈

이 글은 전체 프로젝트 소개에 가깝다.

다음 글부터는 각 문제를 하나씩 나눠서 정리하려고 한다.

- 같은 좌석을 100명이 동시에 잡으면 어떻게 되는지
- 비관적 락, 낙관적 락, Redis 분산 락이 어떻게 다른지
- 대기열 token을 왜 예매 트랜잭션 앞에서 검증해야 하는지
- 결제, 만료, 중복 요청이 동시에 올 때 상태를 어떻게 지키는지
- Outbox와 Kafka로 이벤트 발행 실패를 어떻게 다뤘는지

이 프로젝트를 통해 보여주고 싶은 것은 "Spring Boot로 예매 API를 만들었다"가 아니다.

동시성, 정합성, 멱등성, 비동기 이벤트 실패를 어떻게 나누어 생각했고, 어떤 테스트로 그 판단을 검증했는지다.

## 포트폴리오 메모

고동시성 콘서트 예매 도메인에서 동일 좌석 overselling, 대기열 token 우회, 중복 예약/결제, 결제/만료 race, 이벤트 발행 실패를 방어하는 Spring Boot 백엔드를 구현했다. PostgreSQL을 최종 정합성 기준으로 두고, Redis Queue/Token/Stock, 세 가지 reservation strategy, Outbox/Kafka/DLT, Testcontainers/k6 검증으로 각 실패 조건을 분리해 확인했다.
