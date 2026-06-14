# [실시간 채팅 백엔드] Kafka를 쓰면 메시지 순서가 자동으로 보장될까?

## 한 줄 요약

Kafka를 사용한다고 해서 모든 메시지의 전역 순서가 자동으로 보장되는 것은 아니다.
`realtime-chat`에서 검증한 순서 범위는 `roomId` key를 사용한 동일 room 내 partition ordering이다.

## 이 글에서 다룰 문제

채팅에서 메시지 순서는 중요하다.
사용자가 "안녕" 다음에 "혹시 지금 시간 돼?"라고 보냈는데, 상대방 화면에서는 반대로 보이면 대화가 어색해진다.

처음에는 Kafka를 쓰면 메시지가 알아서 순서대로 처리될 거라고 생각했다.
하지만 Kafka의 순서 보장은 범위가 있다.

- 같은 topic의 모든 메시지가 전역으로 순서 보장될까?
- 서로 다른 채팅방 메시지 사이에도 순서가 필요할까?
- 같은 채팅방 메시지만 순서가 맞으면 충분할까?
- 어떤 key를 써야 같은 채팅방 메시지가 같은 partition으로 갈까?

이 프로젝트에서는 "전체 시스템의 모든 메시지 순서"가 아니라 "같은 room 안의 메시지 순서"를 목표로 잡았다.

## 쉬운 비유

Kafka partition은 여러 줄로 나뉜 계산대와 비슷하다.

한 계산대 안에서는 먼저 줄 선 사람이 먼저 계산한다.
하지만 계산대가 여러 개라면 전체 매장 기준으로 누가 먼저 계산을 끝낼지는 알 수 없다.

채팅방도 비슷하다.
room A와 room B 사이의 전역 순서는 큰 의미가 없다.
대신 room A 안에서 보낸 메시지는 room A 사용자들에게 같은 순서로 보이는 것이 중요하다.

## 프로젝트에서는 어떻게 구현했나

`realtime-chat`에서는 채팅 메시지를 Kafka에 publish할 때 `roomId`를 key로 사용한다.

```text
KafkaTemplate.send(chat.messages, key = roomId, event)
```

같은 key는 같은 partition으로 들어가므로, 같은 room의 메시지는 같은 partition 안에서 offset 순서를 가진다.
consumer는 저장 시 `kafkaPartition`, `kafkaOffset`도 함께 기록한다.

검증 범위는 아래처럼 제한했다.

| 구분 | 보장 또는 검증 |
| --- | --- |
| 같은 room 안의 메시지 | `roomId` key 기반 partition ordering |
| 같은 partition 안의 순서 | offset 순서 |
| 서로 다른 room 간 순서 | 보장하지 않음 |
| 운영 환경 전체 전역 순서 | 주장하지 않음 |

이 경계를 명확히 두어야 "Kafka를 썼으니 순서 보장"이라는 과장된 설명을 피할 수 있다.

## 흐름도

### 흐름도 쉽게 읽기

아래 예시는 Kafka 순서 보장의 범위를 좁혀서 보여준다.

| 요소 | 쉽게 보면 |
| --- | --- |
| `key = roomId` | 같은 채팅방 메시지를 같은 줄로 보내기 위한 기준 |
| partition | Kafka 안의 한 줄짜리 처리 순서 |
| offset | 같은 partition 안에서 붙는 순번 |
| 다른 room | 다른 줄에 설 수 있으므로 전역 순서를 비교하지 않음 |

즉 room 1 안에서는 10, 11, 12 순서를 말할 수 있지만, room 1과 room 2 사이의 전체 순서는 주장하지 않는다.

```text
room 1 messages
  -> key = 1
  -> partition 2
  -> offset 10, 11, 12

room 2 messages
  -> key = 2
  -> partition 4
  -> offset 7, 8, 9
```

room 1 안에서는 offset 10, 11, 12 순서를 볼 수 있다.
하지만 room 1의 offset 12와 room 2의 offset 7 사이에 전역 순서를 부여하지 않는다.

## 코드 또는 설정 일부

테스트 관점에서는 단일 room에 순차 메시지를 발행하고, 저장된 메시지가 같은 partition에 들어갔는지와 offset이 오름차순인지 확인한다.

```text
send message A to room 1
send message B to room 1
send message C to room 1

persisted records:
  A partition=2 offset=10
  B partition=2 offset=11
  C partition=2 offset=12
```

### 코드 쉽게 읽기

이 테스트는 Kafka 전체 순서가 아니라 "한 room 안의 순서"만 본다.

| 확인 항목 | 의미 |
| --- | --- |
| A/B/C가 모두 같은 partition | 같은 room key가 같은 Kafka 줄에 들어갔는지 확인 |
| offset이 10 -> 11 -> 12 | 같은 partition 안에서 순서가 유지됐는지 확인 |
| 다른 room 미포함 | 전역 순서를 테스트하지 않는다는 경계 표시 |

그래서 이 결과를 "Kafka를 쓰면 모든 메시지 순서가 보장된다"로 말하면 과장이다.
정확한 표현은 "같은 `roomId` key의 메시지에 대해 partition 내부 offset 순서를 검증했다"이다.

여기서 확인하는 것은 "room 1 안에서 A, B, C 순서가 유지되는가"다.
서로 다른 room 메시지까지 섞어서 하나의 전역 타임라인을 만들지는 않는다.

## 이 설계가 해결한 문제

첫 번째로 채팅방 단위의 자연스러운 순서 모델을 만들 수 있다.
사용자에게 중요한 것은 자신이 들어간 room의 메시지 순서다.

두 번째로 불필요한 전역 순서 요구를 피할 수 있다.
모든 room 메시지를 하나의 partition에 넣으면 순서는 단순해질 수 있지만 처리량과 확장성이 나빠진다.

세 번째로 테스트 가능한 claim boundary가 생긴다.
같은 room 내 partition/offset 순서는 검증할 수 있지만, 운영 환경 전체 전역 순서는 이 프로젝트에서 주장하지 않는다.

## 한계와 개선점

이 설계는 같은 room의 메시지가 같은 partition에 들어간다는 전제 위에 있다.
따라서 key 선택이 중요하다.
만약 producer가 실수로 다른 key를 사용하면 같은 room 메시지가 여러 partition으로 나뉠 수 있다.

또한 Kafka offset 순서와 사용자 화면에 렌더링되는 최종 순서는 다른 문제다.
네트워크 지연, 클라이언트 재연결, 중복 수신, sync API 처리까지 함께 봐야 사용자가 보는 순서를 안정적으로 만들 수 있다.

현재 프로젝트는 room 단위 ordering 검증을 제공하지만, production 환경에서의 장시간 반복 benchmark나 room-global ordering 성능 수치까지 주장하지는 않는다.

## 관련 링크

- GitHub Repository: [sjh9714/realtime-chat](https://github.com/sjh9714/realtime-chat)
- Testing 문서: [docs/TESTING.md](https://github.com/sjh9714/realtime-chat/blob/main/docs/TESTING.md)
- 이전 글: [[실시간 채팅 백엔드] 채팅 메시지를 바로 DB에 저장하지 않고 Kafka로 보낸 이유](https://velog.io/@sjh9714/실시간-채팅-백엔드-채팅-메시지를-바로-DB에-저장하지-않고-Kafka로-보낸-이유)
- 다음 글: [[실시간 채팅 백엔드] 실패한 메시지를 버리지 않기 위한 DLT와 replay 설계](https://velog.io/@sjh9714/실시간-채팅-백엔드-실패한-메시지를-버리지-않기-위한-DLT와-replay-설계)

## 마무리

Kafka를 쓰면 순서 문제가 모두 해결된다고 말하기 쉽다.
하지만 정확히는 "같은 key가 같은 partition에 들어가고, 같은 partition 안에서 offset 순서가 있다"가 맞다.

이 프로젝트에서는 `roomId`를 key로 사용해 같은 room 안의 메시지 순서를 검증했다.
서로 다른 room 사이의 전역 순서는 요구하지도, 주장하지도 않는다.

다음 글에서는 consumer 처리에 실패한 메시지를 버리지 않기 위한 DLT와 replay 설계를 정리한다.
