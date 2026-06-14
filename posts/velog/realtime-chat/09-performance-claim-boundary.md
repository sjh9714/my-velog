# [실시간 채팅 백엔드] 성능 수치를 주장할 때 조심해야 할 것들

## 한 줄 요약

성능 수치는 숫자보다 정의가 먼저다.
`realtime-chat`에서는 REST 조회 성능, WebSocket 연결 smoke, receiver matrix local scenario, production benchmark를 서로 다른 범위로 분리했다.

## 이 글에서 다룰 문제

포트폴리오에 성능 수치를 쓰고 싶을 때 가장 조심해야 하는 것은 숫자를 크게 보이게 만드는 욕심이다.

처음에는 "1,000명 테스트" 같은 문장을 쓰면 프로젝트가 더 좋아 보일 거라고 생각했다.
하지만 측정 문서를 정리하면서 중요한 것은 숫자 자체보다 그 숫자가 무엇을 의미하는지였다.

- 이 수치는 REST 조회 API 성능인가?
- WebSocket 연결 성공률인가?
- Kafka publish ACK latency인가?
- receiver 기준 send-to-receive latency인가?
- local Docker Compose 결과인가, production benchmark인가?
- 발신자 self echo를 전체 수신자 delivery로 착각하고 있지는 않은가?

이 질문에 답하지 못하면 성능 수치는 오히려 신뢰도를 떨어뜨린다.

## 쉬운 비유

달리기 기록으로 비유하면, 100m 기록과 마라톤 기록은 비교할 수 없다.

둘 다 "빠르다"는 말로 묶을 수 있지만 측정 대상이 다르다.
100m 기록을 가지고 "장거리도 빠르다"고 말하면 과장이다.

채팅 성능도 마찬가지다.
ACK latency, persisted latency, recipient receive latency는 모두 다른 지표다.
이걸 한 그래프에 넣고 "채팅 latency"라고 부르면 해석이 흐려진다.

## 프로젝트에서는 어떻게 구현했나

README와 measurement 문서에서는 측정한 것과 아직 주장하지 않는 것을 분리했다.

REST 조회 API 최적화는 실제 수치가 있다.

| 항목 | Before | After |
| --- | --- | --- |
| RPS | 937 | 1,598 |
| p95 응답 시간 | 212.85ms | 149.22ms |
| 조건 | k6 200 VU / 50s / local Docker | k6 200 VU / 50s / local Docker |

하지만 이 수치는 채팅 메시지 delivery 성능이 아니다.
주로 채팅방 목록 조회의 N+1 제거와 Redis cache가 적용된 REST 조회 시나리오다.

WebSocket 쪽도 연결 안정성과 delivery completeness를 분리했다.
2대 합산 1,158 sessions에서 연결 체크 성공률 100%를 확인했지만, 이것을 "1,000명 메시지 전달 성능 보장"으로 말하지 않는다.

## 흐름도

### 흐름도 쉽게 읽기

이 흐름도는 성능 수치를 하나의 "채팅 성능"으로 뭉뚱그리지 않기 위한 지도다.

| 지표 | 말할 수 있는 것 | 말하면 안 되는 것 |
| --- | --- | --- |
| REST rooms API RPS / p95 | 조회 API 최적화 결과 | 메시지 delivery 성능 |
| WebSocket connection success | 연결 smoke 성공 여부 | 1,000명 메시지 전달 보장 |
| ACK latency | Kafka publish accepted까지의 시간 | DB 저장 완료 시간 |
| PERSISTED latency | DB 저장 완료까지의 시간 | 상대방 수신 시간 |
| recipient receive latency | receiver가 MESSAGE를 파싱한 시간 | 사용자가 읽은 시간 |

숫자보다 먼저 "어떤 구간을 잰 숫자인가"를 정해야 한다.
그래야 면접이나 문서에서 과장 없이 설명할 수 있다.

```text
Metric
  |
  |-- REST rooms API RPS / p95
  |     -> 조회 API 최적화 claim
  |
  |-- WebSocket connection success
  |     -> 연결 smoke claim
  |
  |-- ACK latency
  |     -> Kafka publish accepted까지
  |
  |-- PERSISTED latency
  |     -> DB 저장 완료까지
  |
  |-- recipient receive latency
        -> receiver가 MESSAGE frame을 파싱하기까지
```

서로 다른 지표를 같은 이름으로 부르지 않는 것이 핵심이다.

## 코드 또는 설정 일부

measurement 문서의 기준을 요약하면 다음과 같다.

```text
send-to-receive latency =
sender client가 STOMP SEND frame을 socket에 기록하기 직전 시각
-> receiver client가 /topic/room.{roomId} MESSAGE frame을 파싱한 시각
```

delivery completeness도 sender를 제외한 room member recipient 기준으로 계산한다.

```text
expected deliveries =
테스트 시작 barrier 이후 구독 완료된 room member 수 - sender 1명

actual deliveries =
각 receiver가 messageKey 또는 clientMessageId 기준으로 실제 수신한 unique delivery 수
```

### 코드 쉽게 읽기

measurement 정의는 성능 수치의 분모와 시작/끝 지점을 고정하기 위한 장치다.

| 정의 | 쉽게 보면 |
| --- | --- |
| send-to-receive 시작 | sender가 WebSocket에 SEND frame을 쓰기 직전 |
| send-to-receive 끝 | receiver가 room topic MESSAGE frame을 파싱한 시점 |
| expected deliveries | sender를 제외한 실제 수신 대상 수 |
| actual deliveries | 중복을 제거하고 실제로 관측한 수신 수 |

이 기준이 있어야 "missing 0"이나 "duplicate 0" 같은 표현이 의미를 가진다.
기준 없이 숫자만 쓰면 REST 성능, 연결 성공률, 메시지 전달 성능이 서로 섞여 보인다.

이 정의가 있어야 "누락 0", "중복 0", "p95" 같은 말을 안전하게 쓸 수 있다.

## 이 설계가 해결한 문제

첫 번째로 과장된 성능 claim을 피할 수 있다.
local Docker Compose 결과를 production benchmark처럼 말하지 않는다.

두 번째로 지표별 의미가 선명해진다.
ACK는 Kafka publish accepted이고, PERSISTED는 DB 저장 완료이며, RECEIVED는 runner가 MESSAGE를 관측한 기록이다.

세 번째로 면접에서 방어 가능한 설명이 된다.
"어떤 환경에서 무엇을 측정했는가"를 말할 수 있으면 숫자보다 설계 태도가 더 잘 드러난다.

## 한계와 개선점

현재 공개 수치에는 아직 주장하지 않는 범위가 있다.

- production 1,000-session send-to-receive latency benchmark
- production delivery completeness benchmark
- mixed traffic p95 latency benchmark
- mixed traffic cache hit rate
- Redis rate-limit 알고리즘 비교

또한 local receiver matrix repeat3 결과는 local scenario evidence로 볼 수 있지만, production benchmark로 확장해서 말하지 않는다.

앞으로는 실행 환경, 부하 모델, clock skew, sender/receiver 분리, drain time, expected delivery denominator를 함께 기록해야 한다.

## 관련 링크

- GitHub Repository: [sjh9714/realtime-chat](https://github.com/sjh9714/realtime-chat)
- WebSocket measurement 문서: [docs/WEBSOCKET_MEASUREMENT.md](https://github.com/sjh9714/realtime-chat/blob/main/docs/WEBSOCKET_MEASUREMENT.md)
- Performance 문서: [docs/PERF_RESULT.md](https://github.com/sjh9714/realtime-chat/blob/main/docs/PERF_RESULT.md)
- 이전 글: [[실시간 채팅 백엔드] 안 읽은 메시지 수는 생각보다 단순하지 않다](https://velog.io/@sjh9714/실시간-채팅-백엔드-안-읽은-메시지-수는-생각보다-단순하지-않다)

## 마무리

성능 수치는 포트폴리오에서 강한 인상을 줄 수 있다.
하지만 경계 없이 쓰면 오히려 위험하다.

이번 프로젝트에서 가장 크게 배운 점은 "측정했다"보다 "무엇을 측정했고, 무엇은 아직 주장하지 않는지"가 더 중요하다는 것이다.

그래서 이 시리즈의 마지막은 숫자를 크게 보이는 글이 아니라, 숫자의 의미를 좁히는 글로 마무리하고 싶었다.
