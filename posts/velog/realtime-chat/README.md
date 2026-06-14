# realtime-chat Velog Series

`sjh9714/realtime-chat` 프로젝트를 포트폴리오용 기술 블로그 시리즈로 정리하기 위한 Velog 초안 모음입니다.

## 시리즈 구성

1. `00-websocket-chat-backend-intro.md`
   - 프로젝트 소개, 전체 아키텍처, 시리즈 예고
2. `01-why-websocket.md`
   - HTTP polling과 WebSocket 비교
3. `02-stomp-destination.md`
   - STOMP destination과 메시지 주소 체계
4. `03-connect-auth-subscribe-authorization.md`
   - WebSocket CONNECT 인증과 SUBSCRIBE 인가 분리
5. `04-ack-is-not-read.md`
   - ACK/NACK/PERSISTED/RECEIVED/READ의 의미 경계
6. `05-why-kafka-before-db.md`
   - 메시지 저장과 fan-out 경계를 Kafka로 분리한 이유
7. `06-kafka-room-ordering.md`
   - roomId key 기반 Kafka ordering claim boundary
8. `07-dlt-replay.md`
   - DLT 격리와 manual replay utility
9. `08-unread-count-consistency.md`
   - sender 제외, joinedAt, lastReadMessageId 기반 unread count 정합성
10. `09-performance-claim-boundary.md`
    - 성능 수치와 claim boundary 정리

## 작성 원칙

- 내가 처음 착각한 점 -> 문제 발견 -> 설계 결정 -> 프로젝트 구현 -> 검증/한계 흐름으로 쓴다.
- Kafka ordering, ACK, 성능 수치처럼 오해하기 쉬운 표현은 claim boundary를 함께 적는다.
- 각 글 끝에는 GitHub Repository와 다음 글 링크를 둔다.

## 참고 자료

- GitHub Repository: https://github.com/sjh9714/realtime-chat
- Architecture: https://github.com/sjh9714/realtime-chat/blob/main/docs/ARCHITECTURE.md
- WebSocket Measurement: https://github.com/sjh9714/realtime-chat/blob/main/docs/WEBSOCKET_MEASUREMENT.md
