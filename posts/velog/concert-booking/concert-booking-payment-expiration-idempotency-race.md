# [콘서트 예매 시스템] 결제, 만료, 중복 요청이 동시에 오면 상태는 어떻게 지킬까

## 이 글의 위치

콘서트 예매 시스템 시리즈는 `정합성 문제 발견 -> 동시성 제어 -> 이벤트 유실 방지 -> 성능/운영 경계` 순서로 읽으면 흐름이 가장 자연스럽다.

1. 좌석은 왜 두 번 팔리면 안 되는가 - 이전 흐름
2. 같은 좌석을 100명이 동시에 잡으면 어떻게 될까 - 이전 흐름
3. 비관적 락, 낙관적 락, Redis 분산 락을 비교해보았다 - 이전 흐름
4. 대기열 토큰은 왜 예매 트랜잭션 앞에서 검증해야 할까 - 이전 흐름
5. 결제, 만료, 중복 요청이 동시에 오면 상태는 어떻게 지킬까 - 현재 글
6. Outbox와 Kafka로 이벤트 유실 구간 줄이기 - 다음 흐름
7. Redis stock은 왜 최종 기준 데이터가 아니어야 할까 - 다음 흐름
8. k6 성능 결과를 어디까지 주장할 수 있을까 - 다음 흐름
9. 운영자가 볼 수 있는 지표와 알림 만들기 - 다음 흐름
10. 면접에서 이 프로젝트를 어떻게 설명할까 - 다음 흐름

## 들어가며

좌석을 잡는 것만으로 예매가 끝나지는 않는다.

사용자가 좌석을 선택하면 예약은 잠시 `PENDING` 상태가 된다. 사용자가 결제하면 `CONFIRMED`가 되고, 제한 시간이 지나면 scheduler가 `EXPIRED`로 바꿀 수 있다.

문제는 결제와 만료가 순서대로만 실행되지 않는다는 점이다.

사용자가 결제 버튼을 누르는 순간, 만료 scheduler도 같은 예약을 만료 처리하려고 할 수 있다. 네트워크 timeout 때문에 사용자는 같은 결제 요청을 다시 보낼 수도 있다. 브라우저 더블클릭으로 같은 예약 요청이 두 번 들어올 수도 있다.

이 글은 `concert-booking`에서 예약 상태 전이와 idempotency를 어떻게 분리해서 다뤘는지 정리한 글이다.

Repository는 [sjh9714/concert-booking](https://github.com/sjh9714/concert-booking)이다.

## 예약 상태를 먼저 정했다

예약 상태는 크게 네 가지로 나눴다.

```text
PENDING
CONFIRMED
CANCELLED
EXPIRED
```

`PENDING`은 좌석을 임시로 잡은 상태다.

결제가 성공하면 `CONFIRMED`가 된다. 사용자가 취소하면 `CANCELLED`가 될 수 있고, 제한 시간이 지나면 `EXPIRED`가 된다.

중요한 것은 상태 전이가 마음대로 일어나면 안 된다는 점이다.

예를 들어 이미 `CONFIRMED`된 예약이 만료되어서는 안 된다. 만료 시간이 지나지 않은 `PENDING` 예약이 `EXPIRED`가 되어도 안 된다. 하나의 예약이 confirmed이면서 expired인 것처럼 해석되어도 안 된다.

그래서 상태 전이 규칙은 도메인 메서드와 테스트로 고정했다.

대표적으로 `ReservationStatePolicyTest`는 confirmed reservation이 cancel/expire될 수 없는지, pending reservation이 expiresAt 이전에 expire될 수 없는지 확인한다.

## 결제와 만료 race

가장 조심해야 한 흐름은 결제와 만료가 동시에 실행되는 상황이었다.

```text
T1: 사용자가 결제 요청
T2: 만료 scheduler가 같은 reservation 만료 처리
```

둘 다 같은 reservation을 바꾸려고 한다.

이때 하나의 요청만 상태 전이에 성공해야 한다. 결제가 이겼다면 reservation은 `CONFIRMED`가 되고 payment는 하나만 생성되어야 한다. 만료가 이겼다면 reservation은 `EXPIRED`가 되고 결제는 성공하면 안 된다.

이를 위해 payment API와 expiration scheduler는 reservation row lock과 상태 전이 규칙을 사용한다.

단순히 현재 상태를 읽고 if문으로 확인하는 것만으로는 부족하다. 동시에 실행될 수 있으므로 같은 reservation row를 기준으로 전이를 보호해야 한다.

## Scenario D: race branch 검증

결제/만료 race는 `ReservationStateTransitionRaceIntegrationTest`와 k6 Scenario D로 검증했다.

`docs/PERF_RESULT.md`의 targeted local run에는 다음 결과가 정리되어 있다.

| 항목 | 결과 |
| --- | ---: |
| checks | 24/24 passed |
| expected_race_loser | 10 |
| unexpected_race_response | 0 |
| payment_success | 1 |
| expire_success | 9 |
| confirmedReservationCount | 1 |
| expiredReservationCount | 9 |
| paymentCount | 1 |
| duplicatePaymentCount | 0 |

여기서 중요한 것은 모든 race에서 하나의 방향만 이겨야 한다는 점이다.

다만 이 수치는 운영 latency나 throughput claim으로 사용하지 않는다. race branch와 aggregate final summary를 확인하기 위한 로컬 시나리오 검증이다.

per-reservation 상태 전이 불변식은 `ReservationStateTransitionRaceIntegrationTest`의 검증 범위로 분리했다.

## 중복 요청은 실패가 아니라 replay일 수 있다

다음 문제는 중복 요청이다.

사용자는 같은 요청을 여러 번 보낼 수 있다.

- 버튼을 두 번 클릭한다.
- 네트워크 timeout 이후 같은 요청을 재시도한다.
- 클라이언트가 응답을 받지 못해 같은 요청을 다시 보낸다.

이때 서버는 같은 요청과 다른 요청을 구분해야 한다.

같은 `Idempotency-Key`로 같은 예약 요청이 다시 들어오면 같은 결과를 replay할 수 있어야 한다. 하지만 같은 key로 다른 좌석을 예약하려고 하면 conflict로 봐야 한다.

이 차이를 구분하지 않으면 문제가 생긴다.

같은 요청을 매번 새 예약으로 처리하면 중복 row가 생긴다. 반대로 다른 요청까지 같은 replay로 처리하면 사용자가 의도하지 않은 좌석을 예약한 것처럼 보일 수 있다.

## Idempotency-Key의 역할

이 프로젝트에서는 reservation과 payment 모두 `Idempotency-Key`를 사용했다.

reservation에서는 같은 사용자, 같은 schedule, 같은 key, 같은 요청이면 replay로 처리한다. 같은 key로 다른 좌석을 요청하면 conflict로 처리한다.

payment에서도 같은 결제 요청이 반복되어도 결제가 두 번 생성되지 않아야 한다.

이를 위해 idempotency key를 별도 엔티티로 관리하고, DB unique constraint로 중복 생성을 막는다.

idempotency는 단순히 "중복 요청을 무시한다"가 아니었다.

같은 요청은 안전하게 replay하고, 다른 요청은 명확히 conflict로 거절하는 정책이었다.

## Scenario E: replay와 conflict 검증

중복 요청은 `ReservationIdempotencyIntegrationTest`, `PaymentIdempotencyIntegrationTest`, k6 Scenario E로 검증했다.

targeted local run 결과는 다음과 같다.

| 항목 | 결과 |
| --- | ---: |
| checks | 26/26 passed |
| duplicate_reservation_response | 20 |
| duplicate_payment_response | 20 |
| idempotency_conflict_count | 1 |
| request_fail | 0 |
| reservationCount | 1 |
| paymentCount | 1 |
| duplicateSeatReservationCount | 0 |
| duplicatePaymentCount | 0 |

formal local repeat에서는 세 전략 x 3회로 Scenario E를 반복했고, 234/234 checks passed를 기록했다.

이 결과에서 핵심은 duplicate row가 생기지 않았다는 점이다.

다만 여기서도 claim을 제한했다. k6 evidence는 모든 replay 응답 body가 byte-identical하다는 주장까지 하지는 않는다. same-key replay branch와 최종 중복 row 부재를 확인하는 근거로 사용했다.

## 상태 전이와 idempotency는 함께 봐야 한다

결제/만료 race와 idempotency는 따로 떨어진 문제가 아니다.

결제 요청이 중복으로 들어오는 동시에 예약이 만료될 수도 있다. 같은 key로 다시 들어온 결제 요청이 이미 성공한 결제의 replay인지, 이미 만료된 예약에 대한 잘못된 결제인지 판단해야 한다.

그래서 상태 전이 규칙과 idempotency 정책을 함께 봐야 한다.

상태 전이는 reservation의 현재 상태를 보호하고, idempotency는 같은 요청이 반복될 때 같은 결과를 안정적으로 다룬다.

둘 중 하나만 있으면 부족하다.

상태 전이만 있으면 timeout retry가 중복 row를 만들 수 있다. idempotency만 있으면 이미 confirmed된 예약을 expire하는 잘못된 전이를 막지 못할 수 있다.

## 구현 경계

이 프로젝트에서 관련 흐름은 대략 이렇게 나뉜다.

- `PaymentService`: 결제 요청과 결제 idempotency 처리
- `ReservationExpirationScheduler`: 만료된 reservation 처리
- `Reservation`: 상태 전이 도메인 규칙
- `ReservationIdempotencyService`: reservation idempotency 정책
- `ReservationStateTransitionRaceIntegrationTest`: 결제/만료 race 검증
- `ReservationIdempotencyIntegrationTest`: reservation replay/conflict 검증
- `PaymentIdempotencyIntegrationTest`: 중복 결제 방어 검증

각 컴포넌트가 모든 책임을 갖지 않도록 나눈 것이 중요했다.

도메인 상태 전이, API idempotency, scheduler race를 분리해야 테스트도 선명해진다.

## 배운 점

예매 시스템에서 "중복 요청"은 예외적인 일이 아니었다.

사용자는 버튼을 두 번 누를 수 있고, 네트워크는 끊길 수 있고, 클라이언트는 재시도할 수 있다. 그래서 서버는 같은 요청이 반복되는 상황을 정상 흐름으로 다뤄야 한다.

또 결제와 만료처럼 서로 반대 방향의 상태 전이는 동시에 실행될 수 있다는 전제를 가져야 했다.

상태 전이를 순서대로만 생각하면 race를 놓치기 쉽다.

## 포트폴리오 메모

예약 상태를 `PENDING`, `CONFIRMED`, `CANCELLED`, `EXPIRED`로 나누고, reservation row lock과 도메인 상태 전이 규칙으로 결제/만료 race를 보호했다. `Idempotency-Key`와 DB unique constraint로 reservation/payment 중복 요청을 replay/conflict로 분리했으며, k6 Scenario D/E와 Testcontainers 통합 테스트로 중복 row와 duplicate payment가 생기지 않는 것을 검증했다.
