# [실시간 채팅 백엔드] 채팅 메시지를 바로 DB에 저장하지 않고 Kafka로 보낸 이유

## 한 줄 요약

`realtime-chat`에서는 클라이언트의 메시지를 컨트롤러에서 바로 DB에 저장하지 않고 Kafka에 publish한다.
이렇게 해서 메시지 접수, 저장, fan-out, 실패 복구의 경계를 분리했다.

## 이 글에서 다룰 문제

처음에는 채팅 메시지를 받으면 바로 DB에 저장하고, 저장이 끝나면 WebSocket으로 브로드캐스트하면 된다고 생각했다.

작은 채팅 서비스라면 이 방식도 충분히 자연스럽다.
하지만 다중 인스턴스와 장애 상황을 생각하면 몇 가지 질문이 생긴다.

- DB 저장이 느려지면 WebSocket 요청 처리도 같이 느려질까?
- 메시지 저장과 수신자 fan-out을 같은 트랜잭션처럼 묶어도 될까?
- Kafka publish는 성공했지만 DB 저장은 실패할 수 있지 않을까?
- 실패한 메시지는 어디에 격리하고 어떻게 다시 처리할까?
- 클라이언트는 어느 단계까지 성공했는지 어떻게 알까?

이 프로젝트에서는 이 질문들을 한 번에 숨기지 않고 단계별 상태로 나누었다.

## 쉬운 비유

주문 시스템으로 비유하면, 주문 접수와 조리 완료는 다른 단계다.

사용자가 주문 버튼을 눌렀을 때 매장이 "주문을 접수했다"고 말할 수 있다.
하지만 그 말이 음식이 완성됐거나 배달이 끝났다는 뜻은 아니다.

채팅 메시지도 비슷하다.
Kafka publish accepted는 메시지가 비동기 처리 흐름에 들어갔다는 뜻이고, DB persisted는 저장이 끝났다는 뜻이다.
상대방 수신이나 읽음은 또 다른 단계다.

## 프로젝트에서는 어떻게 구현했나

`/app/chat.send`는 메시지를 직접 DB에 저장하지 않는다.
먼저 room member를 확인하고, Kafka `chat.messages` topic에 `roomId`를 key로 publish한다.

성공하면 발신자의 `/user/queue/messages/ack`로 ACCEPTED를 보내고, 실패하면 `/user/queue/messages/error`로 FAILED를 보낸다.
이후 persistence consumer가 메시지를 DB에 저장하면 `/user/queue/messages/persisted`로 PERSISTED를 보낸다.

```text
Client SEND /app/chat.send
  -> room member check
  -> KafkaTemplate.send(chat.messages, key = roomId, event)
  -> success callback: /user/queue/messages/ack
  -> failure callback: /user/queue/messages/error
  -> persistence consumer save success: /user/queue/messages/persisted
```

이 구조에서는 컨트롤러가 "DB 저장까지 완료"를 바로 말하지 않는다.
컨트롤러가 말할 수 있는 것은 Kafka publish accepted 또는 failed다.

## 흐름도

### 흐름도 쉽게 읽기

이 흐름은 메시지를 "요청 처리", "저장", "전달"로 나눈 구조다.

| 구간 | 쉽게 보면 |
| --- | --- |
| Spring App -> Kafka | 메시지를 바로 DB에 꽂지 않고 비동기 처리 줄에 넣음 |
| persistence consumer | Kafka에서 메시지를 읽어 PostgreSQL에 저장 |
| broadcast consumer | Kafka에서 메시지를 읽어 Redis Pub/Sub로 fan-out |
| PERSISTED ACK | 저장 경로가 끝났다는 발신자용 알림 |
| `/topic/room.{roomId}` | 채팅방 멤버에게 실제 메시지를 전달하는 경로 |

저장과 전달을 한 덩어리로 묶지 않기 때문에, 어느 경로가 느리거나 실패했는지 따로 볼 수 있다.

```text
Client
  |
  | SEND /app/chat.send
  v
Spring App
  |
  | publish key = roomId
  v
Kafka chat.messages
  |                         |
  | persistence consumer    | broadcast consumer
  v                         v
PostgreSQL              Redis Pub/Sub
  |                         |
  v                         v
PERSISTED ACK           /topic/room.{roomId}
```

저장 consumer와 broadcast consumer는 같은 topic을 독립적으로 소비한다.
그래서 저장 경로와 fan-out 경로의 실패와 지연을 분리해서 관찰할 수 있다.

## 코드 또는 설정 일부

ACK/NACK/PERSISTED payload의 의미를 단순화하면 다음과 같다.

```json
{
  "clientMessageId": "client-generated-id",
  "roomId": 1,
  "status": "ACCEPTED"
}
```

```json
{
  "clientMessageId": "client-generated-id",
  "messageKey": "event-identity",
  "messageId": 100,
  "roomId": 1,
  "status": "PERSISTED"
}
```

### 코드 쉽게 읽기

두 JSON은 "접수됨"과 "저장됨"을 나눠서 보여준다.

| payload | 쉽게 말하면 |
| --- | --- |
| `ACCEPTED` | Kafka publish까지 성공해서 메시지가 처리 흐름에 들어감 |
| `PERSISTED` | consumer가 DB 저장까지 끝냈거나 이미 저장된 row를 확인함 |
| `clientMessageId` | 클라이언트 재시도와 응답 매칭을 위한 값 |
| `messageKey` | Kafka event 단위 중복을 막기 위한 값 |

이 둘을 분리하면 클라이언트는 "요청은 들어갔지만 아직 저장 확정은 아님" 같은 중간 상태를 표현할 수 있다.

`clientMessageId`는 클라이언트 재시도와 ACK/NACK correlation에 사용한다.
`messageKey`는 Kafka event identity에 가깝고, DLT replay나 Kafka-level duplication 상황에서 중복 저장 방지 기준으로 사용한다.

## 이 설계가 해결한 문제

첫 번째로 단계별 성공 의미가 분리된다.
ACK는 Kafka publish accepted이고, PERSISTED는 DB 저장 완료 또는 기존 idempotent row 확인이다.
두 상태를 하나로 묶지 않기 때문에 클라이언트와 서버가 같은 의미로 성공을 이해할 수 있다.

두 번째로 장애 격리 지점이 생긴다.
consumer 처리 중 실패가 발생하면 DLT로 격리하고, 원인을 제거한 뒤 replay할 수 있다.

세 번째로 다중 인스턴스 fan-out을 더 자연스럽게 다룰 수 있다.
Kafka와 Redis Pub/Sub를 통해 한 app instance에서 받은 메시지를 다른 app instance의 WebSocket session에도 전달할 수 있다.

## 한계와 개선점

Kafka를 넣었다고 해서 메시지 전달이 자동으로 완벽해지는 것은 아니다.

ACK는 publish accepted만 의미한다.
DB 저장, Redis Pub/Sub broadcast, 상대방 클라이언트 수신, 읽음 완료는 모두 별도 상태다.

또한 비동기 구조는 관찰 지표가 더 중요해진다.
Kafka publish 실패, consumer 실패, DLT 적재, persisted ACK 지연을 따로 볼 수 있어야 한다.

운영 환경에서는 replay 권한, 감사 로그, replay 결과 추적도 필요하다.
이 프로젝트는 DLT 격리와 manual replay utility를 테스트로 검증했지만, 완성된 운영 도구를 제공한다고 말하지는 않는다.

## 관련 링크

- GitHub Repository: [sjh9714/realtime-chat](https://github.com/sjh9714/realtime-chat)
- Design 문서: [docs/DESIGN.md](https://github.com/sjh9714/realtime-chat/blob/main/docs/DESIGN.md)
- 이전 글: [[실시간 채팅 백엔드] ACK는 상대방이 읽었다는 뜻이 아니다](https://velog.io/@sjh9714/실시간-채팅-백엔드-ACK는-상대방이-읽었다는-뜻이-아니다)
- 다음 글: [[실시간 채팅 백엔드] Kafka를 쓰면 메시지 순서가 자동으로 보장될까?](https://velog.io/@sjh9714/실시간-채팅-백엔드-Kafka를-쓰면-메시지-순서가-자동으로-보장될까)

## 마무리

바로 DB에 저장하는 구조는 단순하고 직관적이다.
하지만 실시간 채팅 백엔드에서 메시지는 저장, 전달, 복구, 측정이라는 여러 경계를 지난다.

Kafka를 먼저 통과시키면서 이 경계를 명시적으로 나눌 수 있었다.
중요한 것은 Kafka를 썼다는 사실보다, Kafka publish accepted와 DB persisted를 같은 성공으로 말하지 않는 것이다.

다음 글에서는 Kafka를 사용할 때 가장 자주 오해하는 메시지 순서 보장 범위를 정리한다.
