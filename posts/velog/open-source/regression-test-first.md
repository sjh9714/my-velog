# [오픈소스 기여] Regression Test부터 쓰면 diff가 작아진다

## 들어가며

앞선 글에서는 버그를 고치기 전에 먼저 재현하는 과정이 중요하다고 적었다.

그 다음 단계는 재현한 실패를 테스트로 옮기는 일이다. 이때 regression test는 단순히 테스트 커버리지를 늘리는 장치가 아니었다. 내가 고치려는 행동을 정확히 고정하고, 수정 범위가 커지는 것을 막는 기준선에 가까웠다.

테스트가 없으면 수정 범위가 쉽게 커진다.

"이 조건도 같이 고치면 좋지 않을까", "여기 구조를 조금 정리하면 낫지 않을까", "비슷한 edge case도 처리하면 더 완성도 있지 않을까" 같은 생각이 계속 따라온다. 하지만 오픈소스 PR에서는 이런 확장이 항상 좋은 신호는 아니었다.

좋은 첫 PR은 보통 하나의 실패를 정확히 고치는 쪽에 가깝다.

실패하는 테스트를 먼저 만들면, 내가 고쳐야 할 문제가 문장보다 더 정확하게 남는다.

## 실패하는 테스트가 먼저다

regression test를 먼저 쓴다는 말은 거창한 TDD 의식처럼 들릴 수 있다.

하지만 실제로는 더 단순했다.

기존 코드에서 실패하는 입력을 테스트로 만들고, 그 테스트가 정말 실패하는지 확인한 뒤, 수정 후 같은 테스트가 통과하는지 확인하는 흐름이다.

이 과정에서 중요한 것은 "테스트를 추가했다"가 아니라 "수정 전에는 실패했다"는 점이다. 수정 전에도 통과하던 테스트라면, 그 테스트가 실제 버그를 고정하고 있는지 다시 봐야 한다.

내가 보려고 했던 신호는 대략 이렇다.

- 이 테스트는 이슈에 적힌 실패를 직접 표현하는가
- 기존 코드에서 실패하는가
- 수정 후에는 같은 테스트가 통과하는가
- 기존 동작 중 유지해야 할 것도 같이 보호하는가
- 테스트 때문에 production fix가 과하게 커지지는 않는가

특히 마지막 항목이 중요했다.

테스트를 먼저 쓰면 production code를 많이 고치고 싶은 마음을 줄일 수 있다. 테스트가 요구하는 행동만 맞추면 되기 때문이다.

## 어떤 테스트 형태를 고를까

회귀 테스트를 추가할 때 매번 같은 형태를 쓰지는 않았다.

프로젝트마다 기존 테스트 문화가 다르고, 버그가 드러나는 위치도 다르다. 그래서 새 테스트를 만들기 전에 먼저 기존 테스트를 읽었다.

lint rule이나 parser라면 fixture가 자연스러울 수 있다. 출력 형식까지 중요하다면 snapshot이 붙을 수 있다. 내부 함수의 작은 조건이라면 unit test가 낫다. 브라우저나 사용자 흐름이 문제라면 integration test가 필요할 수도 있다.

기준은 "가장 작은 테스트"였다.

작다는 것은 단순히 코드 줄 수가 적다는 뜻은 아니다. 실패를 가장 직접적으로 보여주고, 유지보수자가 기존 테스트 흐름 안에서 이해하기 쉬운 형태를 말한다.

예를 들어 lint rule 버그라면 새 테스트 프레임워크를 만들 필요가 없다. 기존 invalid fixture에 실패 코드를 넣고, valid fixture에 고치면 안 되는 코드를 넣고, snapshot을 갱신하는 편이 더 자연스럽다.

반대로 상태 관리 버그라면 fixture보다 unit test가 더 선명할 수 있다. 특정 queue에 어떤 payload가 들어 있고, 현재 identity가 바뀌었을 때 무엇을 retry하고 무엇을 drop해야 하는지 직접 확인하면 된다.

## 선택한 사례: Biome useOptionalChain fixture와 snapshot

대표적으로 기억에 남는 사례는 [biomejs/biome#10425](https://github.com/biomejs/biome/pull/10425)였다.

이 PR의 제목은 `fix(lint): detect optional-chain inequality guards`이고, 관련 이슈는 [biomejs/biome#10244](https://github.com/biomejs/biome/issues/10244)였다.

문제는 `lint/complexity/useOptionalChain` rule이 안전하게 optional chain으로 바꿀 수 있는 일부 negated guard inequality 형태를 잡지 못한다는 것이었다.

예를 들면 이런 형태다.

```text
!foo || foo.bar !== "x"
```

이 표현은 `foo`가 없으면 전체식이 `true`가 되고, `foo`가 있으면 `foo.bar !== "x"`를 평가한다. 그래서 안전한 경우에는 다음과 같은 optional chain 형태로 제안할 수 있다.

```text
foo?.bar !== "x"
```

여기서 중요한 것은 모든 비교식을 욕심내서 처리하지 않는 것이었다.

PR에서는 `!==`와 `!=`처럼 이 이슈에서 안전하게 설명할 수 있는 inequality 형태만 다뤘고, `===`, `==`, `<`, `>`, dynamic comparison value, `null`/`undefined` 비교, mismatched chain 같은 경우는 valid fixture에 넣어 report되지 않도록 했다.

즉 테스트는 두 방향으로 필요했다.

하나는 "이제 잡아야 하는 코드"였다.

```js
!foo || foo.bar !== "x";
!foo || foo.bar != "x";
```

다른 하나는 "여전히 건드리면 안 되는 코드"였다.

```js
!foo || foo.bar === "x";
!foo || foo.bar !== value;
!foo || foo.bar !== null;
!foo || bar.baz !== "x";
```

이런 rule 작업에서는 production code만 보면 범위를 넓히기 쉽다. 비슷해 보이는 logical expression을 더 많이 처리하고 싶어질 수 있다.

하지만 fixture를 먼저 나누면 선이 생긴다.

- invalid fixture: 이번 PR에서 새로 report해야 하는 코드
- valid fixture: 이번 PR에서 report하면 안 되는 코드
- snapshot: diagnostic과 fix가 실제로 어떻게 나오는지

이 구조 덕분에 PR의 범위도 분명해졌다.

변경 파일도 그에 맞게 좁게 유지할 수 있었다.

- `crates/biome_js_analyze/src/lint/complexity/use_optional_chain.rs`
- `crates/biome_js_analyze/tests/specs/complexity/useOptionalChain/invalidNegatedOrChain.js`
- `crates/biome_js_analyze/tests/specs/complexity/useOptionalChain/validNegatedOrChain.js`
- 관련 snapshot 파일
- changeset 파일

테스트 흐름도 fixture 중심이었다.

```bash
cargo test -p biome_js_analyze -- use_optional_chain --show-output
INSTA_UPDATE=always cargo test -p biome_js_analyze -- use_optional_chain --show-output
just test-lintrule useOptionalChain
cargo fmt --check
git diff --check
```

처음에는 새 fixture를 추가한 뒤 기존 구현에서 diagnostic이 나오지 않는 것을 확인했다. 그 다음 rule 코드를 수정하고 snapshot을 갱신했다.

snapshot이 있는 프로젝트에서는 업데이트 자체보다 업데이트 후 diff 확인이 더 중요했다. snapshot은 테스트 결과를 쉽게 갱신할 수 있다는 장점이 있지만, 의도하지 않은 diagnostic 변화까지 같이 들어갈 수 있기 때문이다.

이 PR에서는 generated snapshot의 diagnostic 출력 때문에 일반 `git diff --check`가 snapshot의 공백을 지적하는 상황도 있었다. 그래서 그 부분은 숨기지 않고, snapshot 테스트가 요구하는 출력임을 확인한 뒤 나머지 파일에 대해서도 별도로 diff check를 확인했다.

이런 검증 한계는 PR 본문에 짧게 남기는 편이 낫다. 완벽한 척하는 것보다 어떤 명령을 실행했고, 어떤 부분이 generated output 특성인지 적는 쪽이 리뷰하기 쉽다.

## 보조 사례: SitePing stale identity retry queue

다른 형태의 regression test로는 [NeosiaNexus/SitePing#95](https://github.com/NeosiaNexus/SitePing/pull/95)가 있었다.

관련 이슈는 [NeosiaNexus/SitePing#86](https://github.com/NeosiaNexus/SitePing/issues/86)이었다.

문제는 widget retry queue에 저장된 feedback payload가 sign-out이나 sign-in 변경 이후에도 이전 `authorName` / `authorEmail`로 다시 POST될 수 있다는 점이었다.

예를 들어 Alice로 작성하다가 네트워크 실패로 queue에 들어간 payload가 있고, 이후 Bob으로 다시 실행했을 때 Alice의 payload가 그대로 전송되면 안 된다. 이 문제는 UI보다 queue 처리 함수의 상태 조건으로 표현하는 편이 더 작았다.

그래서 테스트는 "현재 identity가 바뀐 경우"를 먼저 고정했다.

수정 전에는 다음 명령으로 새 regression test가 실패했다.

```bash
bun run test:run -- packages/widget/__tests__/widget/api-client.test.ts -t "stale"
```

실패 이유도 선명했다. 현재 identity가 Bob인데도 Alice의 queued payload가 fetch로 전송되고 있었다.

수정 후에는 다음 경우를 테스트로 나눴다.

- 현재 identity와 queued payload identity가 다르면 POST하지 않고 stale entry를 제거한다.
- 현재 identity와 queued payload identity가 같으면 정상적으로 retry한다.
- 다른 endpoint의 queue entry는 그대로 남긴다.
- identity를 넘기지 않는 기존 호출은 legacy behavior를 유지한다.

이렇게 테스트를 나누면 production change도 작아진다.

실제 변경은 `flushRetryQueue()`가 선택적으로 현재 identity를 받아 stale same-endpoint entry를 drop하도록 하는 정도였다. widget launcher는 `config.identity ?? getIdentity()`를 넘기도록 이어주었다. public config나 schema를 바꿀 필요는 없었다.

확인한 명령은 다음과 같았다.

```bash
bun run test:run -- packages/widget/__tests__/widget/api-client.test.ts -t "stale"
bun run test:run -- packages/widget/__tests__/widget/api-client.test.ts -t "flushRetryQueue|stale"
bun run test:run -- packages/widget/__tests__/widget/api-client.test.ts
bun run check
bun run build
bun run lint
git diff --check
```

이 사례는 fixture나 snapshot이 아니라 상태 기반 unit test가 더 맞는 경우였다. 문제는 화면에 보이는 문구가 아니라 queue에 남은 payload와 현재 identity의 관계였기 때문이다.

## 테스트가 diff를 작게 만드는 방식

regression test는 리뷰어에게도 신호를 준다.

"이 PR은 이 실패를 고친다"는 말을 코드로 보여주기 때문이다.

테스트가 없으면 리뷰어는 직접 상상해야 한다. 이 수정이 어떤 입력을 위한 것인지, 기존 동작을 깨지 않는지, 더 넓은 리팩터링이 필요한지 판단하기 어렵다.

반대로 테스트가 작게 들어가 있으면 diff를 읽는 순서가 단순해진다.

1. 새 테스트가 어떤 실패를 표현하는지 본다.
2. production change가 그 실패를 해결하는지 본다.
3. valid case나 기존 테스트가 유지되는지 본다.

이 흐름이 만들어지면 PR도 작아 보인다.

코드 줄 수가 적어서가 아니라, 변경의 목적이 작아졌기 때문이다.

나에게도 도움이 됐다. 테스트가 있으면 "여기까지 고치면 충분하다"는 기준이 생긴다. 그래서 관련 있어 보이는 리팩터링이나 추가 edge case를 다음 이슈로 미룰 수 있다.

오픈소스에서는 이 절제가 생각보다 중요했다.

## 주의할 점

regression test를 추가한다고 해서 항상 좋은 PR이 되는 것은 아니었다.

특히 조심하려고 한 부분이 몇 가지 있었다.

첫째, 기존 테스트를 약화하지 않는 것이다.

새 동작을 통과시키려고 기존 assertion을 느슨하게 만들면 오히려 신뢰가 떨어진다. 기존 테스트가 정말 잘못되었다면 PR 본문에서 왜 바꾸는지 설명해야 한다.

둘째, fixture 변경을 넓히지 않는 것이다.

fixture 기반 프로젝트에서는 작은 입력 하나만 바꾸려다가 주변 포맷이나 unrelated case가 같이 바뀌기 쉽다. 그래서 fixture와 snapshot diff는 직접 읽어야 한다.

셋째, snapshot은 반드시 확인해야 한다.

snapshot update 명령은 편하지만, 유지보수자가 보는 것은 최종 diff다. diagnostic message, range, suggestion, autofix output이 의도한 대로 바뀌었는지 봐야 한다.

넷째, 실행하지 않은 명령을 적지 않는 것이다.

PR 본문에 `npm test`나 `cargo test ./...`를 적었다면 실제로 실행했어야 한다. 시간이 오래 걸려서 못 했다면, 못 했다고 적는 편이 낫다.

검증하지 못한 부분은 숨기는 순간 리스크가 된다.

## 마무리

regression test는 "테스트를 하나 더 추가했다" 이상의 의미가 있었다.

재현한 실패를 코드로 고정하고, 수정 범위를 좁히고, 리뷰어가 PR을 읽는 순서를 만들어준다. 특히 첫 PR이나 작은 bugfix에서는 이 효과가 크다.

물론 모든 버그에 완벽한 regression test를 붙일 수 있는 것은 아니다. 하지만 가능한 범위에서 가장 작은 실패를 테스트로 남기면, PR은 훨씬 설명 가능해진다.

다음 글에서는 그 테스트를 통과시키기 위해 실제 production diff를 어떻게 작게 유지했는지 정리해보려고 한다. 작은 수정이 왜 유지보수자에게 큰 신뢰로 이어지는지, 그리고 unrelated formatting이나 lockfile 변경을 왜 피하려고 했는지 이야기해볼 생각이다.
