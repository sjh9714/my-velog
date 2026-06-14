# [콘서트 예매 시스템] 대기열 토큰은 왜 예매 트랜잭션 앞에서 검증해야 할까

## 이 글의 위치

콘서트 예매 시스템 시리즈는 `정합성 문제 발견 -> 동시성 제어 -> 이벤트 유실 방지 -> 성능/운영 경계` 순서로 읽으면 흐름이 가장 자연스럽다.

1. 좌석은 왜 두 번 팔리면 안 되는가 - 이전 흐름
2. 같은 좌석을 100명이 동시에 잡으면 어떻게 될까 - 이전 흐름
3. 비관적 락, 낙관적 락, Redis 분산 락을 비교해보았다 - 이전 흐름
4. 대기열 토큰은 왜 예매 트랜잭션 앞에서 검증해야 할까 - 현재 글
5. 결제, 만료, 중복 요청이 동시에 오면 상태는 어떻게 지킬까 - 다음 흐름
6. Outbox와 Kafka로 이벤트 유실 구간 줄이기 - 다음 흐름
7. Redis stock은 왜 최종 기준 데이터가 아니어야 할까 - 다음 흐름
8. k6 성능 결과를 어디까지 주장할 수 있을까 - 다음 흐름
9. 운영자가 볼 수 있는 지표와 알림 만들기 - 다음 흐름
10. 면접에서 이 프로젝트를 어떻게 설명할까 - 다음 흐름

## 들어가며

예매 시스템에서 대기열은 단순히 사용자에게 순번을 보여주는 기능이 아니다.

대기열이 있어도 예매 API를 직접 호출해서 성공할 수 있다면, 대기열은 사실상 장식이 된다. 인기 공연에서는 이런 우회 경로가 치명적이다.

그래서 `concert-booking`에서는 예매 트랜잭션 앞에서 queue token을 검증한다.

사용자는 대기열에 진입하고, 입장 가능한 순서가 되면 token을 받는다. Reservation API는 이 token이 현재 사용자와 현재 공연 일정에 맞는지 확인한 뒤에만 좌석 예약을 진행한다.

이 글은 대기열 token을 왜 예매 트랜잭션 앞에서 검증해야 하는지, 그리고 어떤 abuse case를 막으려고 했는지 정리한 글이다.

Repository는 [sjh9714/concert-booking](https://github.com/sjh9714/concert-booking)이다.

## 대기열이 막아야 하는 것

대기열의 목적은 요청을 줄 세우는 것이다.

하지만 백엔드 입장에서는 더 구체적인 질문이 필요하다.

- token 없이 예매 API를 호출하면 어떻게 할 것인가
- 다른 사용자의 token을 가져오면 어떻게 할 것인가
- 다른 공연 일정의 token을 재사용하면 어떻게 할 것인가
- 만료된 token으로 예매하려고 하면 어떻게 할 것인가
- 좌석 경합 실패 후 token은 바로 소비해야 하는가

이 질문에 답하지 않으면 대기열은 쉽게 우회된다.

예매 화면에서는 버튼이 막혀 있어도, API를 직접 호출할 수 있다. 그래서 reservation transaction에 들어가기 전에 token을 검증해야 한다.

## Redis Sorted Set으로 순번을 만든 이유

대기열은 Redis Sorted Set을 사용했다.

사용자가 대기열에 들어오면 `userId + scheduleId` 기준으로 queue key를 만들고, 진입 시각을 score로 저장한다.

순번은 `ZRANK`로 계산할 수 있다.

```text
queue enter
→ Redis Sorted Set에 user 저장
→ rank 조회
→ 입장 가능하면 token issue
```

이 구조는 단순하다.

대기열의 최종 목적은 reservation transaction에 들어갈 수 있는 사용자를 제한하는 것이다. 그래서 복잡한 배치 처리보다, user와 schedule에 바인딩된 token을 발급하고 검증하는 흐름에 집중했다.

## token은 userId와 scheduleId에 묶는다

token은 단순 문자열이면 안 된다.

누구의 token인지, 어떤 공연 일정의 token인지가 함께 검증되어야 한다.

이 프로젝트에서는 token을 `userId + scheduleId`에 바인딩했다.

이렇게 하면 다음 우회 시도를 막을 수 있다.

- A 사용자의 token을 B 사용자가 사용한다.
- 1번 schedule의 token을 2번 schedule 예매에 사용한다.
- 이미 만료되었거나 Redis에 없는 token을 사용한다.

`QueueTokenInterceptor`와 `QueueService`는 이 흐름을 담당한다.

Reservation API는 token이 유효하지 않으면 좌석 예약 로직으로 넘어가지 않는다.

## 예매 성공 후에만 token을 소비한다

token 소비 시점도 중요했다.

처음에는 reservation API에 들어오면 token을 바로 소비하는 방식도 생각할 수 있다.

하지만 사용자가 token을 받고 좌석을 선택했는데, 그 좌석이 이미 다른 사용자에게 잡혀 실패할 수 있다. 이때 token을 이미 소비해버리면 사용자는 다른 좌석으로 재시도할 수 없다.

그래서 이 프로젝트에서는 예매 성공 후에만 token을 소비한다.

좌석 경합 실패는 예매 실패지만, 대기열을 통과한 권한 자체를 바로 잃어야 한다는 뜻은 아니다.

이 결정은 사용자 경험과 abuse 방어 사이의 균형이었다.

## 구현 흐름

핵심 흐름은 다음과 같다.

```text
POST /api/queue/enter
→ userId + scheduleId로 대기열 진입

POST /api/queue/token
→ 입장 순서 확인
→ token 발급
→ 대기열에서 제거

POST /api/reservations
→ queueToken body 전달
→ Idempotency-Key header 전달
→ Reservation Tx 앞에서 token 검증
→ 좌석 예약 성공 시 token 소비
```

여기서 token 검증은 reservation transaction의 입구 역할을 한다.

좌석 락 전략이 비관적이든, 낙관적이든, Redis 분산 락이든, 대기열을 통과하지 않은 요청은 예매 로직에 들어오면 안 된다.

## Scenario F: token abuse 검증

대기열 token 정책은 k6 Scenario F와 `QueueTokenPolicyIntegrationTest`로 검증했다.

Scenario F에서 다룬 abuse branch는 다음과 같다.

- token 없음
- 다른 사용자 token
- 다른 schedule token
- 만료 token
- 정상 token

`docs/PERF_RESULT.md`에는 targeted local run 결과가 이렇게 정리되어 있다.

| 항목 | 결과 |
| --- | ---: |
| checks | 16/16 passed |
| unauthorized_success_count | 0 |
| unauthorized_reject_count | 4 |
| unexpected_reject_status_count | 0 |
| normal_success_count | 1 |

formal local repeat에서는 세 전략 x 3회로 Scenario F를 반복했고, 144/144 checks passed를 기록했다.

다만 이 결과는 token abuse branch와 threshold 검증이다. 대기열 token abuse의 부하 성능이나 운영 latency를 주장하기 위한 수치가 아니다.

이 구분이 중요하다.

대기열 token 정책이 맞게 동작한다는 것과, production traffic에서 어느 정도 latency를 보장한다는 것은 다른 claim이다.

## Testcontainers에서 고정한 정책

`QueueTokenPolicyIntegrationTest`는 대기열 token 정책을 더 직접적으로 고정한다.

테스트가 지지하는 핵심 주장은 다음과 같다.

- token이 필수다.
- token은 `userId + scheduleId`에 바인딩된다.
- 성공 후 token이 소비된다.
- 좌석 경합 실패 시 token은 보존된다.

이 테스트가 있어야 token 소비 시점 같은 정책을 바꿀 때 위험을 줄일 수 있다.

예를 들어 실수로 reservation API 진입 직후 token을 소비하게 바꾸면, 좌석 경합 실패 후 재시도 정책이 깨질 수 있다.

## 대기열은 보안 기능이기도 하다

대기열을 UI 기능으로만 보면 순번 표시가 중심이 된다.

하지만 백엔드에서는 대기열이 access control에 가깝다.

예매 트랜잭션에 들어갈 자격이 있는 요청인지 검증하는 장치이기 때문이다.

그래서 token은 화면에서 버튼을 누른 흔적이 아니라, 서버가 검증 가능한 권한이어야 한다.

이 프로젝트에서 token을 `userId + scheduleId`에 묶고, reservation transaction 앞에서 검증한 이유도 여기에 있다.

## 배운 점

대기열은 "사람을 줄 세운다"보다 더 구체적으로 설계해야 했다.

누가, 어떤 공연 일정에 대해, 언제까지, 어떤 API를 호출할 수 있는지를 서버가 판단할 수 있어야 한다.

또 token 소비 시점도 도메인 정책이었다.

예매 실패의 이유가 좌석 경합이라면 token을 유지해서 다른 좌석을 시도하게 할 수 있다. 반대로 예매 성공 후에는 token을 소비해서 같은 입장 권한으로 반복 예매하지 못하게 해야 한다.

## 포트폴리오 메모

Redis Sorted Set 기반 대기열과 `userId + scheduleId` 바인딩 queue token을 구현했다. Reservation API는 예매 트랜잭션 앞에서 token을 검증하고, 예매 성공 후에만 token을 소비한다. `QueueTokenPolicyIntegrationTest`와 k6 Scenario F로 token 없음, 타 사용자, 타 schedule, 만료 token 우회가 성공하지 않는 것을 branch/threshold 검증했다.
