# [콘서트 예매 시스템] 면접에서 이 프로젝트를 어떻게 설명할까

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
9. 운영자가 볼 수 있는 지표와 알림 만들기 - 이전 흐름
10. 면접에서 이 프로젝트를 어떻게 설명할까 - 현재 글

## 들어가며

프로젝트 글을 9편까지 쓰고 나면 마지막으로 남는 질문이 있다.

면접에서는 이 프로젝트를 어떻게 설명해야 할까?

기능 목록을 길게 나열하면 오히려 핵심이 흐려진다. "Spring Boot, Redis, Kafka, k6, Testcontainers를 썼습니다"라고 말하는 것만으로는 설계 의도를 보여주기 어렵다.

이 프로젝트의 핵심은 기술 스택이 아니라 고동시성 예매 도메인에서 정합성 문제를 식별하고, 실패 경계를 나누고, 테스트로 검증한 과정이다.

이 글은 `concert-booking`을 면접에서 어떻게 설명하면 좋을지 정리한 글이다.

Repository는 [sjh9714/concert-booking](https://github.com/sjh9714/concert-booking)이다.

## 30초 요약

가장 먼저 준비할 것은 짧은 요약이다.

```text
동일 좌석 경합에서 overselling을 막고,
대기열 token 우회, 중복 요청, 결제/만료 race,
DB commit 이후 이벤트 발행 실패를 다룬 콘서트 예매 백엔드입니다.

Redis는 queue, token, stock pre-check에 사용했지만
최종 기준 데이터는 PostgreSQL seat/reservation 상태로 두었습니다.

Testcontainers 통합 테스트와 제한된 k6 로컬 시나리오로
정합성 branch와 실패 경계를 검증했습니다.
```

이 요약에서 중요한 것은 세 가지다.

- 어떤 문제를 풀었는가
- 어떤 설계 선택을 했는가
- 어디까지 검증했는가

반대로 처음부터 모든 class 이름과 endpoint를 말하면 듣는 사람이 구조를 잡기 어렵다.

## 핵심 문제는 좌석 정합성이다

면접에서 이 프로젝트를 소개할 때 가장 먼저 잡아야 할 축은 좌석 정합성이다.

예매 시스템은 단순 CRUD가 아니다.

한 좌석이 두 번 팔리면 안 되고, 대기열을 우회하면 안 되고, 결제와 만료가 동시에 와도 상태가 깨지면 안 된다. 취소/만료 이벤트가 사라져 좌석 반환이 누락되어도 안 된다.

그래서 설명의 시작점은 이렇게 잡는 것이 좋다.

```text
이 프로젝트는 예매 도메인에서 깨질 수 있는 정합성 지점을 먼저 나열하고,
각 지점을 DB lock, Redis token, idempotency, Outbox/DLT, reconciliation으로 나눠 검증했습니다.
```

이렇게 말하면 기술 스택이 문제를 해결하기 위한 선택으로 보인다.

## 락 전략은 비교의 결과로 설명한다

이 프로젝트에는 비관적 락, 낙관적 락, Redis 분산 락이 모두 남아 있다.

그 이유를 "여러 기술을 써보고 싶어서"처럼 말하면 약하다.

더 좋은 설명은 같은 API 계약에서 경합 패턴별 trade-off를 비교했다는 것이다.

| 전략 | 설명 포인트 |
| --- | --- |
| 비관적 락 | 결과가 직관적이고 높은 경합에서 안정적이지만 DB lock wait 비용이 있다 |
| 낙관적 락 | 낮은 경합에서 lock wait가 적지만 공유 counter row version 충돌이 크게 드러났다 |
| Redis 분산 락 | stock pre-check로 sold out 이후 요청을 DB 전에 차단하지만 Redis/DB reconciliation이 필요하다 |

특히 Scenario B에서 낙관적 락이 20/50으로 낮게 나온 이유를 설명할 수 있어야 한다.

각 사용자가 서로 다른 좌석을 잡아도 `ConcertSchedule.availableSeats`라는 공유 row를 함께 갱신한다. 낙관적 락은 이 row의 version 충돌을 commit 시점에 감지한다. 그래서 "서로 다른 좌석인데 왜 충돌하지?"라는 질문에 답할 수 있다.

## Redis는 빠른 도구지만 기준은 아니다

Redis를 쓴 부분은 세 가지다.

- 대기열 순서 관리
- userId + scheduleId 바인딩 token
- stock pre-check

면접에서 중요한 질문은 "왜 Redis를 썼나"보다 "Redis가 틀리면 어떻게 하나"일 수 있다.

안전한 답변은 이렇다.

```text
Redis는 빠른 입장 제어와 선검증 캐시로 사용했습니다.
하지만 장애, TTL, 중복 이벤트, 수동 reset 과정에서 DB와 어긋날 수 있으므로
최종 기준은 DB Seat.status로 두고 reconciliation utility를 별도로 만들었습니다.
```

이 답변은 Redis의 장점과 한계를 같이 말한다.

기술을 무조건 신뢰하는 것이 아니라, 실패했을 때 무엇을 기준으로 복구할지까지 생각했다는 점을 보여준다.

## 결제/만료 race와 idempotency를 함께 설명한다

결제와 만료는 서로 반대 방향의 상태 전이다.

결제가 이기면 예약은 `CONFIRMED`가 되어야 하고, 만료가 이기면 `EXPIRED`가 되어야 한다. 둘 다 성공하면 안 된다.

또 사용자는 같은 결제 요청을 다시 보낼 수 있다.

그래서 이 프로젝트에서는 상태 전이와 idempotency를 함께 봤다.

```text
Reservation row lock과 도메인 상태 전이 규칙으로
같은 reservation이 동시에 confirmed/expired가 되지 않게 했습니다.

Idempotency-Key와 DB unique constraint로
같은 요청은 replay하고, 같은 key의 다른 요청은 conflict로 분리했습니다.
```

여기서 "중복 요청을 그냥 막았다"라고만 말하면 부족하다.

같은 요청은 replay되어야 하고, 다른 요청은 conflict가 되어야 한다. 이 차이를 말할 수 있어야 한다.

## Outbox는 실패 경계를 나누는 장치다

Outbox를 설명할 때도 과장하지 않는 것이 중요하다.

Outbox는 DB transaction과 Kafka publish를 완전히 원자적으로 만들어주는 마법이 아니다. DB commit 이후 publish 실패로 이벤트가 사라지는 구간을 줄이는 장치다.

안전한 답변은 이렇다.

```text
비즈니스 transaction 안에 outbox event를 PENDING으로 저장하고,
relay scheduler가 Kafka로 발행합니다.
publish 실패는 FAILED와 nextAttemptAt으로 재시도하고,
retry 초과는 DEAD로 격리해 manual 판단 대상으로 분리했습니다.
```

그리고 consumer 실패는 DLT로 따로 본다고 이어가면 좋다.

```text
Outbox PUBLISHED는 Kafka publish 성공이지 consumer 성공은 아닙니다.
consumer 실패는 Kafka DLT와 manual replay utility로 분리했고,
같은 DLT 메시지를 replay해도 좌석 반환이 중복 증가하지 않는지 테스트했습니다.
```

이 설명은 Outbox, Kafka, DLT의 책임 경계를 보여준다.

## 검증은 숫자보다 경계가 중요하다

k6 결과를 말할 때는 조심해야 한다.

좋은 답변은 숫자를 말하되 범위를 제한한다.

```text
동일 좌석 100 concurrent requests에서 success 1, fail 99, overselling 0을 확인했습니다.
다만 이 결과는 로컬 Docker 단일 실행 기준이고, 운영 환경의 처리량이나 수용량 근거로 사용하지 않습니다.
```

Scenario D/E/F도 마찬가지다.

```text
결제/만료 race, idempotency replay/conflict, queue token abuse는
세 전략 x 3회 local repeat로 branch와 threshold를 확인했습니다.
운영 latency나 throughput 비교로 해석하지는 않았습니다.
```

이렇게 말하면 수치를 숨기지 않으면서도 과장하지 않는다.

## 한계를 먼저 말할 수 있어야 한다

`docs/LIMITATIONS.md`에 적어둔 한계는 면접에서도 그대로 도움이 된다.

현재 주장하지 않는 것은 다음과 같다.

- production 성능
- 운영형 SLO
- 실제 alert firing과 dashboard 운영
- Outbox 기반 단일 처리 보장
- Redis를 최종 기준으로 삼는 구조
- 외부 PG latency, 승인 실패, webhook까지 포함한 결제 시스템

한계를 말하는 것은 약점이 아니다.

오히려 프로젝트의 검증 범위를 알고 있다는 신호가 된다. 포트폴리오 프로젝트에서 가장 위험한 것은 하지 않은 일을 한 것처럼 말하는 것이다.

## 예상 질문에 대한 답변 포인트

면접에서 나올 수 있는 질문을 기준으로 답변 포인트를 정리하면 다음과 같다.

| 질문 | 답변 포인트 |
| --- | --- |
| 왜 Redis stock을 최종 기준으로 두지 않았나요? | Redis는 빠른 차단에 좋지만 DB seat 상태를 복구 기준으로 둬야 한다 |
| 낙관적 락이 왜 낮은 성공률을 보였나요? | 좌석은 달라도 `ConcertSchedule.availableSeats` 공유 row version 충돌이 있었다 |
| Outbox가 무엇을 해결하나요? | DB commit 이후 Kafka publish 실패로 이벤트가 사라지는 구간을 줄인다 |
| Outbox가 한 번만 처리를 보장하나요? | 아니다. 중복 가능성은 consumer idempotency와 상태 전이 조건으로 흡수한다 |
| 결제/만료 race는 어디서 막나요? | reservation row lock과 도메인 상태 전이 규칙으로 한 방향만 성공하게 한다 |
| queue token abuse는 어떻게 막았나요? | token을 userId + scheduleId에 바인딩하고 reservation transaction 전에 검증했다 |
| 관측성은 어디까지 했나요? | metric contract, synthetic alert rule test, local Prometheus scrape artifact까지 검증했다 |

이 표를 그대로 외우기보다는, 각 답변의 근거가 어느 테스트와 문서에 있는지 함께 기억하는 것이 좋다.

## 배운 점

프로젝트를 설명할 때 가장 중요한 것은 "무엇을 만들었다"가 아니라 "왜 그렇게 나눴는가"였다.

좌석 정합성, 대기열 우회 차단, idempotency, Outbox, Redis reconciliation, observability는 모두 따로 떨어진 기능이 아니다. 동시에 요청이 몰리는 예매 도메인에서 상태를 지키기 위한 경계들이다.

또 면접에서는 잘한 부분만큼 한계를 말하는 능력도 중요하다고 느꼈다.

검증하지 않은 운영 성능을 주장하지 않고, local Docker 단일 실행과 Testcontainers 통합 테스트의 범위를 구분하는 것이 프로젝트의 신뢰도를 높인다.

## 포트폴리오 메모

`concert-booking`은 고동시성 콘서트 예매 상황에서 좌석 overselling, 대기열 token 우회, 결제/만료 race, 중복 요청, 이벤트 발행 실패, Redis stock mismatch를 다룬 Spring Boot 백엔드 프로젝트다. PostgreSQL을 최종 정합성 기준으로 두고 Redis, Kafka, Outbox, DLT, reconciliation, Micrometer/Prometheus metric을 보조 경계로 나눴으며, Testcontainers 통합 테스트와 제한된 k6 로컬 시나리오로 각 실패 branch를 검증했다. 운영 성능, SLO, 실제 alerting, 외부 결제 연동은 아직 주장하지 않는 범위로 분리했다.
