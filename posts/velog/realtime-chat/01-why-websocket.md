# [실시간 채팅 백엔드] WebSocket은 왜 필요할까?

## 한 줄 요약

HTTP polling은 클라이언트가 계속 묻는 방식이고, WebSocket은 연결을 유지한 뒤 서버가 먼저 말할 수 있는 방식이다.

하지만 WebSocket은 실시간 통신의 통로일 뿐이다.
실제 채팅 백엔드에서는 그 통로 위에서 어떤 메시지를 어디로 보낼지 정하는 규칙이 따로 필요했다.

## 이 글에서 다룰 문제

처음에는 채팅을 만들려면 WebSocket을 쓰면 된다고 생각했다.

맞는 말이긴 하다.
채팅처럼 서버에서 새 이벤트가 생겼을 때 클라이언트가 바로 받아야 하는 기능에는 WebSocket이 잘 어울린다.

하지만 조금 더 생각해보면 이런 질문이 남는다.

- HTTP 요청만으로는 왜 불편할까?
- WebSocket은 정확히 어떤 문제를 해결할까?
- WebSocket 연결만 열면 채팅 백엔드는 끝나는 걸까?
- 메시지를 어떤 채팅방으로 보낼지는 누가 정할까?
- 로그인한 사용자가 어떤 방을 구독할 수 있는지는 어디서 검사할까?
- 메시지가 서버에 도착한 것과 DB에 저장된 것은 같은 성공일까?

이번 글에서는 HTTP polling과 WebSocket을 비교하고, `realtime-chat` 프로젝트에서 WebSocket을 어떤 위치에 두었는지 정리해보려고 한다.

## 쉬운 비유

HTTP polling은 사용자가 계속 물어보는 방식에 가깝다.

```text
클라이언트: 새 메시지 있어요?
서버: 없어요.

클라이언트: 새 메시지 있어요?
서버: 없어요.

클라이언트: 새 메시지 있어요?
서버: 이제 하나 있어요.
```

반면 WebSocket은 전화를 연결해두는 것에 가깝다.

```text
클라이언트와 서버가 연결을 유지한다.

서버: 새 메시지가 왔어요.
클라이언트: 받았어요.

클라이언트: 메시지를 보낼게요.
서버: 받았어요.
```

즉, HTTP polling은 클라이언트가 계속 묻는 방식이고, WebSocket은 연결을 유지한 뒤 서버가 먼저 메시지를 보낸다.

## HTTP 요청/응답 방식의 한계

일반적인 HTTP 요청/응답 모델에서는 클라이언트가 먼저 요청해야 서버가 응답한다.

게시글 목록 조회나 프로필 조회처럼 사용자가 필요할 때 데이터를 가져오는 기능에는 이 방식이 자연스럽다.
하지만 채팅에서는 상황이 다르다.

채팅방에 누군가 새 메시지를 보냈다면, 서버는 그 메시지를 다른 참여자에게 바로 알려줘야 한다.
그런데 순수한 HTTP 요청/응답 흐름만 사용하면 클라이언트가 주기적으로 서버에 물어봐야 한다.

```text
GET /api/rooms/1/messages?after=100
GET /api/rooms/1/messages?after=100
GET /api/rooms/1/messages?after=100
```

이런 polling 방식은 구현은 단순하지만 몇 가지 문제가 있다.

- 새 메시지가 없어도 계속 요청이 발생한다.
- polling 간격이 길면 메시지가 늦게 보인다.
- polling 간격을 짧게 잡으면 서버와 네트워크 부담이 커진다.
- 서버 입장에서는 대부분의 요청이 "새 데이터 없음"일 수 있다.

채팅처럼 사용자가 실시간성을 기대하는 기능에서는 이 구조가 어색해진다.

## WebSocket은 무엇을 해결하는가

WebSocket은 브라우저와 서버 사이에 양방향 통신 세션을 열 수 있게 해준다.
MDN 문서에서도 WebSocket API를 사용하면 서버 응답을 받기 위해 계속 polling하지 않고도 메시지를 보내고 받을 수 있다고 설명한다.

핵심은 연결을 유지한다는 점이다.

```text
Client
  <====================>
             Server

연결을 유지한 상태에서 양쪽이 메시지를 주고받는다.
```

이 구조에서는 서버가 새 이벤트를 감지했을 때 클라이언트에게 바로 메시지를 보낼 수 있다.

채팅에서는 이 차이가 크다.

```text
1. 사용자 A가 메시지를 보낸다.
2. 서버가 메시지를 처리한다.
3. 서버가 같은 채팅방을 구독 중인 사용자 B, C에게 바로 내려준다.
```

클라이언트가 계속 "새 메시지 있어요?"라고 묻지 않아도 된다.
서버가 먼저 알려줄 수 있기 때문이다.

## 프로젝트에서는 어떻게 구현했나

`realtime-chat` 프로젝트에서는 클라이언트가 WebSocket STOMP 연결로 메시지를 보내고 받는다.

## 흐름도

### 흐름도 쉽게 읽기

이 흐름에서 WebSocket은 계속 열려 있는 통로이고, STOMP destination은 그 통로 안에서 사용하는 주소다.

| 단계 | 쉽게 보면 |
| --- | --- |
| `CONNECT` | 서버와 실시간 연결을 열고 사용자를 확인하는 단계 |
| `SUBSCRIBE` | 어떤 채팅방 메시지를 받을지 신청하는 단계 |
| `SEND` | 클라이언트가 서버로 채팅 메시지를 보내는 단계 |
| Kafka / Consumer | 메시지를 저장하고 다른 사용자에게 전달하기 위한 서버 내부 흐름 |
| `MESSAGE` 수신 | room topic을 구독 중인 클라이언트가 메시지를 받는 단계 |

즉 WebSocket 하나만으로 채팅 규칙이 생기는 것이 아니라, 연결 이후의 주소와 상태를 따로 정해야 한다.

큰 흐름은 다음과 같다.

```text
Client
  -> WebSocket STOMP CONNECT
  -> SUBSCRIBE /topic/room.{roomId}
  -> SEND /app/chat.send
  -> Spring Boot
  -> Kafka publish
  -> Consumer DB 저장
  -> room topic fan-out
  -> Client receives MESSAGE
```

여기서 WebSocket은 클라이언트와 서버 사이의 실시간 통신 통로다.

하지만 이 통로만으로는 부족하다.
그래서 이 프로젝트에서는 WebSocket 위에서 STOMP를 사용한다.

STOMP는 메시지를 어디로 보낼지, 어디를 구독할지 표현하는 규칙을 제공한다.

## 코드 또는 설정 일부

```text
SEND /app/chat.send
SUBSCRIBE /topic/room.{roomId}
SUBSCRIBE /user/queue/messages/ack
SUBSCRIBE /user/queue/messages/error
SUBSCRIBE /user/queue/messages/persisted
```

### 코드 쉽게 읽기

각 줄은 실제 코드라기보다 "어디로 보내고 어디서 받을지"를 나타내는 주소 목록이다.
초심자 입장에서는 아래처럼 읽으면 된다.

| 주소 | 한 줄 해석 |
| --- | --- |
| `SEND /app/chat.send` | 서버에게 "이 메시지를 처리해줘"라고 보내는 입구 |
| `SUBSCRIBE /topic/room.{roomId}` | 특정 채팅방의 새 메시지를 받겠다고 구독 |
| `SUBSCRIBE /user/queue/...` | 나에게만 오는 처리 결과를 받는 개인 채널 |

이렇게 destination을 나누면 메시지 흐름을 더 명확히 볼 수 있다.

- `/app/chat.send`: 클라이언트가 서버로 채팅 메시지를 보냄
- `/topic/room.{roomId}`: 같은 room을 구독한 사용자들이 메시지를 받음
- `/user/queue/messages/ack`: 특정 사용자에게 Kafka publish accepted 결과를 알려줌
- `/user/queue/messages/error`: 특정 사용자에게 publish 실패를 알려줌
- `/user/queue/messages/persisted`: 특정 사용자에게 DB 저장 완료를 알려줌

즉, WebSocket은 통로이고 STOMP destination은 주소에 가깝다.

## 이 설계가 해결한 문제

WebSocket 연결이 열렸다고 해서 채팅 시스템의 문제가 모두 해결되지는 않는다.

실제로는 다음 질문들이 남는다.

```text
이 사용자는 누구인가?
이 사용자는 이 room을 구독할 권한이 있는가?
이 사용자가 이 room에 메시지를 보낼 권한이 있는가?
메시지가 Kafka publish까지 성공했는가?
DB 저장까지 완료됐는가?
수신자가 실제로 메시지를 받았는가?
사용자가 메시지를 읽었는가?
연결이 끊겼다가 다시 들어오면 누락 메시지는 어떻게 복구할 것인가?
```

그래서 `realtime-chat`에서는 WebSocket 연결 이후의 경계를 나누었다.

| 단계 | 역할 |
|---|---|
| `CONNECT` | JWT 인증 |
| `SUBSCRIBE /topic/room.{roomId}` | room member 인가 |
| `SEND /app/chat.send` | 메시지 전송 전 room member 재검증 |
| Kafka publish | 비동기 메시지 흐름 진입 |
| ACK/NACK | publish accepted/failed 결과 |
| PERSISTED | DB 저장 완료 또는 idempotent row 확인 |
| Reconnect Sync API | 재연결 후 누락 메시지 복구 |

여기서 중요한 문장은 이것이다.

```text
WebSocket은 실시간 통신의 통로일 뿐이고,
그 위에서 어떤 메시지를 어디로 보낼지 정하는 규칙은 따로 필요했다.
```

## 한계와 개선점

WebSocket은 실시간 채팅에 잘 맞지만, 항상 모든 문제의 답은 아니다.

연결을 유지한다는 것은 서버가 연결 상태를 관리해야 한다는 뜻이기도 하다.
사용자가 많아질수록 연결 수, heartbeat, reconnect, backpressure, 인증 만료, 서버 재시작 같은 문제를 함께 봐야 한다.

또한 WebSocket을 사용한다고 해서 메시지 전달 보장이 자동으로 생기지는 않는다.
이 프로젝트에서도 ACK, PERSISTED, RECEIVED, READ를 분리해서 본 이유가 여기에 있다.

- ACK는 Kafka publish accepted를 의미한다.
- PERSISTED는 DB 저장 완료 또는 기존 idempotent row 확인을 의미한다.
- RECEIVED는 receiver runner가 room topic MESSAGE를 관측한 기록이다.
- READ는 사용자가 읽음 처리한 상태다.

WebSocket은 이 상태들을 전달할 수 있는 통로를 제공하지만, 각 상태의 의미는 서버 설계에서 별도로 정해야 한다.

## 관련 링크

- GitHub Repository: [sjh9714/realtime-chat](https://github.com/sjh9714/realtime-chat)
- MDN WebSocket API: [WebSocket API (WebSockets)](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
- 이전 글: [[실시간 채팅 백엔드] WebSocket 채팅 서버를 만들며 고민한 것들](https://velog.io/@sjh9714/실시간-채팅-백엔드-WebSocket-채팅-서버를-만들며-고민한-것들)
- 다음 글: [[실시간 채팅 백엔드] STOMP는 WebSocket 위의 메시지 주소 체계다](https://velog.io/@sjh9714/실시간-채팅-백엔드-STOMP는-WebSocket-위의-메시지-주소-체계다)

## 마무리

처음에는 채팅을 만들려면 WebSocket을 쓰면 된다고만 생각했다.

하지만 실제로는 WebSocket이 해결하는 문제와 해결하지 않는 문제를 나누어 봐야 했다.
WebSocket은 서버가 먼저 메시지를 보낼 수 있는 실시간 통신 통로를 제공한다.

다만 채팅 백엔드에서는 그 통로 위에 STOMP destination, CONNECT 인증, SUBSCRIBE 인가, ACK/NACK, PERSISTED 같은 규칙이 필요했다.

다음 글에서는 이 통로 위에서 메시지 주소 체계 역할을 하는 STOMP를 정리해보려고 한다.
