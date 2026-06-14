# [실시간 채팅 백엔드] 안 읽은 메시지 수는 생각보다 단순하지 않다

## 한 줄 요약

안 읽은 메시지 수는 단순히 전체 메시지 수에서 읽은 메시지 수를 빼면 끝나지 않는다.
`realtime-chat`에서는 발신자 제외, 참여 시각, `lastReadMessageId`를 기준으로 unread count 정합성을 검증했다.

## 이 글에서 다룰 문제

채팅방 목록에는 보통 안 읽은 메시지 수가 표시된다.
처음에는 이 값을 쉽게 계산할 수 있을 것 같았다.

하지만 실제 조건을 생각하면 단순하지 않다.

- 내가 보낸 메시지도 나에게 안 읽은 메시지로 세야 할까?
- 내가 채팅방에 들어오기 전에 쌓인 메시지는 안 읽은 메시지일까?
- 읽음 요청이 중복으로 들어오면 unread count가 흔들릴까?
- 더 과거 메시지 id로 읽음 처리가 들어오면 상태를 되돌려도 될까?
- Redis cache가 틀리면 어떤 값을 기준으로 복구할까?

이 프로젝트에서는 unread count를 "화면에 보이는 숫자"가 아니라 정합성을 지켜야 하는 상태로 봤다.

## 쉬운 비유

책갈피로 비유하면 쉽다.

책을 읽을 때 책갈피는 내가 어디까지 읽었는지 표시한다.
이미 100페이지까지 읽었는데 실수로 80페이지 책갈피가 다시 들어왔다고 해서 읽은 위치를 80페이지로 되돌리면 이상하다.

채팅의 `lastReadMessageId`도 비슷하다.
사용자가 어디까지 읽었는지 나타내는 기준점이고, 이 기준점은 뒤로 후퇴하면 안 된다.

## 프로젝트에서는 어떻게 구현했나

읽음 처리는 `lastReadMessageId`를 기준으로 room member row를 갱신한다.
그리고 unread count는 이 기준으로 다시 계산한다.

계산 조건은 아래와 같다.

- 같은 room의 메시지
- `message.id > lastReadMessageId`
- `message.senderId != userId`
- `message.createdAt >= member.joinedAt`

즉, 내가 읽은 마지막 메시지 이후의 메시지 중에서 내가 보낸 메시지를 제외하고, 내가 room에 참여한 뒤 생성된 메시지만 unread로 본다.

## 흐름도

### 흐름도 쉽게 읽기

읽음 처리는 단순히 "읽었다"를 저장하는 것이 아니라, 읽음 커서를 안전하게 앞으로 옮기는 작업이다.

| 단계 | 쉽게 보면 |
| --- | --- |
| `POST /read` | 클라이언트가 여기까지 읽었다고 알려줌 |
| room 메시지 검증 | 요청한 메시지가 정말 이 채팅방의 메시지인지 확인 |
| `joinedAt` 검증 | 사용자가 들어오기 전 메시지를 읽음 기준으로 삼지 않음 |
| `lastReadMessageId` 갱신 | 읽음 위치를 앞으로만 이동 |
| unread 재계산 | 내가 안 읽은 메시지 수를 DB 기준으로 다시 계산 |

핵심은 읽음 위치가 뒤로 가면 안 된다는 점이다.
늦게 도착한 오래된 read receipt가 최신 읽음 상태를 덮어쓰면 unread count가 다시 커질 수 있다.

```text
POST /api/rooms/{roomId}/read
  |
  | lastReadMessageId
  v
validate message belongs to room
  |
  | message.createdAt >= joinedAt
  v
update member.lastReadMessageId
  |
  v
recalculate unreadCount
```

읽음 요청이 들어오면 먼저 그 메시지가 해당 room의 메시지인지 확인한다.
그리고 사용자가 참여하기 전에 생성된 메시지를 읽음 기준으로 삼지 않도록 막는다.

## 코드 또는 설정 일부

정합성 규칙을 pseudo code로 표현하면 다음과 같다.

```text
if requestedLastReadMessageId <= currentLastReadMessageId:
    do not move read cursor backward

unreadCount =
    count messages
    where roomId = currentRoom
      and id > lastReadMessageId
      and senderId != currentUserId
      and createdAt >= joinedAt
```

### 코드 쉽게 읽기

이 pseudo code는 unread count를 계산할 때 빼야 하는 메시지를 명확히 보여준다.

| 조건 | 왜 필요한가 |
| --- | --- |
| `requestedLastReadMessageId <= currentLastReadMessageId` | 읽음 위치가 뒤로 가는 것을 막음 |
| `id > lastReadMessageId` | 이미 읽은 메시지는 제외 |
| `senderId != currentUserId` | 내가 보낸 메시지를 내 unread로 세지 않음 |
| `createdAt >= joinedAt` | 참여하기 전 과거 메시지를 unread로 세지 않음 |

그래서 unread count는 단순한 전체 메시지 수가 아니라, 사용자별 room membership 상태를 함께 봐야 하는 값이다.

핵심은 "읽음 위치는 앞으로만 간다"는 것이다.
중복 read receipt가 들어와도 기존 `lastReadMessageId`보다 크지 않으면 상태를 되돌리지 않는다.

## 이 설계가 해결한 문제

첫 번째로 내가 보낸 메시지가 내 unread count에 포함되는 문제를 막는다.
채팅 UI에서 내가 방금 보낸 메시지를 내가 안 읽었다고 표시하면 어색하다.

두 번째로 참여 전 메시지를 unread로 세지 않는다.
새로 들어온 사용자가 과거 대화 전체를 안 읽은 메시지로 받으면 숫자가 과하게 커진다.

세 번째로 중복 요청이나 순서가 뒤섞인 읽음 요청에 강해진다.
`lastReadMessageId`가 뒤로 가지 않기 때문에 이전 요청이 늦게 도착해도 상태를 되돌리지 않는다.

## 한계와 개선점

unread count는 DB 기준으로 재계산할 수 있어야 한다.
Redis cache는 빠른 조회를 돕지만 진실 소스가 아니다.

또한 모바일 push, multi-device read sync, 오프라인 상태에서의 읽음 처리까지 들어가면 정책이 더 복잡해진다.
예를 들어 한 사용자가 노트북과 휴대폰으로 동시에 접속했을 때 어느 기기의 읽음 처리를 기준으로 볼지 정해야 한다.

이 프로젝트는 sender 제외, joinedAt 이전 메시지 제외, lastReadMessageId 후퇴 방지라는 핵심 정합성을 테스트로 검증한 범위로 설명하는 것이 안전하다.

## 관련 링크

- GitHub Repository: [sjh9714/realtime-chat](https://github.com/sjh9714/realtime-chat)
- Testing 문서: [docs/TESTING.md](https://github.com/sjh9714/realtime-chat/blob/main/docs/TESTING.md)
- 이전 글: [[실시간 채팅 백엔드] 실패한 메시지를 버리지 않기 위한 DLT와 replay 설계](https://velog.io/@sjh9714/실시간-채팅-백엔드-실패한-메시지를-버리지-않기-위한-DLT와-replay-설계)
- 다음 글: [[실시간 채팅 백엔드] 성능 수치를 주장할 때 조심해야 할 것들](https://velog.io/@sjh9714/실시간-채팅-백엔드-성능-수치를-주장할-때-조심해야-할-것들)

## 마무리

안 읽은 메시지 수는 작은 숫자처럼 보이지만, 사용자 경험에서는 꽤 민감한 값이다.
한두 개만 틀려도 사용자는 바로 어색함을 느낀다.

이번 구현에서 배운 점은 unread count도 단순 카운트가 아니라 상태 전이 문제라는 것이다.
누가 보냈는지, 언제 참여했는지, 어디까지 읽었는지를 함께 봐야 한다.

마지막 글에서는 이 프로젝트의 성능 수치를 어떻게 말해야 안전한지 정리한다.
