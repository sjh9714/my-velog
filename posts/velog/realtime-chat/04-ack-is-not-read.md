# [실시간 채팅 백엔드] ACK는 상대방이 읽었다는 뜻이 아니다

## 한 줄 요약

채팅 시스템에서 ACK는 "상대방이 읽었다"는 뜻이 아니다.
어떤 단계의 처리가 성공했는지 알려주는 신호일 뿐이고, publish, 저장, 수신, 읽음은 모두 다른 성공 단계다.

## 이 글에서 다룰 문제

처음에는 메시지를 보내고 ACK를 받으면 "전송 성공"이라고 생각했다.

그런데 채팅 백엔드 흐름을 나눠보면, 성공이라는 말이 생각보다 모호하다.

메시지를 보냈을 때 성공은 무엇일까?

1. 서버가 요청을 받았다.
2. Kafka publish가 성공했다.
3. DB에 저장됐다.
4. 상대방 클라이언트가 메시지를 받았다.
5. 상대방이 메시지를 읽었다.

이 다섯 가지는 모두 다른 상태다.
그런데 이 차이를 구분하지 않고 "ACK 받았으니 성공"이라고 쓰면 클라이언트와 서버가 서로 다른 의미로 성공을 이해하게 된다.

이 글에서는 `realtime-chat` 프로젝트에서 ACK/NACK/PERSISTED/RECEIVED/READ를 어떻게 나누어 봤는지 정리한다.

## 쉬운 비유

택배로 비유하면 조금 쉽다.

- 접수 완료: 택배사가 물건을 받았다.
- 물류센터 입고: 물건이 물류센터에 들어갔다.
- 배송 출발: 기사님에게 전달됐다.
- 배송 완료: 받는 사람이 받았다.
- 확인 완료: 받는 사람이 상자를 열어봤다.

이 모든 단계를 그냥 "배송 성공"이라고 부르면 정확하지 않다.
채팅 메시지도 비슷하다.

ACK는 그중 특정 단계의 성공을 말할 뿐이다.
ACK가 왔다고 해서 상대방이 메시지를 읽었다고 볼 수는 없다.

## 프로젝트에서는 어떻게 구현했나

`realtime-chat`에서는 메시지 전송 경로를 다음처럼 분리했다.

```text
Client SEND /app/chat.send
  -> room member check
  -> KafkaTemplate.send(chat.messages, key = roomId, event)
  -> success callback: /user/queue/messages/ack
  -> failure callback: /user/queue/messages/error
  -> persistence consumer save success: /user/queue/messages/persisted
```

여기서 핵심은 ACK와 PERSISTED를 분리한 것이다.

`/user/queue/messages/ack`는 Kafka publish 요청이 accepted 됐다는 의미다.
반면 `/user/queue/messages/persisted`는 consumer가 메시지를 DB에 저장했거나, 이미 저장된 idempotent row를 확인했다는 의미다.

둘은 같은 성공이 아니다.

## 흐름도

### 흐름도 쉽게 읽기

아래 흐름은 메시지가 여러 성공 단계를 지난다는 것을 보여준다.

| 단계 | 쉽게 말하면 | 아직 아닌 것 |
| --- | --- | --- |
| ACK | Kafka가 publish 요청을 받아들임 | DB 저장 완료 아님 |
| PERSISTED | DB 저장 완료 또는 기존 row 확인 | 상대방 수신 완료 아님 |
| RECEIVED | receiver runner가 MESSAGE를 관측 | 사용자가 읽음 아님 |
| READ | 사용자가 읽음 처리함 | publish 성공과 같은 의미 아님 |

따라서 ACK를 받았다는 말은 "상대방이 읽었다"가 아니라 "서버의 비동기 메시지 흐름에 들어갔다"에 가깝다.

```text
Client
  |
  | SEND /app/chat.send
  v
Spring Boot
  |
  | Kafka publish 요청
  v
Kafka broker
  |
  | accepted
  v
/user/queue/messages/ack
  |
  | consumer 처리
  v
PostgreSQL 저장
  |
  | persisted
  v
/user/queue/messages/persisted
  |
  | fan-out 경로
  v
/topic/room.{roomId}
  |
  | receiver client 관측
  v
RECEIVED
  |
  | read receipt
  v
READ
```

이 흐름에서 ACK, PERSISTED, RECEIVED, READ는 각각 다른 위치에 있다.

## 코드 또는 설정 일부

ACK payload는 대략 이런 형태다.

```json
{
  "clientMessageId": "9b75d8e9-5f73-4f6d-8f1a-3b1c0d7e8d10",
  "roomId": 1,
  "status": "ACCEPTED",
  "acceptedAt": "2026-05-11T10:15:30"
}
```

NACK payload는 Kafka publish 실패를 나타낸다.

```json
{
  "clientMessageId": "9b75d8e9-5f73-4f6d-8f1a-3b1c0d7e8d10",
  "roomId": 1,
  "status": "FAILED",
  "reason": "Kafka publish failed"
}
```

PERSISTED payload는 DB 저장 완료 또는 기존 저장 row 확인을 나타낸다.

```json
{
  "clientMessageId": "9b75d8e9-5f73-4f6d-8f1a-3b1c0d7e8d10",
  "messageKey": "3f430c7b-4ed9-4c52-8ef3-9503d19a65f1",
  "messageId": 100,
  "roomId": 1,
  "status": "PERSISTED",
  "persistedAt": "2026-05-11T10:15:31"
}
```

### 코드 쉽게 읽기

세 payload는 같은 메시지를 서로 다른 단계에서 설명한다.

| 필드 또는 상태 | 의미 |
| --- | --- |
| `clientMessageId` | 클라이언트 임시 메시지와 서버 응답을 연결하는 id |
| `ACCEPTED` | Kafka publish 요청이 accepted 됨 |
| `FAILED` | Kafka publish 단계에서 실패함 |
| `messageKey` | Kafka event identity, replay 중복 저장 방지에 사용 |
| `messageId` | DB에 저장된 뒤 생긴 실제 메시지 id |

UI에서 ACK만 보고 "전송 완료"라고 표시하면 과할 수 있다.
DB에 저장된 확정 메시지로 바꾸는 기준은 PERSISTED 쪽에 더 가깝다.

이때 `clientMessageId`는 클라이언트가 보낸 메시지와 서버 응답을 연결하기 위한 correlation id다.
같은 사용자가 같은 `clientMessageId`로 재시도했을 때 중복 저장되지 않도록 `(senderId, clientMessageId)` 기준 멱등성도 둔다.

`messageKey`는 Kafka event/message identity에 가깝다.
DLT replay나 Kafka-level duplication 상황에서 중복 저장을 방지하는 기준으로 사용할 수 있다.

## 상태 이름 정리

| 상태 | 의미 | 의미하지 않는 것 |
|---|---|---|
| ACK / ACCEPTED | Kafka broker가 publish 요청을 accepted | 상대방 수신 완료 아님 |
| NACK / FAILED | Kafka publish 실패 | DB 저장 성공 아님 |
| PERSISTED | DB 저장 완료 또는 기존 idempotent row 확인 | 상대방 읽음 아님 |
| RECEIVED | receiver runner가 room topic MESSAGE를 관측 | production delivery 보장 아님 |
| READ | 사용자가 읽음 처리 | Kafka publish 성공과 별개 |

이 표를 만들면서 가장 조심했던 건 "성공"이라는 단어를 뭉뚱그리지 않는 것이었다.

## 이 설계가 해결한 문제

ACK와 PERSISTED를 분리하면 클라이언트가 다음과 같은 상태를 더 정확히 표현할 수 있다.

- 메시지가 서버 경로에 들어갔는지
- Kafka publish가 실패했는지
- DB 저장까지 완료됐는지
- 재시도해야 하는지
- UI에서 임시 메시지를 확정 메시지로 바꿔도 되는지

예를 들어 클라이언트가 메시지를 보낸 직후에는 "전송 중" 상태로 둘 수 있다.
ACK를 받으면 "서버 처리 시작" 또는 "전송 요청 접수"처럼 볼 수 있고, PERSISTED를 받으면 DB 기준으로 확정된 메시지로 볼 수 있다.

반대로 ACK만 받고 PERSISTED를 받지 못했다면, 이 메시지는 아직 DB 저장 완료로 확정할 수 없다.

## 측정에서도 상태를 섞지 않기

이 구분은 성능 측정에서도 중요하다.

`realtime-chat`의 WebSocket measurement 문서에서는 ACK latency, persisted latency, recipient receive latency를 같은 차트에 섞지 않는다고 정리했다.

그 이유는 간단하다.
세 값은 서로 다른 경로를 측정하기 때문이다.

- ACK latency: Kafka publish accepted까지의 시간
- persisted latency: DB 저장 완료까지의 시간
- recipient receive latency: receiver client가 room topic MESSAGE를 파싱하기까지의 시간

이 세 값을 한 그래프에 넣고 "채팅 latency"라고 부르면 해석이 흐려진다.
측정값은 숫자보다 정의가 먼저다.

## 이 글의 검증 근거

이 글에서 말한 ACK/NACK 경계는 실제 컨트롤러 코드의 `Kafka publish 결과`를 기준으로 나뉜다. `sendMessage(event)`가 성공하면 `/user/queue/messages/ack`로 accepted 응답을 보내고, 실패하면 `/user/queue/messages/error`로 failed 응답을 보낸다.

```java
chatMessageProducer
    .sendMessage(event)
    .whenComplete(
        (result, ex) -> {
          if (ex != null) {
            messagingTemplate.convertAndSendToUser(
                userDestination,
                MESSAGE_ERROR_DESTINATION,
                MessagePublishErrorResponse.failed(
                    clientMessageId, request.getRoomId(), reason));
            return;
          }

          messagingTemplate.convertAndSendToUser(
              userDestination,
              MESSAGE_ACK_DESTINATION,
              MessagePublishAckResponse.accepted(clientMessageId, request.getRoomId()));
        });
```

검증은 `WebSocketAckIntegrationTest`, `WebSocketPersistedAckIntegrationTest`, `ChatMessageControllerTest`, 그리고 `docs/WEBSOCKET_MEASUREMENT.md`의 ACK/PERSISTED 측정 구분을 기준으로 확인했다.

여기서 중요한 점은 `accepted`가 상대방 수신이나 읽음을 뜻하지 않는다는 것이다. 이 코드는 Kafka publish 요청이 받아들여졌는지까지만 알려준다.

## 한계와 개선점

이 구현에서 ACK는 Kafka publish accepted를 의미한다.
즉, ACK는 Redis Pub/Sub broadcast 완료, 상대 클라이언트 수신 완료, 읽음 완료를 의미하지 않는다.

또한 RECEIVED는 로컬 receiver runner가 room topic MESSAGE를 관측한 기록이다.
이것을 production delivery guarantee로 확장해서 말하지 않는다.

운영 환경에서 더 엄밀하게 다루려면 다음 과제가 남는다.

- 수신자별 delivery receipt를 별도로 설계할지 결정
- 모바일/브라우저 background 상태에서 수신 확인을 어떻게 볼지 정의
- 장시간 연결과 네트워크 흔들림 상황의 send-to-receive latency 측정
- ACK, PERSISTED, RECEIVED, READ 각각의 모니터링 지표 분리

## 관련 링크

- GitHub Repository: [sjh9714/realtime-chat](https://github.com/sjh9714/realtime-chat)
- WebSocket measurement 문서: [docs/WEBSOCKET_MEASUREMENT.md](https://github.com/sjh9714/realtime-chat/blob/main/docs/WEBSOCKET_MEASUREMENT.md)
- 이전 글: [[실시간 채팅 백엔드] 로그인한 사용자도 아무 채팅방이나 구독하면 안 된다](https://velog.io/@sjh9714/실시간-채팅-백엔드-로그인한-사용자도-아무-채팅방이나-구독하면-안-된다)
- 다음 글: [[실시간 채팅 백엔드] 채팅 메시지를 바로 DB에 저장하지 않고 Kafka로 보낸 이유](https://velog.io/@sjh9714/실시간-채팅-백엔드-채팅-메시지를-바로-DB에-저장하지-않고-Kafka로-보낸-이유)

## 마무리

이번 글에서 가장 중요했던 문장은 이것이다.

```text
ACK는 상대방이 읽었다는 뜻이 아니다.
```

더 정확히 말하면, ACK는 현재 단계에서 어떤 처리가 성공했는지를 알려주는 신호다.
실시간 채팅 백엔드에서는 publish, 저장, 수신, 읽음을 같은 성공으로 묶지 않고 나누어야 한다.

이 구분을 해두면 클라이언트 UI도 더 정확해지고, 장애 상황에서도 어디에서 문제가 생겼는지 추적하기 쉬워진다.
