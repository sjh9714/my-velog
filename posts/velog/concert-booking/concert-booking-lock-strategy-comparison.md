# [콘서트 예매 시스템] 비관적 락, 낙관적 락, Redis 분산 락을 비교해보았다

## 이 글의 위치

콘서트 예매 시스템 시리즈는 `정합성 문제 발견 -> 동시성 제어 -> 이벤트 유실 방지 -> 성능/운영 경계` 순서로 읽으면 흐름이 가장 자연스럽다.

1. 좌석은 왜 두 번 팔리면 안 되는가 - 이전 흐름
2. 같은 좌석을 100명이 동시에 잡으면 어떻게 될까 - 이전 흐름
3. 비관적 락, 낙관적 락, Redis 분산 락을 비교해보았다 - 현재 글
4. 대기열 토큰은 왜 예매 트랜잭션 앞에서 검증해야 할까 - 다음 흐름
5. 결제, 만료, 중복 요청이 동시에 오면 상태는 어떻게 지킬까 - 다음 흐름
6. Outbox와 Kafka로 이벤트 유실 구간 줄이기 - 다음 흐름
7. Redis stock은 왜 최종 기준 데이터가 아니어야 할까 - 다음 흐름
8. k6 성능 결과를 어디까지 주장할 수 있을까 - 다음 흐름
9. 운영자가 볼 수 있는 지표와 알림 만들기 - 다음 흐름
10. 면접에서 이 프로젝트를 어떻게 설명할까 - 다음 흐름

## 코드 또는 검증 근거

락 비교 글의 핵심은 “전략을 바꿔도 같은 예매 유스케이스를 검증한다”는 점이다. 프로젝트에서는 예매 전략을 인터페이스로 분리하고, 설정값으로 비관적 락, 낙관적 락, Redis 분산 락 구현을 선택할 수 있게 했다.

```java
public interface SeatReservationStrategy {
    ReservationCreationMode creationMode();

    ReservationResponse execute(
            ReservationCommand command,
            Supplier<ReservationResponse> reservationOperation);
}
```

```java
@Bean
@Primary
public ReservationService reservationService(
        @Value("${reservation.strategy:pessimistic}") String strategy,
        PessimisticLockReservationService pessimistic,
        OptimisticLockReservationService optimistic,
        DistributedLockReservationService distributed) {
    ReservationService selected = switch (strategy) {
        case "optimistic" -> optimistic;
        case "distributed" -> distributed;
        default -> pessimistic;
    };
    log.info("예매 전략 선택: {} → {}", strategy, selected.getClass().getSimpleName());
    return selected;
}
```

그래서 글에서 비교한 것은 “락 이름” 자체가 아니라 같은 예매 흐름에서 경합 조건을 만났을 때 각 전략이 어떤 실패/성공 패턴을 보였는지다.

## 들어가며

같은 좌석을 동시에 예매하면 한 명만 성공해야 한다.

이 규칙을 지키는 방법은 하나가 아니다. DB row를 잠글 수도 있고, version 충돌을 감지할 수도 있고, Redis lock과 stock을 앞단에 둘 수도 있다.

`concert-booking`에서는 세 가지 전략을 같은 예매 API 계약 아래에서 비교했다.

- 비관적 락
- 낙관적 락
- Redis 분산 락

이 글은 세 전략을 "무엇이 더 좋다"로 단순 비교하기보다, 어떤 상황에서 어떤 비용이 드러났는지 정리한 글이다.

Repository는 [sjh9714/concert-booking](https://github.com/sjh9714/concert-booking)이다.

## 먼저 비교 기준을 정했다

락 전략을 비교할 때 숫자만 보면 위험하다.

어떤 전략이 p95가 낮게 나왔다고 해서 항상 좋은 전략이라고 말할 수는 없다. 반대로 어떤 전략의 성공률이 낮게 나왔다고 해서 그 전략이 항상 나쁘다고 말할 수도 없다.

그래서 비교 기준을 먼저 나눴다.

- 동일 좌석 경합에서 overselling이 없는가
- 서로 다른 좌석을 동시에 예매할 때 성공률은 어떤가
- 좌석이 소진된 이후 실패 요청을 얼마나 빨리 거절하는가
- Redis와 DB 상태가 어긋날 때 보정 경로가 있는가
- retry 정책이 사용자 경험과 DB 부하에 어떤 영향을 주는가

이 기준이 있어야 수치를 해석할 수 있다.

## 비관적 락: 먼저 잠그고 순서대로 처리하기

비관적 락은 이름 그대로 "동시에 건드릴 가능성이 높다"고 보고 먼저 잠그는 방식이다.

예매 도메인에서는 같은 좌석 row를 DB에서 잠그고, 그 row를 수정하는 요청을 순서대로 처리한다.

비유하면 화장실 문을 잠그는 방식에 가깝다. 누군가 사용 중이면 다른 사람은 기다려야 한다.

장점은 결과가 직관적이라는 점이다.

동일 좌석 경합처럼 충돌이 매우 높은 상황에서는 "하나씩 처리한다"는 설명이 명확하다. 같은 좌석에 몰린 요청은 DB row lock을 기준으로 직렬화된다.

하지만 비용도 있다.

lock wait가 생기고, 기다리는 동안 DB connection을 점유할 수 있다. hot row가 많아지면 latency가 증가할 수 있다.

이 프로젝트에서는 동일 좌석 경합과 분산 좌석 예약에서 비관적 락이 모두 정합성을 지켰다. 특히 50명/50좌석 분산 예약에서도 50/50 성공을 확인했다.

## 낙관적 락: 일단 시도하고 충돌을 감지하기

낙관적 락은 "충돌이 자주 나지 않을 것"이라고 보고 먼저 진행한 뒤, 저장 시점에 version 충돌을 확인하는 방식이다.

JPA에서는 `@Version`을 통해 이 패턴을 구현할 수 있다.

낮은 충돌 상황에서는 lock wait를 줄일 수 있다. 읽기가 많고 쓰기 충돌이 적은 도메인에서는 좋은 선택이 될 수 있다.

하지만 이 프로젝트에서는 흥미로운 결과가 나왔다.

Scenario B에서 각 사용자는 서로 다른 좌석을 예매했다. 표면적으로는 좌석 row 충돌이 없어 보인다. 그런데 낙관적 락은 50건 중 20건만 성공했다.

이유는 `ConcertSchedule.availableSeats`라는 공유 counter row였다.

각 사용자가 서로 다른 좌석을 잡아도, 모든 예매는 같은 공연 일정의 남은 좌석 수를 감소시킨다. 그 shared row에 `@Version`이 걸려 있으면 commit 시점에 version 충돌이 발생할 수 있다.

즉 충돌 단위가 좌석이 아니라 schedule counter로 넓어진 것이다.

이 결과는 낙관적 락이 항상 부적합하다는 뜻이 아니다. 다만 공유 counter row가 있는 모델에서는 충돌 비용이 예상보다 쉽게 드러날 수 있다는 뜻이다.

## Redis 분산 락: DB 앞에서 빠르게 거절하기

Redis 분산 락 전략은 Redis lock과 stock pre-check를 함께 사용한다.

핵심은 좌석이 이미 소진된 뒤에도 반복해서 들어오는 실패 요청을 DB transaction 전에 빠르게 차단하는 것이다.

Mixed Load처럼 70%는 조회, 30%는 예매이고 예매가 인기 좌석 상위 20%에 몰리는 상황에서는, 좌석이 금방 소진된다. 소진 이후에도 쓰기 요청은 계속 들어온다.

이때 매번 DB transaction까지 들어가서 실패를 확인하면 비용이 커질 수 있다.

Redis stock pre-check를 두면 이미 소진된 요청을 앞단에서 빠르게 실패시킬 수 있다.

하지만 Redis를 사용하면 반드시 따라오는 질문이 있다.

Redis 값이 DB와 어긋나면 무엇을 기준으로 복구할 것인가?

이 프로젝트에서는 Redis stock을 최종 기준 데이터로 보지 않았다. 최종 기준은 DB의 `Seat.status = AVAILABLE` count다. Redis stock은 빠른 보조 상태이고, 불일치 가능성은 reconciliation utility로 다룬다.

Redis 분산 락은 편하지만, Redis가 진실이라고 말하는 순간 위험해질 수 있다.

## Scenario A: 동일 좌석 경합

먼저 동일 좌석 경합이다.

조건은 100 VU, 동일 좌석 1개, 각 VU 예매 요청 1회다.

| 메트릭 | 비관적 락 | 낙관적 락 | Redis 분산 락 |
| --- | ---: | ---: | ---: |
| 성공 수 | 1 | 1 | 1 |
| 실패 수 | 99 | 99 | 99 |
| overselling | 0건 | 0건 | 0건 |

세 전략 모두 같은 좌석 1개에 대해 하나의 성공만 허용했다.

이 시나리오의 핵심은 성능 비교가 아니라 정합성이다. 어떤 전략이든 overselling 0을 만족해야 다음 비교로 넘어갈 수 있다.

## Scenario B: 분산 좌석 예약

다음은 50 VU, 50개 좌석, 각 VU가 서로 다른 좌석 1개를 예매하는 시나리오다.

| 메트릭 | 비관적 락 | 낙관적 락 | Redis 분산 락 |
| --- | ---: | ---: | ---: |
| 성공률 | 100% (50/50) | 40% (20/50) | 100% (50/50) |
| p50 | 64ms | 200ms | 90ms |
| p90 | 91ms | 215ms | 120ms |
| p95 | 95ms | 215ms | 126ms |

처음에는 낙관적 락도 서로 다른 좌석이면 잘 될 것이라고 생각하기 쉽다.

하지만 실제로는 `ConcertSchedule.availableSeats` 공유 row version conflict가 성공률을 낮췄다. 이 결과 덕분에 "락 대상이 무엇인가"를 더 조심해서 봐야 한다는 점을 확인했다.

## Scenario C: 혼합 부하

혼합 부하에서는 200 VU, 45초 동안 70% 좌석 조회와 30% 예매 요청을 섞었다. 예매는 80% 확률로 인기 좌석 상위 20%에 집중된다.

| 메트릭 | 비관적 락 | 낙관적 락 | Redis 분산 락 |
| --- | ---: | ---: | ---: |
| 총 RPS | 969 | 993 | 1,005 |
| 쓰기 p95 | 37ms | 10ms | 6ms |
| 쓰기 성공 | 50 | 50 | 50 |
| 쓰기 실패 | 20,766 | 21,711 | 21,638 |

쓰기 성공은 좌석 수만큼 50건이다. 쓰기 실패는 이미 선점되었거나 예매된 좌석을 다시 시도한 요청이다.

여기서 Redis 분산 락의 쓰기 p95가 낮게 나온 것은, 소진 이후 실패 요청을 Redis stock pre-check로 DB 전에 차단한 영향으로 해석했다.

다만 이 수치 역시 로컬 Docker 단일 실행 기준이다. 운영 성능 claim으로 확장하지 않았다.

## 전략별 선택 기준

정리하면 선택 기준은 이렇게 볼 수 있다.

| 상황 | 우선 고려 전략 | 이유 |
| --- | --- | --- |
| 동일 좌석 경합이 높음 | 비관적 락 | 같은 좌석 row를 DB에서 직렬화해 결과가 직관적이다. |
| 충돌이 낮고 공유 counter row가 없음 | 낙관적 락 | lock wait를 줄일 수 있다. |
| 소진 이후 실패 요청이 많음 | Redis 분산 락 | DB transaction 전에 빠르게 실패시킬 수 있다. |
| Redis stock과 DB가 어긋날 수 있음 | DB 기준 reconciliation | Redis는 최종 기준 데이터가 아니다. |

어떤 전략이 항상 정답인 것은 아니다.

도메인의 경합 단위가 좌석인지, schedule counter인지, 실패 요청을 DB 전에 차단해야 하는지에 따라 선택이 달라진다.

## 배운 점

락 전략을 비교하면서 가장 크게 배운 것은 "충돌 단위"를 정확히 봐야 한다는 점이었다.

좌석이 서로 다르면 충돌이 없을 것처럼 보일 수 있다. 하지만 같은 schedule counter를 함께 갱신한다면 그 row가 새로운 병목이 된다.

또 하나는 Redis를 사용할 때 최종 기준 데이터를 분리해야 한다는 점이다.

Redis는 빠른 선검증에 좋지만, 좌석 정합성의 최종 근거는 DB에 두는 편이 안전했다.

## 포트폴리오 메모

비관적 락, 낙관적 락, Redis 분산 락을 같은 reservation API 계약에서 비교했다. 동일 좌석 100 VU에서는 세 전략 모두 overselling 0을 확인했고, 50명/50좌석 분산 예매에서는 낙관적 락이 `ConcertSchedule.availableSeats` 공유 row version conflict로 20/50 성공에 그치는 현상을 분석했다. Redis stock은 빠른 선검증용 캐시로 사용하되 최종 기준은 DB로 유지했다.
