# [콘서트 예매 시스템] Redis stock은 왜 최종 기준 데이터가 아니어야 할까

## 이 글의 위치

콘서트 예매 시스템 시리즈는 `정합성 문제 발견 -> 동시성 제어 -> 이벤트 유실 방지 -> 성능/운영 경계` 순서로 읽으면 흐름이 가장 자연스럽다.

1. 좌석은 왜 두 번 팔리면 안 되는가 - 이전 흐름
2. 같은 좌석을 100명이 동시에 잡으면 어떻게 될까 - 이전 흐름
3. 비관적 락, 낙관적 락, Redis 분산 락을 비교해보았다 - 이전 흐름
4. 대기열 토큰은 왜 예매 트랜잭션 앞에서 검증해야 할까 - 이전 흐름
5. 결제, 만료, 중복 요청이 동시에 오면 상태는 어떻게 지킬까 - 이전 흐름
6. Outbox와 Kafka로 이벤트 유실 구간 줄이기 - 이전 흐름
7. Redis stock은 왜 최종 기준 데이터가 아니어야 할까 - 현재 글
8. k6 성능 결과를 어디까지 주장할 수 있을까 - 다음 흐름
9. 운영자가 볼 수 있는 지표와 알림 만들기 - 다음 흐름
10. 면접에서 이 프로젝트를 어떻게 설명할까 - 다음 흐름

## 코드 또는 검증 근거

Redis stock은 빠른 선점 검사용으로 사용하지만, 최종 기준 데이터로 두지는 않았다. 선점 시에는 Redis 값을 먼저 감소시키고, 부족하면 즉시 복구한 뒤 품절 예외를 낸다.

```java
public StockLease tryAcquire(Long scheduleId, int seatCount) {
    if (seatCount <= 0) {
        throw new IllegalArgumentException("선점할 좌석 수는 1개 이상이어야 합니다.");
    }

    initialize(scheduleId, false);

    String stockKey = RedisKeyUtil.stockKey(scheduleId);
    StockLease lease = new StockLease(redisTemplate, stockKey, seatCount);
    Long remaining = redisTemplate.opsForValue().decrement(stockKey, seatCount);
    if (remaining == null || remaining < 0) {
        lease.restoreOnce();
        throw new SoldOutException("잔여 좌석이 부족합니다.");
    }
    return lease;
}
```

그리고 정합성 확인은 DB row lock을 잡고 좌석 상태와 Redis 값을 비교하는 reconciliation 흐름에서 수행한다. 이 때문에 글에서는 Redis를 “빠른 캐시/게이트”로 설명하고, 최종 기준은 DB라고 정리했다.

## 들어가며

예매 시스템에서 Redis를 쓰면 많은 문제를 빠르게 처리할 수 있다.

대기열 순서를 관리하기 좋고, 토큰을 짧은 TTL로 저장하기도 좋다. 좌석 수가 이미 소진되었는지 빠르게 확인하는 데도 유용하다.

하지만 Redis에 있는 stock 값을 최종 기준으로 삼으면 위험하다.

Redis는 빠르지만 보조 상태다. 네트워크 실패, consumer 중복 처리, 수동 fixture reset, 장애 복구 과정에서 DB와 어긋날 수 있다. 예매 도메인에서 최종 기준은 사용자가 실제로 예약할 수 있는 좌석 상태여야 한다.

이 글은 `concert-booking`에서 Redis stock을 어떻게 빠른 선검증 캐시로 사용하고, DB 기준 reconciliation으로 불일치를 다뤘는지 정리한 글이다.

Repository는 [sjh9714/concert-booking](https://github.com/sjh9714/concert-booking)이다.

## Redis stock을 둔 이유

Redis stock은 분산 락 전략에서 먼저 사용했다.

동일 공연 일정에 남은 좌석이 없는데 모든 요청을 DB transaction까지 들여보내면 비용이 커진다. 이미 sold out인 상황에서는 DB row lock을 잡기 전에 빠르게 실패시키는 편이 낫다.

흐름은 단순하다.

```text
reservation request
→ Redis stock DECR
→ stock < 0 이면 복원 후 SoldOut
→ stock ok 이면 Redisson MultiLock
→ DB에서 seat 상태 확인
→ reservation 생성
```

이 구조의 장점은 소진 이후 실패 요청을 DB 전에 차단할 수 있다는 점이다.

하지만 stock을 먼저 감소시키는 순간 복원해야 하는 실패 경로도 생긴다.

- Redis decrement 이후 좌석이 이미 사용 불가로 확인되는 경우
- lock 획득에 실패하는 경우
- DB transaction 중 예외가 나는 경우
- consumer가 좌석 반환 이벤트를 처리하다 실패하는 경우

그래서 Redis stock은 최종 기준이 될 수 없다.

## 최종 기준은 DB seat 상태

이 프로젝트에서 최종 기준은 DB의 `Seat.status = AVAILABLE` count다.

```text
DB Seat.status AVAILABLE count
→ ConcertSchedule.availableSeats 비교
→ Redis stock 비교
```

Redis stock은 빠른 차단을 위한 캐시이고, `ConcertSchedule.availableSeats`는 조회와 전략 비교를 위한 counter 성격을 가진다. 둘 다 실제 좌석 상태와 어긋날 수 있으므로 최종 판단은 DB seat 상태로 돌아와야 한다.

이 기준을 명확히 두면 복구 방향도 명확해진다.

Redis 값이 10이고 DB AVAILABLE 좌석이 8이라면 Redis를 믿고 DB를 10으로 맞추면 안 된다. DB seat 상태를 기준으로 Redis와 schedule counter를 맞춰야 한다.

## Reconciliation 흐름

Reconciliation은 불일치를 검산하고 필요할 때 수동으로 보정하는 흐름이다.

```text
DB Seat.status AVAILABLE count
→ StockReconciliationService
→ ConcertSchedule.availableSeats 비교
→ Redis stock 비교
→ dry-run mismatch report
→ repair=true 시 DB 기준으로 보정
```

endpoint는 두 가지 모드로 나뉜다.

```http
POST /api/admin/schedules/{scheduleId}/stock/reconcile?repair=false
POST /api/admin/schedules/{scheduleId}/stock/reconcile?repair=true
```

`repair=false`는 dry-run이다. DB 기준 available seat count, schedule counter, Redis stock을 비교하고 mismatch를 보고한다.

`repair=true`는 관리자 권한으로 실행하는 수동 보정이다. 이때도 기준은 Redis가 아니라 DB seat 상태다.

중요한 것은 이것을 자동 운영 복구로 주장하지 않는 것이다.

이 프로젝트에서 reconciliation은 장애 후 수동 검산/보정을 위한 utility다. 운영 환경에서 자동으로 모든 불일치를 고쳐주는 시스템이라고 보지 않는다.

## 초기화 정책도 중요했다

Redis stock은 언제 만들어지고 언제 덮어써지는지도 정해야 했다.

이 프로젝트에서는 다음 정책을 사용했다.

- 로컬 fixture 생성 시 DB `AVAILABLE` 좌석 수 기준으로 Redis stock을 초기화한다.
- `/api/admin/reset`과 load-test reset은 `overwrite=true`로 DB 기준 값을 쓴다.
- `/api/admin/schedules/{scheduleId}/stock/initialize?overwrite=false`는 기존 key가 있으면 보존한다.
- 분산 예매 진입 시 stock key가 없으면 DB 기준으로 lazy init한다.
- 좌석 조회 API는 stock을 만들거나 덮어쓰지 않는다.

조회 API가 stock을 바꾸지 않도록 한 것도 의도적인 선택이었다.

사용자가 좌석 목록을 보는 것만으로 Redis stock이 생성되거나 덮어써지면, 조회 요청이 상태를 바꾸는 부작용을 갖게 된다. stock은 예매/관리 흐름에서만 명시적으로 다루는 편이 안전하다.

## 실패 경로의 stock 복원

분산 락 전략에서는 Redis stock을 먼저 감소시킨다.

그래서 실패하면 정확히 한 번만 복원해야 한다.

```text
DECR stock
→ 이후 단계 실패
→ INCR stock once
```

이때 실패 경로마다 stock을 다시 올리다 보면 중복 복원 위험이 있다. 반대로 복원을 놓치면 Redis stock이 실제보다 작아진다.

이 프로젝트에서는 `RedisStockService.StockLease`처럼 lease 개념을 두고, 실패 시 복원과 성공 시 완료를 명확히 나누는 방식으로 처리했다.

`DistributedLockStockFailureIntegrationTest`는 다음 흐름을 확인한다.

- Redis stock key가 없으면 DB 기준으로 lazy init 후 예매한다.
- sold out 발생 시 Redis stock이 음수로 남지 않는다.
- Redis decrement 후 좌석 불가가 발견되면 stock을 복원한다.
- 이 실패들이 queue token 자체를 불필요하게 제거하지 않는다.

## Reconciliation 테스트

`StockReconciliationIntegrationTest`는 reconciliation 정책을 검증한다.

대표적으로 다음 케이스를 확인한다.

- stock 초기화는 DB AVAILABLE 좌석 수를 기준으로 생성한다.
- `overwrite=false`는 기존 Redis 값을 보존하고, `overwrite=true`는 DB 기준으로 덮어쓴다.
- dry-run은 Redis stock이 DB보다 크거나 작은 경우를 mismatch로 탐지한다.
- repair는 DB AVAILABLE 기준으로 schedule counter와 Redis stock을 보정한다.
- admin reset은 좌석 50개와 Redis stock 50을 복구한다.

이 테스트들이 중요한 이유는 Redis stock을 "빠른 값"으로 쓰면서도 "최종 판단"으로 승격하지 않도록 경계를 고정하기 때문이다.

## Runbook에서의 판단 기준

Runbook에서도 같은 기준을 사용한다.

Redis stock mismatch가 의심되면 먼저 dry-run reconciliation을 실행한다.

```http
POST /api/admin/schedules/{scheduleId}/stock/reconcile?repair=false
```

그 다음 mismatch 원인을 본다.

- 분산 락 실패 경로에서 복원이 누락되었는지
- consumer 실패로 좌석 반환이 누락되었는지
- 수동 fixture reset 과정에서 값이 어긋났는지

필요하면 `repair=true`로 보정하고, 다시 `repair=false`로 mismatch가 해소됐는지 확인한다.

여기서도 원칙은 같다.

Redis 값을 기준으로 DB를 고치지 않는다. DB seat 상태를 기준으로 Redis와 schedule counter를 맞춘다.

## 배운 점

Redis를 쓰는 순간 성능이 좋아 보이는 흐름을 만들 수 있다.

하지만 빠른 값은 틀릴 수 있다는 전제를 같이 가져야 한다. 특히 예매처럼 한 좌석이 두 번 팔리면 안 되는 도메인에서는 캐시와 기준 데이터를 분리해야 한다.

Redis stock을 쓰면서 배운 점은 "빠른 실패"와 "최종 정합성"이 같은 말이 아니라는 것이다.

Redis는 sold out 이후 요청을 DB 전에 차단하는 데 유용했다. 하지만 장애 후 무엇을 믿고 복구할지의 기준은 DB seat 상태로 남겨야 했다.

## 포트폴리오 메모

Redis stock을 분산 락 전략의 빠른 선검증 캐시로 사용해 sold out 이후 실패 요청이 DB transaction까지 진입하는 비용을 줄였다. 동시에 DB `Seat.status = AVAILABLE` count를 최종 기준으로 두고, `StockReconciliationService`와 admin reconciliation endpoint로 Redis stock 및 schedule counter mismatch를 dry-run/repair 방식으로 검산했다. `StockReconciliationIntegrationTest`와 `DistributedLockStockFailureIntegrationTest`로 초기화, lazy init, 실패 복원, DB 기준 보정 흐름을 검증했다.
