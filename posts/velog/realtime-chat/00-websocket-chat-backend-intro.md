# [실시간 채팅 백엔드] WebSocket 채팅 서버를 만들며 고민한 것들

## 한 줄 요약

실시간 채팅 백엔드는 WebSocket 연결 하나로 끝나지 않는다.
연결, 인증, 구독 권한, 메시지 발행, DB 저장, 수신자 전달, 읽음 처리, 장애 복구를 서로 다른 단계로 나누어 생각해야 한다.

## 이 글에서 다룰 문제

처음에는 실시간 채팅 서버라고 하면 WebSocket으로 메시지를 주고받는 기능을 가장 먼저 떠올렸다.

클라이언트가 서버에 연결하고, 메시지를 보내고, 서버가 그 메시지를 다른 사용자에게 뿌려주면 채팅 기능은 어느 정도 완성되는 줄 알았다.
하지만 직접 백엔드 흐름을 설계하다 보니 실제 문제는 그 다음부터 시작됐다.

- 로그인한 사용자가 아무 채팅방이나 구독할 수 있으면 안 된다.
- 메시지가 Kafka publish에는 성공했지만 DB 저장은 실패할 수 있다.
- ACK가 왔다고 해서 상대방이 메시지를 받은 것은 아니다.
- 여러 서버 인스턴스가 있을 때 같은 채팅방 메시지 순서를 어떻게 볼지 정해야 한다.
- Redis Pub/Sub fan-out을 놓친 클라이언트는 재연결 후 누락 메시지를 복구해야 한다.
- 실패한 메시지는 정상 흐름을 막지 않도록 격리하고, 필요하면 다시 처리할 수 있어야 한다.
- 한 사용자가 여러 기기로 접속했을 때 온라인 상태를 session 단위로 판단해야 한다.

이 프로젝트는 이런 문제들을 하나씩 분리해서 검증해본 Spring Boot 기반 실시간 채팅 백엔드다.

## 쉬운 비유

WebSocket 연결은 채팅방으로 이어진 전화선에 가깝다.

하지만 전화선이 연결됐다고 해서 모든 문제가 해결되지는 않는다.
누가 통화방에 들어올 수 있는지, 말한 내용이 어디에 기록되는지, 상대방에게 전달됐는지, 나중에 끊겼다가 다시 들어왔을 때 빠진 대화가 있는지까지 따로 관리해야 한다.

그래서 이 프로젝트에서는 WebSocket을 "실시간 통로"로 보고, 그 위에 필요한 규칙과 저장 경로를 분리했다.

## 프로젝트에서는 어떻게 구현했나

프로젝트의 전체 구성은 다음과 같다.

- Spring Boot
- WebSocket STOMP
- Kafka
- Redis Pub/Sub
- Redis Presence / Cache / Rate Limit
- PostgreSQL

핵심 흐름은 단순화하면 이렇게 볼 수 있다.

```text
Client
  -> WebSocket STOMP CONNECT
  -> JWT 인증
  -> SUBSCRIBE /topic/room.{roomId}
  -> room member 인가
  -> SEND /app/chat.send
  -> room member 재검증
  -> Kafka publish, key = roomId
  -> ACK or NACK
  -> Consumer DB 저장
  -> PERSISTED ACK
  -> room topic fan-out
  -> receiver 수신
  -> read receipt 처리
```

여기서 중요한 점은 각 단계가 같은 성공을 의미하지 않는다는 것이다.

예를 들어 Kafka publish ACK는 "Kafka broker가 publish 요청을 accepted 했다"는 뜻이지, 상대방이 메시지를 받았다는 뜻이 아니다.
DB 저장 완료는 `PERSISTED`로 따로 본다.
수신자가 메시지를 관측했는지, 사용자가 읽었는지도 또 다른 단계다.

## 흐름도

### 흐름도 쉽게 읽기

| 구간 | 쉽게 보면 |
| --- | --- |
| Client | 사용자가 메시지를 보내고, 채팅방을 구독하는 출발점 |
| Spring Boot | 인증, room 권한 확인, Kafka publish를 담당하는 입구 |
| Kafka | 메시지를 저장 경로와 fan-out 경로로 나누는 중간 허브 |
| PostgreSQL | 메시지, 읽음 상태, 재연결 복구의 기준 데이터 |
| Redis Pub/Sub | 여러 서버 인스턴스의 WebSocket 세션으로 빠르게 뿌리는 경로 |

핵심은 Redis가 빠른 전달 경로이고, PostgreSQL이 나중에 다시 확인할 수 있는 기준 데이터라는 점이다.
그래서 재연결 복구는 Redis Pub/Sub가 아니라 DB에 저장된 메시지를 기준으로 설명한다.

```text
                    +------------------+
                    |      Client      |
                    +------------------+
                              |
                              | STOMP CONNECT / SUBSCRIBE / SEND
                              v
                    +------------------+
                    |   Spring Boot    |
                    | Auth / Room Auth |
                    +------------------+
                              |
                              | Kafka publish, key = roomId
                              v
                    +------------------+
                    |      Kafka       |
                    |  chat.messages   |
                    +------------------+
                         |          |
                         |          |
             DB 저장 consumer     fan-out consumer
                         |          |
                         v          v
              +--------------+   +----------------+
              | PostgreSQL   |   | Redis Pub/Sub  |
              | message/read |   | room delivery  |
              +--------------+   +----------------+
                         |
                         | reconnect recovery truth
                         v
                 Reconnect Sync API
```

PostgreSQL은 메시지와 읽음 상태의 기준 데이터가 된다.
Redis Presence는 빠른 TTL 기반 임시 상태이고, Redis Pub/Sub는 fan-out 경로로 사용한다.
재연결 복구의 진실 소스는 Redis가 아니라 PostgreSQL로 둔다.

## 코드 또는 설정 일부

README에 정리한 메시지 전송 흐름은 다음과 같은 형태다.

```text
Client SEND /app/chat.send
  -> room member check
  -> KafkaTemplate.send(chat.messages, key = roomId, event)
  -> success callback: /user/queue/messages/ack
  -> failure callback: /user/queue/messages/error
  -> persistence consumer save success: /user/queue/messages/persisted
```

### 코드 쉽게 읽기

이 흐름은 "메시지를 받자마자 DB 저장 완료라고 말하지 않는다"는 뜻이다.

| 단계 | 클라이언트가 이해해야 할 의미 |
| --- | --- |
| `room member check` | 이 사용자가 이 방에 메시지를 보낼 수 있는지 확인 |
| `KafkaTemplate.send` | 메시지를 비동기 처리 흐름에 넣음 |
| `ack` | Kafka publish 요청이 accepted 됨 |
| `error` | Kafka publish 단계에서 실패함 |
| `persisted` | consumer가 DB 저장 완료 또는 기존 row를 확인함 |

이 구조에서 `/user/queue/messages/ack`와 `/user/queue/messages/persisted`를 분리한 이유는 클라이언트가 "어디까지 성공했는지"를 오해하지 않게 하기 위해서다.

## 이 설계가 해결한 문제

이 프로젝트에서 특히 신경 쓴 문제는 다음과 같다.

| 문제 | 대응 |
|---|---|
| 유효한 JWT 사용자가 다른 방을 구독할 수 있는가 | `SUBSCRIBE /topic/room.{roomId}`에서 room membership 검증 |
| Kafka publish 성공 여부를 클라이언트가 알 수 있는가 | `/user/queue/messages/ack`, `/user/queue/messages/error`로 ACK/NACK 전달 |
| DB 저장 완료와 publish 성공을 구분할 수 있는가 | `/user/queue/messages/persisted`로 PERSISTED ACK 분리 |
| 같은 room 메시지 순서를 어떻게 볼 것인가 | Kafka key를 `roomId`로 사용하고 room 단위 ordering 검증 |
| 재연결 중 누락된 메시지를 어떻게 복구할 것인가 | `lastReceivedMessageId` 이후 메시지를 조회하는 sync API |
| consumer 실패 메시지를 어떻게 다룰 것인가 | DLT 격리와 manual replay utility |
| 한 사용자의 여러 세션을 어떻게 presence로 볼 것인가 | `userId + sessionId` 단위 TTL presence |

이 표를 만들면서 가장 크게 느낀 점은, 채팅 백엔드는 "메시지 보내기" 기능이 아니라 여러 상태 경계를 관리하는 시스템이라는 점이었다.

## 한계와 개선점

이 프로젝트의 README에는 측정한 것과 아직 주장하지 않는 것을 분리해서 적었다.

예를 들어 로컬 receiver matrix repeat3에서 missing 0 / duplicate 0을 확인했지만, 이것을 곧바로 production 1,000-session benchmark라고 말하지 않는다.
WebSocket measurement 문서에서도 ACK latency, persisted latency, recipient receive latency를 한 차트에 섞지 않는다고 정리했다.

현재 기준으로 명확히 선을 그은 부분은 다음과 같다.

- local Docker Compose 또는 local 단일 앱 반복 실행 결과는 운영 성능 claim이 아니다.
- ACK는 상대방 수신 완료가 아니다.
- `RECEIVED`는 receiver runner가 room topic MESSAGE를 관측했다는 뜻이지 production delivery 보장이 아니다.
- Redis Pub/Sub와 Presence는 durable recovery store가 아니다.
- mixed traffic p95 latency, cache hit rate, production 1,000-session benchmark는 별도 측정이 필요하다.

이런 경계를 적어두는 것은 약점이 아니라 신뢰도를 높이는 장치라고 생각한다.
숫자를 크게 보이게 만드는 것보다, 그 숫자가 무엇을 의미하고 무엇을 의미하지 않는지 구분하는 것이 더 중요하기 때문이다.

## 앞으로 쓸 글

이 글은 전체 프로젝트 소개에 가깝다.
앞으로는 아래 주제들을 하나씩 분리해서 정리해보려고 한다.

1. WebSocket은 왜 필요할까?
2. STOMP는 WebSocket 위에서 어떤 역할을 할까?
3. 로그인한 사용자도 아무 채팅방이나 구독하면 안 되는 이유
4. ACK는 상대방이 읽었다는 뜻이 아닌 이유
5. 채팅 메시지를 바로 DB에 저장하지 않고 Kafka로 보낸 이유
6. Kafka를 쓰면 메시지 순서가 자동으로 보장되는지
7. 실패한 메시지를 버리지 않기 위한 DLT와 replay
8. 안 읽은 메시지 수가 생각보다 단순하지 않은 이유
9. 성능 수치를 주장할 때 조심해야 하는 것들

## 관련 링크

- GitHub Repository: [sjh9714/realtime-chat](https://github.com/sjh9714/realtime-chat)
- Architecture 문서: [docs/ARCHITECTURE.md](https://github.com/sjh9714/realtime-chat/blob/main/docs/ARCHITECTURE.md)
- WebSocket measurement 문서: [docs/WEBSOCKET_MEASUREMENT.md](https://github.com/sjh9714/realtime-chat/blob/main/docs/WEBSOCKET_MEASUREMENT.md)
- 다음 글: [[실시간 채팅 백엔드] WebSocket은 왜 필요할까?](https://velog.io/@sjh9714/실시간-채팅-백엔드-WebSocket은-왜-필요할까)

## 마무리

처음에는 WebSocket 연결만 성공하면 채팅 기능은 거의 끝난 줄 알았다.

하지만 실제로는 메시지를 보내는 것, Kafka에 publish되는 것, DB에 저장되는 것, 상대방에게 전달되는 것, 사용자가 읽는 것이 전부 다른 단계였다.
이 프로젝트는 그 단계들을 일부러 분리하고, 각 단계가 어디까지의 성공을 의미하는지 검증해본 기록이다.

다음 글에서는 먼저 WebSocket이 왜 필요한지, 그리고 WebSocket만으로는 왜 부족했는지 정리해보려고 한다.
