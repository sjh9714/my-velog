# [실시간 채팅 백엔드] STOMP는 WebSocket 위의 메시지 주소 체계다

## 한 줄 요약

WebSocket은 연결 통로를 열어주지만, 메시지를 어디로 보내고 어디를 구독할지는 정해주지 않는다.
`realtime-chat`에서는 STOMP destination을 사용해서 SEND, SUBSCRIBE, MESSAGE의 주소 체계를 분리했다.

## 이 글에서 다룰 문제

처음에는 WebSocket 연결만 열면 클라이언트와 서버가 알아서 메시지를 주고받을 수 있을 거라고 생각했다.

하지만 채팅 백엔드에서는 단순히 "메시지를 보낸다"보다 더 구체적인 질문이 필요했다.

- 사용자는 어떤 주소로 메시지를 보내야 할까?
- 채팅방 메시지는 어떤 주소로 구독해야 할까?
- ACK/NACK처럼 특정 사용자에게만 가야 하는 응답은 어디로 보내야 할까?
- presence heartbeat는 채팅 메시지와 같은 흐름으로 처리해도 될까?

WebSocket 자체는 이 질문에 답하지 않는다.
그래서 이 프로젝트에서는 WebSocket 위에 STOMP를 얹어서 메시지의 목적지를 명시했다.

## 쉬운 비유

WebSocket이 전화선을 연결하는 일이라면, STOMP destination은 내선 번호에 가깝다.

전화선이 연결되어 있어도 "어느 부서에 연결할지"를 정하지 않으면 대화가 섞인다.
채팅 메시지, ACK, 에러, presence가 모두 같은 통로를 지나더라도 각각 도착해야 할 주소는 달라야 한다.

그래서 STOMP에서는 `/app`, `/topic`, `/user/queue` 같은 주소를 사용한다.
주소를 분리하면 서버도 "이 메시지는 명령이고, 이 메시지는 방송이고, 이 메시지는 개인 응답"이라고 구분할 수 있다.

## 프로젝트에서는 어떻게 구현했나

`realtime-chat`의 핵심 destination은 다음처럼 나눌 수 있다.

| 목적 | Destination | 의미 |
| --- | --- | --- |
| 메시지 전송 | `/app/chat.send` | 클라이언트가 서버 애플리케이션으로 채팅 메시지를 보냄 |
| 채팅방 구독 | `/topic/room.{roomId}` | 특정 room의 메시지를 구독 |
| Kafka publish ACK | `/user/queue/messages/ack` | 발신자에게 publish accepted 결과 전달 |
| Kafka publish NACK | `/user/queue/messages/error` | 발신자에게 publish failed 결과 전달 |
| DB 저장 완료 | `/user/queue/messages/persisted` | 발신자에게 persisted 결과 전달 |
| presence heartbeat | `/app/presence.heartbeat` | 접속 상태 TTL 갱신 |

여기서 중요한 점은 `/topic/room.{roomId}`와 `/user/queue/...`의 성격이 다르다는 것이다.

`/topic/room.{roomId}`는 채팅방 멤버들이 함께 받는 room broadcast 주소다.
반면 `/user/queue/messages/ack`는 특정 사용자에게만 보내는 개인 응답 주소다.

ACK를 room topic으로 보내면 다른 사용자에게 발신자의 전송 상태가 노출될 수 있다.
반대로 채팅방 메시지를 user queue로만 보내면 여러 수신자에게 fan-out하기 어렵다.

## 흐름도

### 흐름도 쉽게 읽기

아래 흐름은 같은 WebSocket 연결 안에서도 메시지가 세 갈래로 나뉜다는 것을 보여준다.

| 갈래 | 의미 |
| --- | --- |
| `SEND /app/chat.send` | 클라이언트가 서버 애플리케이션에 메시지 처리를 요청 |
| `/user/queue/messages/ack` | 발신자 한 명에게 Kafka publish accepted 결과를 알려줌 |
| `/user/queue/messages/persisted` | 발신자 한 명에게 DB 저장 완료를 알려줌 |
| `/topic/room.{roomId}` | 채팅방 멤버들에게 실제 채팅 메시지를 방송 |

ACK나 persisted 알림은 개인 상태이므로 room topic에 뿌리지 않는다.
반대로 채팅방 메시지는 여러 멤버가 함께 받아야 하므로 room topic으로 fan-out한다.

```text
Client
  | STOMP CONNECT + JWT
  v
Spring WebSocket endpoint
  |
  | SEND /app/chat.send
  v
ChatMessageController
  |
  | Kafka publish accepted
  v
/user/queue/messages/ack

Kafka consumer
  |
  | DB persisted
  v
/user/queue/messages/persisted

Broadcast consumer
  |
  | room fan-out
  v
/topic/room.{roomId}
```

이 흐름에서 같은 WebSocket 연결을 쓰더라도 메시지의 의미는 destination으로 구분된다.

## 코드 또는 설정 일부

실제 구현을 단순화하면 아래처럼 볼 수 있다.

```text
SEND /app/chat.send
  -> room member check
  -> KafkaTemplate.send(chat.messages, key = roomId, event)
  -> /user/queue/messages/ack or /user/queue/messages/error
```

구독은 별도 흐름이다.

```text
SUBSCRIBE /topic/room.{roomId}
  -> destination에서 roomId 추출
  -> room member 검증
  -> 허용된 사용자만 room topic 구독
```

### 코드 쉽게 읽기

두 코드블록은 `SEND`와 `SUBSCRIBE`를 일부러 나눠서 보여준다.

| 동작 | 서버가 확인하는 것 |
| --- | --- |
| `SEND /app/chat.send` | 메시지를 보내는 사용자가 해당 room 멤버인지 확인 |
| `SUBSCRIBE /topic/room.{roomId}` | 메시지를 받으려는 사용자가 해당 room 멤버인지 확인 |

구독을 허용받았다고 해서 전송을 무조건 믿지는 않는다.
전송 시점에도 room member를 다시 확인해야 직접 frame을 보내는 우회 시도를 막을 수 있다.

즉 `SEND`와 `SUBSCRIBE`는 같은 WebSocket 연결 안에서 일어나지만, 서버가 처리하는 의미는 다르다.

## 이 설계가 해결한 문제

첫 번째로 메시지 종류를 분리할 수 있었다.
채팅방 메시지, 전송 결과, 저장 결과, 에러를 같은 payload로 섞지 않고 목적지별로 나눌 수 있다.

두 번째로 권한 검증 지점을 명확히 할 수 있었다.
`/topic/room.{roomId}` 구독 시 room member인지 검사하고, `/app/chat.send` 전송 시에도 다시 room member를 확인한다.

세 번째로 클라이언트 UI가 상태를 더 정확히 표현할 수 있다.
클라이언트는 `/user/queue/messages/ack`를 보고 "서버가 Kafka publish를 accepted 했다"고 표시하고, `/user/queue/messages/persisted`를 보고 "DB 저장까지 완료됐다"고 표시할 수 있다.

## 한계와 개선점

STOMP destination을 나눴다고 해서 모든 정책이 자동으로 안전해지는 것은 아니다.

destination별 권한 정책을 서버에서 계속 명확히 유지해야 한다.
예를 들어 `/topic/room.{roomId}`는 room member 검증이 필요하지만, presence topic이나 user queue는 다른 정책이 필요할 수 있다.

또한 STOMP ERROR payload를 표준화하면 클라이언트가 실패 이유를 더 일관되게 처리할 수 있다.
지금 구조에서는 인증 실패, 구독 권한 실패, rate limit 실패 같은 오류를 더 세밀한 error code로 나눌 여지가 있다.

## 관련 링크

- GitHub Repository: [sjh9714/realtime-chat](https://github.com/sjh9714/realtime-chat)
- Design 문서: [docs/DESIGN.md](https://github.com/sjh9714/realtime-chat/blob/main/docs/DESIGN.md)
- 이전 글: [[실시간 채팅 백엔드] WebSocket은 왜 필요할까?](https://velog.io/@sjh9714/실시간-채팅-백엔드-WebSocket은-왜-필요할까)
- 다음 글: [[실시간 채팅 백엔드] 로그인한 사용자도 아무 채팅방이나 구독하면 안 된다](https://velog.io/@sjh9714/실시간-채팅-백엔드-로그인한-사용자도-아무-채팅방이나-구독하면-안-된다)

## 마무리

WebSocket은 실시간 통신의 통로를 열어준다.
하지만 채팅 백엔드에서는 그 통로 위에 주소 체계가 필요했다.

STOMP destination을 사용하니 메시지 전송, room 구독, 개인 ACK/NACK, persisted 알림을 서로 다른 흐름으로 볼 수 있었다.

다음 글에서는 이 주소 체계 중에서도 가장 조심해야 하는 부분인 `CONNECT` 인증과 `SUBSCRIBE` 인가 분리를 정리한다.
