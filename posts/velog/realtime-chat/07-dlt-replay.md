# [실시간 채팅 백엔드] 실패한 메시지를 버리지 않기 위한 DLT와 replay 설계

## 한 줄 요약

Kafka consumer에서 실패한 메시지를 정상 흐름에 계속 묶어두면 전체 처리가 막힐 수 있다.
`realtime-chat`에서는 실패 메시지를 DLT로 격리하고, 원인 제거 후 manual replay할 수 있는 경계를 검증했다.

## 이 글에서 다룰 문제

실시간 채팅에서 메시지 하나가 실패했다고 해서 이후 모든 메시지가 멈추면 안 된다.
반대로 실패한 메시지를 조용히 버려도 안 된다.

처음에는 consumer에서 예외가 나면 retry하면 된다고 생각했다.
하지만 retry만으로 해결되지 않는 상황이 있다.

- 특정 payload가 계속 실패하면 consumer가 같은 메시지에서 막힐 수 있다.
- DB 장애나 schema mismatch처럼 원인을 먼저 고쳐야 하는 실패가 있을 수 있다.
- 실패 메시지를 나중에 다시 처리하려면 원본 event identity가 필요하다.
- replay가 중복 저장을 만들면 안 된다.

그래서 실패 메시지를 분리해서 보관하고, 다시 처리할 수 있는 경계가 필요했다.

## 쉬운 비유

택배 분류 중 주소가 잘못된 물건이 하나 있다고 해보자.

그 물건 때문에 전체 컨베이어 벨트를 멈춰두면 다른 정상 택배도 모두 늦어진다.
그렇다고 문제 있는 물건을 버릴 수도 없다.

현실에서는 문제 있는 물건을 별도 구역으로 빼두고, 주소를 확인한 뒤 다시 분류 라인에 올린다.
DLT와 replay도 비슷하다.

## 프로젝트에서는 어떻게 구현했나

`realtime-chat`의 Kafka consumer는 처리 실패가 반복되면 메시지를 DLT로 보낸다.
채팅 메시지 DLT는 `chat.messages.dlt`로 분리된다.

`DltReplayService`는 DLT에 격리된 `ChatMessageEvent`를 원래 topic인 `chat.messages`로 다시 발행하는 내부 utility다.
자동 복구가 아니라 원인을 제거한 뒤 수동으로 호출하는 도구에 가깝다.

핵심은 replay가 중복 저장을 만들지 않게 하는 것이다.
이 프로젝트에서는 `messageKey`를 event identity로 보고, consumer가 이미 저장한 `messageKey`인지 확인한다.

## 흐름도

### 흐름도 쉽게 읽기

이 흐름도는 실패 메시지를 정상 처리 줄에서 빼내는 과정을 보여준다.

| 단계 | 쉽게 보면 |
| --- | --- |
| `Kafka chat.messages` | 정상 메시지가 들어오는 기본 topic |
| `Persistence consumer` | 메시지를 DB에 저장하려고 처리하는 consumer |
| `Retry` | 일시적 실패일 수 있으니 몇 번 더 시도 |
| `chat.messages.dlt` | 계속 실패한 메시지를 따로 격리하는 topic |
| `manual replay` | 원인을 고친 뒤 사람이 다시 원래 topic으로 넣는 작업 |

정상 메시지는 계속 흐르고, 실패 메시지만 별도 topic에 보관된다.
그래서 장애를 숨기지 않으면서도 전체 consumer 흐름이 한 메시지에 계속 묶이지 않게 한다.

```text
Kafka chat.messages
  |
  v
Persistence consumer
  |
  | processing failed
  v
Retry
  |
  | retry exhausted
  v
chat.messages.dlt
  |
  | manual replay after fixing cause
  v
Kafka chat.messages
  |
  v
Persistence consumer
```

정상 메시지는 계속 흐르고, 실패 메시지는 별도 topic에 격리된다.

## 코드 또는 설정 일부

replay 동작을 단순화하면 아래처럼 볼 수 있다.

```text
read record from chat.messages.dlt
  -> restore ChatMessageEvent
  -> choose replay key
     - original DLT record key if exists
     - otherwise event.roomId
  -> publish to chat.messages
```

### 코드 쉽게 읽기

replay는 "DLT에 있던 메시지를 다시 원래 줄에 올리는 작업"이다.

| 줄 | 의미 |
| --- | --- |
| `read record from chat.messages.dlt` | 실패해서 격리된 메시지를 읽음 |
| `restore ChatMessageEvent` | 원래 채팅 메시지 이벤트 형태로 복원 |
| `original DLT record key` | 가능하면 기존 Kafka key를 유지해 같은 partition 흐름으로 보냄 |
| `otherwise event.roomId` | key가 없으면 room 단위 순서를 위해 roomId를 key로 사용 |
| `publish to chat.messages` | 다시 정상 consumer가 처리할 수 있게 원래 topic으로 발행 |

여기서 replay key를 아무 값으로 고르면 같은 room 메시지가 다른 partition으로 갈 수 있다.
그래서 원래 key를 우선 사용하고, 없으면 `roomId`를 fallback으로 둔다.

중복 저장 방지는 두 기준을 나눠서 본다.

| 기준 | 목적 |
| --- | --- |
| `(senderId, clientMessageId)` | 같은 사용자의 클라이언트 재시도 중복 방지 |
| `messageKey` | Kafka event identity, DLT replay 중복 저장 방지 |

이 둘을 섞지 않는 것이 중요하다.
클라이언트 재시도와 Kafka replay는 비슷해 보이지만 서로 다른 중복 시나리오다.

## 이 설계가 해결한 문제

첫 번째로 consumer 실패가 정상 메시지 흐름을 계속 막는 상황을 줄일 수 있다.
실패 메시지는 DLT로 격리되고, 다른 메시지는 계속 처리될 수 있다.

두 번째로 실패 메시지를 잃어버리지 않는다.
원인을 분석하고 고친 뒤 다시 처리할 수 있는 대상이 남아 있다.

세 번째로 replay 중복 저장을 검증할 수 있다.
`messageKey` 기준으로 이미 처리한 이벤트인지 확인하기 때문에 같은 DLT record를 다시 replay해도 DB에 중복 row가 생기지 않아야 한다.

## 한계와 개선점

DLT가 있다고 해서 운영 복구가 완성되는 것은 아니다.

이 프로젝트의 replay는 내부 manual utility다.
운영 환경에서는 다음이 더 필요하다.

- replay 권한 제어
- 누가 언제 어떤 메시지를 replay했는지에 대한 감사 로그
- replay 대상 필터링
- replay 결과 추적
- DLT lag와 replay 성공/실패에 대한 알림

또한 Redis Pub/Sub broadcast 실패의 DLT 적재 end-to-end 검증은 별도 개선 범위다.
현재는 publish 실패 재전파와 no-ack 동작을 테스트로 검증한 수준으로 설명하는 것이 안전하다.

## 관련 링크

- GitHub Repository: [sjh9714/realtime-chat](https://github.com/sjh9714/realtime-chat)
- Runbook 문서: [docs/RUNBOOK.md](https://github.com/sjh9714/realtime-chat/blob/main/docs/RUNBOOK.md)
- 이전 글: [[실시간 채팅 백엔드] Kafka를 쓰면 메시지 순서가 자동으로 보장될까?](https://velog.io/@sjh9714/실시간-채팅-백엔드-Kafka를-쓰면-메시지-순서가-자동으로-보장될까)
- 다음 글: [[실시간 채팅 백엔드] 안 읽은 메시지 수는 생각보다 단순하지 않다](https://velog.io/@sjh9714/실시간-채팅-백엔드-안-읽은-메시지-수는-생각보다-단순하지-않다)

## 마무리

장애 복구에서 중요한 것은 실패를 숨기지 않는 것이다.
실패한 메시지를 정상 흐름에서 분리하고, 원인을 고친 뒤 다시 처리할 수 있어야 한다.

이 프로젝트에서는 DLT와 manual replay utility로 그 경계를 검증했다.
다만 운영 도구까지 완성했다고 말하기보다는, 어떤 실패를 격리하고 어떤 기준으로 중복을 막았는지 설명하는 것이 더 정확하다.

다음 글에서는 채팅 서비스에서 은근히 까다로운 안 읽은 메시지 수 정합성을 정리한다.
