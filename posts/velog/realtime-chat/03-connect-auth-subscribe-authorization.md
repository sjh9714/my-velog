# [실시간 채팅 백엔드] 로그인한 사용자도 아무 채팅방이나 구독하면 안 된다

## 한 줄 요약

WebSocket에서 JWT 인증이 성공했다고 해서 모든 채팅방을 구독할 수 있는 것은 아니다.
`CONNECT` 인증과 `SUBSCRIBE` 인가는 서로 다른 문제로 분리해야 한다.

## 이 글에서 다룰 문제

처음에는 WebSocket 연결 시점에 JWT만 검증하면 충분하다고 생각했다.

사용자가 로그인했고, 토큰도 유효하다면 WebSocket 연결을 허용해도 된다고 본 것이다.
하지만 채팅방 구독까지 생각하면 이야기가 달라진다.

예를 들어 사용자 A가 정상적으로 로그인했다고 해보자.
A의 JWT는 유효하다.
하지만 A는 `roomId = 10` 채팅방의 멤버가 아니다.

그런데 A가 아래 destination을 구독하려고 하면 어떻게 해야 할까?

```text
SUBSCRIBE /topic/room.10
```

JWT만 보면 A는 정상 사용자다.
하지만 room 관점에서 보면 A는 해당 방을 볼 권한이 없다.

그래서 이 프로젝트에서는 인증과 인가를 분리했다.

```text
인증: 너 누구야?
인가: 너 이 방에 들어올 권한 있어?
```

## 쉬운 비유

회사 건물 출입증으로 비유할 수 있다.

출입증이 유효하면 회사 건물에는 들어갈 수 있다.
하지만 출입증이 있다고 해서 모든 회의실, 서버실, 임원실에 들어갈 수 있는 것은 아니다.

WebSocket `CONNECT` 인증은 건물 입구에서 출입증을 확인하는 단계에 가깝다.
`SUBSCRIBE` 인가는 특정 회의실에 들어갈 수 있는지 확인하는 단계다.

채팅방도 마찬가지다.
로그인한 사용자라는 사실과 특정 채팅방의 멤버라는 사실은 다르다.

## 프로젝트에서는 어떻게 구현했나

`realtime-chat`에서는 STOMP inbound 흐름에서 세 단계를 나눴다.

| 단계 | 담당 | 목적 |
|---|---|---|
| `CONNECT` | `WebSocketAuthInterceptor` | JWT 검증, STOMP Principal에 `userId` 바인딩 |
| `SUBSCRIBE` | `WebSocketAuthorizationInterceptor` | `/topic/room.{roomId}` 구독 시 room member 검증 |
| `SEND` | `ChatMessageController` | 메시지 전송 시 room member 재검증 |

핵심은 `CONNECT`에서 끝내지 않는 것이다.

연결 시 JWT를 검증하고 사용자 식별자를 Principal에 묶는다.
그 다음 사용자가 room topic을 구독할 때 destination에서 `roomId`를 추출하고, 해당 사용자가 그 room의 멤버인지 다시 확인한다.

메시지를 보낼 때도 마찬가지다.
구독 때 통과했다고 해서 SEND를 무조건 믿지 않고, 메시지 전송 시점에도 room member를 다시 검증한다.

## 흐름도

### 흐름도 쉽게 읽기

이 흐름도는 "로그인 성공"과 "채팅방 접근 허용"이 다른 단계라는 점을 보여준다.

| 단계 | 질문 |
| --- | --- |
| `CONNECT` | 이 사용자는 유효한 JWT를 가진 사용자인가? |
| `SUBSCRIBE` | 이 사용자는 이 room의 메시지를 받아도 되는가? |
| `SEND` | 이 사용자는 이 room에 메시지를 보내도 되는가? |

`CONNECT`에서 사용자를 확인했더라도, room마다 권한은 다시 확인해야 한다.
그래서 room topic 구독과 메시지 전송을 각각 별도 경계로 둔다.

```text
Client
  |
  | STOMP CONNECT + JWT
  v
WebSocketAuthInterceptor
  |
  | JWT 검증 성공
  | Principal(userId) 바인딩
  v
CONNECTED
  |
  | SUBSCRIBE /topic/room.{roomId}
  v
WebSocketAuthorizationInterceptor
  |
  | room membership 검증
  v
구독 허용 or 거부
  |
  | SEND /app/chat.send
  v
ChatMessageController
  |
  | room membership 재검증
  v
Kafka publish
```

이렇게 보면 WebSocket 연결은 시작점일 뿐이다.
실제로 사용자가 어떤 destination을 구독하고 어떤 room에 메시지를 보내는지는 별도로 검증해야 한다.

## 코드 또는 설정 일부

이 글에서는 실제 전체 코드를 가져오기보다 정책을 의사코드로 정리해보면 충분하다.

```text
on CONNECT:
  token = Authorization header에서 추출
  userId = JWT 검증 결과에서 추출
  STOMP Principal에 userId 저장

on SUBSCRIBE:
  destination = frame.destination
  if destination matches /topic/room.{roomId}:
    userId = Principal.userId
    if userId is not member of roomId:
      reject subscribe

on SEND /app/chat.send:
  userId = Principal.userId
  roomId = payload.roomId
  if userId is not member of roomId:
    reject send
  else:
    publish to Kafka
```

여기서 중요한 destination은 다음과 같다.

```text
SUBSCRIBE /topic/room.{roomId}
SEND /app/chat.send
SUBSCRIBE /user/queue/messages/ack
SUBSCRIBE /user/queue/messages/error
SUBSCRIBE /user/queue/messages/persisted
```

### 코드 쉽게 읽기

이 pseudo code는 세 개의 문을 따로 둔 것으로 보면 된다.

| 문 | 통과 조건 |
| --- | --- |
| `CONNECT` | 토큰이 유효하고 `userId`를 Principal에 묶을 수 있어야 함 |
| `SUBSCRIBE /topic/room.{roomId}` | Principal의 사용자가 해당 room 멤버여야 함 |
| `SEND /app/chat.send` | payload의 room에 메시지를 보낼 권한이 있어야 함 |

`/user/queue/messages/...`는 개인 응답 채널이라 room broadcast와 다르게 본다.
room topic처럼 모든 사용자에게 열려 있는 주소가 아니라, 서버가 특정 사용자에게 결과를 내려주는 경로에 가깝다.

`/topic/room.{roomId}`는 같은 채팅방 사용자들이 함께 보는 room topic이다.
반면 `/user/queue/messages/ack`, `/user/queue/messages/error`, `/user/queue/messages/persisted`는 특정 사용자에게만 내려가는 개인 응답 채널로 볼 수 있다.

## 이 설계가 해결한 문제

이 설계가 없으면 다음 문제가 생길 수 있다.

```text
1. 공격자가 정상 JWT로 WebSocket CONNECT에 성공한다.
2. roomId를 추측한다.
3. /topic/room.{roomId}를 구독한다.
4. 본인이 속하지 않은 채팅방 메시지를 볼 수 있다.
```

이 문제는 단순히 "로그인 여부"만 확인해서는 막을 수 없다.
특정 room topic에 접근할 권한이 있는지를 확인해야 한다.

`SUBSCRIBE` 인가를 추가하면 room 멤버가 아닌 사용자의 구독을 거부할 수 있다.
`SEND`에서도 room member를 재검증하면, 구독은 하지 않았지만 메시지 전송 endpoint로 직접 보내는 시도도 막을 수 있다.

## 검증 포인트

README의 Evidence Matrix 기준으로 이 프로젝트는 비멤버 room topic 구독 거부를 Unit + STOMP integration 테스트로 검증했다.

검증해야 할 시나리오는 다음과 같다.

- 유효한 JWT + room member: 구독 허용
- 유효한 JWT + room non-member: 구독 거부
- malformed room topic: 거부
- room topic이 아닌 destination: 기존 정책 유지
- 메시지 SEND 시 room member가 아니면 거부

여기서 핵심은 "JWT가 유효한 사용자"를 실패 케이스에 넣는 것이다.
그래야 인증과 인가를 분리해서 검증할 수 있다.

## 이 글의 검증 근거

이 글에서 말한 `CONNECT 인증`과 `SUBSCRIBE 인가` 분리는 실제 STOMP interceptor에서 확인할 수 있다. `SUBSCRIBE` 프레임만 골라 destination에서 roomId를 추출하고, 현재 사용자가 해당 room member인지 다시 검사한다.

```java
@Override
public Message<?> preSend(Message<?> message, MessageChannel channel) {
  StompHeaderAccessor accessor =
      MessageHeaderAccessor.getAccessor(message, StompHeaderAccessor.class);
  if (accessor == null || !StompCommand.SUBSCRIBE.equals(accessor.getCommand())) {
    return message;
  }

  String destination = accessor.getDestination();
  Long roomId = extractRoomId(destination);
  if (roomId == null) {
    if (isRoomTopicCandidate(destination)) {
      throw new AccessDeniedException("잘못된 채팅방 구독 경로입니다.");
    }
    return message;
  }

  Principal principal = accessor.getUser();
  if (principal == null) {
    throw new AccessDeniedException("인증된 사용자만 채팅방을 구독할 수 있습니다.");
  }

  Long userId = parseUserId(principal);
  if (!chatRoomMemberRepository.existsByChatRoomIdAndUserId(roomId, userId)) {
    throw new AccessDeniedException("채팅방 구독 권한이 없습니다.");
  }

  return message;
}
```

검증은 `WebSocketAuthInterceptorTest`, `WebSocketAuthorizationInterceptorTest`, `WebSocketSubscribeAuthorizationIntegrationTest`를 기준으로 확인했다. 로그인한 사용자라도 room member가 아니면 구독이 막혀야 한다는 점이 이 글의 핵심이다.

## 한계와 개선점

이 구조는 room membership 기반 구독 권한을 다룬다.
하지만 운영 환경에서는 더 많은 정책이 필요할 수 있다.

- 강퇴된 사용자의 기존 WebSocket session 처리
- room membership 변경 시 기존 subscription revoke 전략
- 관리자/운영자 권한처럼 일반 멤버와 다른 권한 모델
- STOMP ERROR payload의 표준화
- 권한 거부 이벤트의 audit log 기록

또한 `/topic/presence`처럼 room topic이 아닌 destination은 같은 방식으로 처리하면 안 된다.
destination마다 권한 모델이 다를 수 있으므로, room topic 정책과 presence topic 정책을 구분해야 한다.

## 관련 링크

- GitHub Repository: [sjh9714/realtime-chat](https://github.com/sjh9714/realtime-chat)
- Architecture 문서: [docs/ARCHITECTURE.md](https://github.com/sjh9714/realtime-chat/blob/main/docs/ARCHITECTURE.md)
- 이전 글: [[실시간 채팅 백엔드] STOMP는 WebSocket 위의 메시지 주소 체계다](https://velog.io/@sjh9714/실시간-채팅-백엔드-STOMP는-WebSocket-위의-메시지-주소-체계다)
- 다음 글: [[실시간 채팅 백엔드] ACK는 상대방이 읽었다는 뜻이 아니다](https://velog.io/@sjh9714/실시간-채팅-백엔드-ACK는-상대방이-읽었다는-뜻이-아니다)

## 마무리

WebSocket 인증에서 가장 조심해야 할 점은 "연결된 사용자"와 "특정 채팅방을 볼 수 있는 사용자"를 같은 의미로 보면 안 된다는 것이다.

JWT 인증은 사용자가 누구인지 확인한다.
하지만 채팅방 구독 권한은 그 사용자가 해당 room의 멤버인지 따로 확인해야 한다.

그래서 이 프로젝트에서는 `CONNECT` 인증, `SUBSCRIBE` 인가, `SEND` 재검증을 나누었다.
작은 차이처럼 보이지만, 이 차이가 실시간 채팅 백엔드에서 메시지 노출 사고를 막는 중요한 경계가 된다.
