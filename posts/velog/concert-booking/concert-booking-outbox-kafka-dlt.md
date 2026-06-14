# [콘서트 예매 시스템] Outbox와 Kafka로 이벤트 유실 구간 줄이기

## 이 글의 위치

콘서트 예매 시스템 시리즈는 `정합성 문제 발견 -> 동시성 제어 -> 이벤트 유실 방지 -> 성능/운영 경계` 순서로 읽으면 흐름이 가장 자연스럽다.

1. 좌석은 왜 두 번 팔리면 안 되는가 - 이전 흐름
2. 같은 좌석을 100명이 동시에 잡으면 어떻게 될까 - 이전 흐름
3. 비관적 락, 낙관적 락, Redis 분산 락을 비교해보았다 - 이전 흐름
4. 대기열 토큰은 왜 예매 트랜잭션 앞에서 검증해야 할까 - 이전 흐름
5. 결제, 만료, 중복 요청이 동시에 오면 상태는 어떻게 지킬까 - 이전 흐름
6. Outbox와 Kafka로 이벤트 유실 구간 줄이기 - 현재 글
7. Redis stock은 왜 최종 기준 데이터가 아니어야 할까 - 다음 흐름
8. k6 성능 결과를 어디까지 주장할 수 있을까 - 다음 흐름
9. 운영자가 볼 수 있는 지표와 알림 만들기 - 다음 흐름
10. 면접에서 이 프로젝트를 어떻게 설명할까 - 다음 흐름

## 코드 또는 검증 근거

Outbox 글의 핵심은 DB 트랜잭션과 Kafka publish 사이의 유실 구간을 줄이는 것이다. relay는 저장된 OutboxEvent를 읽어 Kafka로 보내고, 성공하면 `PUBLISHED`, 실패하면 재시도 가능한 실패 상태 또는 `DEAD` 상태로 바꾼다.

```java
private boolean publishClaimedEvent(Long eventId) {
    OutboxEvent event = outboxEventRepository.findById(eventId).orElse(null);
    if (event == null
            || event.getStatus() == OutboxEventStatus.PUBLISHED
            || event.getStatus() == OutboxEventStatus.DEAD) {
        return false;
    }

    long startedAt = bookingMetrics.startOutboxPublish();
    try {
        Object payload = deserializePayload(event);
        kafkaTemplate.send(event.getTopic(), String.valueOf(event.getAggregateId()), payload)
                .get(sendTimeoutSeconds, TimeUnit.SECONDS);
        markPublished(eventId);
        bookingMetrics.recordOutboxPublished(startedAt);
        return true;
    } catch (Exception e) {
        OutboxEventStatus status = markFailed(eventId, rootMessage(e));
        if (status == OutboxEventStatus.DEAD) {
            bookingMetrics.recordOutboxDead(startedAt);
        } else {
            bookingMetrics.recordOutboxFailed(startedAt);
        }
        return false;
    }
}
```

이 코드는 exactly-once를 주장하기 위한 코드가 아니라, 실패한 이벤트를 관측하고 재처리할 수 있는 상태로 남기기 위한 코드다.

## 들어가며

예매 시스템에서 좌석을 잡고 결제까지 끝났다고 해서 모든 일이 끝나는 것은 아니다.

예약이 생성되고, 결제가 확정되고, 취소나 만료가 발생하면 다른 컴포넌트에도 그 사실을 알려야 한다. 예를 들어 예약이 취소되거나 만료되면 좌석을 다시 반환해야 한다. 이 작업을 모두 하나의 트랜잭션 안에서 동기 처리하면 흐름은 단순해 보이지만, 외부 메시징 시스템이 끼는 순간 실패 경계가 생긴다.

가장 조심한 구간은 DB commit 이후 Kafka publish가 실패하는 상황이었다.

```text
DB transaction commit 성공
→ Kafka publish 실패
→ 이벤트를 잃어버림
```

이 글은 `concert-booking`에서 Outbox와 Kafka, DLT, manual replay를 어떻게 나눠 이벤트 유실 구간을 줄였는지 정리한 글이다.

Repository는 [sjh9714/concert-booking](https://github.com/sjh9714/concert-booking)이다.

## 왜 바로 Kafka로 보내지 않았나

처음 생각하기 쉬운 구조는 비즈니스 로직 안에서 바로 Kafka로 이벤트를 보내는 것이다.

```text
reservation 상태 변경
→ kafkaTemplate.send(...)
```

하지만 이 구조는 DB와 Kafka 사이의 원자성을 보장하기 어렵다.

DB transaction이 rollback되었는데 Kafka event만 발행되면 실제로 존재하지 않는 예약 이벤트가 소비될 수 있다. 반대로 DB commit은 성공했는데 Kafka publish가 실패하면 도메인 상태는 바뀌었지만 후속 이벤트가 사라진다.

예매 도메인에서는 후자가 특히 위험하다.

예약 취소나 만료 이벤트가 사라지면 좌석 반환 흐름이 실행되지 않을 수 있다. 결제 확정 이벤트가 사라지면 downstream이 예약 확정 사실을 모를 수 있다.

그래서 이벤트를 바로 publish하지 않고, 먼저 DB transaction 안에 "발행해야 할 이벤트"를 기록했다.

## Outbox의 역할

Outbox는 비즈니스 transaction 안에 이벤트 발행 의도를 저장하는 테이블이다.

```text
business transaction
→ seat / reservation / payment 변경
→ INSERT outbox_events(status=PENDING)
→ commit
```

이렇게 하면 도메인 상태 변경과 이벤트 발행 의도는 같은 DB commit 경계 안에 묶인다.

이후 별도의 relay scheduler가 outbox table에서 발행 가능한 이벤트를 읽고 Kafka로 publish한다.

```text
outbox PENDING
→ relay scheduler
→ Kafka publish
→ success: PUBLISHED
→ failure: FAILED + nextAttemptAt
→ max retry exceeded: DEAD
```

중요한 점은 Outbox가 모든 문제를 없애는 장치가 아니라는 것이다.

Outbox는 DB commit 이후 Kafka publish 실패로 이벤트가 조용히 사라지는 구간을 줄이기 위한 장치다. 중복 발행 가능성은 남는다. 그래서 consumer는 같은 이벤트가 다시 와도 상태를 망가뜨리지 않도록 멱등적으로 처리해야 한다.

## Outbox 상태를 나눈 이유

Outbox event는 다음 상태를 가진다.

| 상태 | 의미 |
| --- | --- |
| `PENDING` | DB transaction 안에 이벤트 발행 의도만 기록된 상태 |
| `PUBLISHED` | Kafka publish가 성공한 상태 |
| `FAILED` | publish 실패 후 재시도 대기 상태 |
| `DEAD` | 재시도 횟수를 초과해 자동 relay 대상에서 제외된 상태 |

`FAILED`와 `DEAD`를 나눈 이유는 운영 판단 기준이 다르기 때문이다.

`FAILED`는 아직 자동 재시도의 대상이다. `nextAttemptAt`이 지나면 relay가 다시 publish를 시도할 수 있다.

반면 `DEAD`는 더 이상 자동으로 계속 밀어붙이지 않는다. 같은 이벤트를 무한히 재시도하면 장애를 더 크게 만들 수 있다. payload, aggregate 최신 상태, consumer idempotency 기준을 확인한 뒤 수동으로 replay할지 보류할지 판단해야 한다.

이 프로젝트에서는 `OutboxIntegrationTest`로 다음 흐름을 검증했다.

- reservation/payment 흐름에서 outbox event가 저장되는지
- Kafka publish 실패 시 `FAILED`로 남는지
- `nextAttemptAt` 이전의 `FAILED` event는 relay 대상이 아닌지
- `nextAttemptAt` 이후 다시 relay되는지
- retry count를 초과하면 `DEAD`가 되는지
- stale lock이 남은 `PENDING` event는 다시 claim 가능한지
- `DEAD` event는 stale lock이 있어도 relay되지 않는지

## Consumer 실패는 DLT로 본다

Outbox는 Kafka publish까지의 경계를 다룬다.

하지만 Kafka publish가 성공했다고 consumer 처리까지 성공했다는 뜻은 아니다.

```text
Outbox PUBLISHED
→ Kafka topic
→ Consumer 처리 실패
→ DLT
```

예를 들어 `reservation.cancelled` 이벤트가 publish되었지만 `SeatReleaseConsumer`가 처리 중 실패할 수 있다. 이때 Outbox 상태만 보면 이미 `PUBLISHED`다. 따라서 consumer 실패는 Kafka DLT와 consumer log, 도메인 상태를 함께 봐야 한다.

DLT topic은 Spring Kafka의 `DeadLetterPublishingRecoverer` 규칙을 따라 `원본토픽.DLT` 형태로 사용했다. 예를 들면 `reservation.cancelled.DLT`다.

## Manual replay로 제한했다

DLT 메시지를 다시 원본 topic으로 보내는 replay 경로도 만들었다.

```http
POST /api/admin/dlt/replay?topic=reservation.cancelled.DLT&limit=10
```

하지만 이 기능은 자동 복구 시스템이 아니다.

`ROLE_ADMIN` 권한으로 제한된 manual replay utility다. replay 전에 payload가 안전한지, 같은 이벤트가 이미 처리되었는지, aggregate 최신 상태가 replay 가능한지 확인해야 한다.

이 경계를 글과 문서에 명확히 남겨둔 이유는 포트폴리오 프로젝트에서 과장하기 쉬운 지점이기 때문이다.

DLT replay endpoint가 있다고 해서 운영 장애 자동 복구를 완성한 것은 아니다. 이 프로젝트에서 검증한 것은 "실패 메시지를 격리하고, 제한된 관리자 경로로 재처리할 수 있는 구조"다.

## DLT replay 검증

`KafkaDltReplayIntegrationTest`는 DLT와 replay 흐름을 검증한다.

테스트에서 확인한 핵심은 네 가지다.

- consumer 실패 메시지가 DLT로 이동한다.
- DLT record에 원본 topic, partition, offset, exception header가 남는다.
- replay 후 원본 topic으로 다시 발행된다.
- 같은 DLT 메시지를 다시 replay해도 좌석과 stock이 중복 복구되지 않는다.

마지막 항목이 특히 중요하다.

Replay는 기본적으로 중복 처리 가능성을 가진다. 같은 메시지가 다시 들어와도 좌석 반환이 두 번 일어나면 안 된다. 그래서 `SeatReleaseConsumer`는 `HELD` 좌석만 반환하고, 이미 반환되었거나 예약 확정된 좌석은 중복으로 증가시키지 않는 방식으로 처리한다.

## 구현 경계

관련 흐름은 대략 이렇게 나뉜다.

- `OutboxEvent`: 발행할 이벤트와 상태를 저장하는 도메인
- `OutboxRelayService`: 발행 가능한 outbox event를 Kafka로 publish
- `OutboxRelayScheduler`: 주기적으로 relay 실행
- `KafkaConfig`: DLT recoverer와 listener factory 설정
- `SeatReleaseConsumer`: 취소/만료 이벤트를 받아 좌석 반환
- `DltReplayService`: DLT 메시지를 제한적으로 원본 topic에 재발행
- `OutboxIntegrationTest`: Outbox 상태 전이와 retry/backoff 검증
- `KafkaDltReplayIntegrationTest`: DLT 이동과 replay 멱등성 검증

각 컴포넌트가 하나의 책임을 갖도록 나눈 것이 중요했다.

Outbox는 publish 의도를 보존하고, relay는 Kafka 전송을 담당하며, DLT는 consumer 실패를 격리한다. Replay는 운영자가 판단한 뒤 제한적으로 실행하는 수동 경로다.

## 배운 점

이벤트 기반 구조를 붙이면 "Kafka로 보내면 된다"보다 먼저 실패 경계를 나눠야 한다.

DB commit 전 실패, DB commit 후 publish 실패, publish 성공 후 consumer 실패는 서로 다른 문제다. 이 문제를 하나의 retry로 묶으면 오히려 원인을 보기 어려워진다.

Outbox와 DLT를 분리하니 어떤 실패를 어디서 봐야 하는지 더 명확해졌다. 대신 중복 발행과 replay 가능성을 인정해야 했다.

그래서 이 구조의 핵심은 "한 번만 처리된다"는 주장이 아니라, 실패가 사라지지 않도록 기록하고, 중복은 도메인 상태 전이와 consumer idempotency로 흡수하는 데 있었다.

## 포트폴리오 메모

DB transaction 안에 Outbox event를 저장해 DB commit 이후 Kafka publish 실패로 이벤트가 유실되는 구간을 줄였다. Outbox 상태를 `PENDING`, `PUBLISHED`, `FAILED`, `DEAD`로 나누고 retry/backoff와 manual 판단 경계를 분리했으며, Kafka DLT와 제한된 admin replay utility를 통해 consumer 실패 메시지를 격리하고 재처리할 수 있는 흐름을 Testcontainers 통합 테스트로 검증했다.
