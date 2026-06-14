# [오픈소스 기여] 작은 수정, 큰 신뢰: 유지보수자가 좋아하는 diff 만들기

## 들어가며

앞선 글에서는 재현한 실패를 regression test로 옮기면 diff가 작아진다고 적었다.

이번 글은 그 다음 이야기다. 테스트가 실패를 고정해주더라도, 실제 수정 과정에서는 여전히 범위가 커질 수 있다. 관련 있어 보이는 구조를 정리하고 싶어지고, 비슷한 edge case를 더 처리하고 싶어지고, 파일을 열어본 김에 오래된 코드 스타일도 바꾸고 싶어진다.

하지만 오픈소스 PR에서 작은 diff는 꽤 중요한 신뢰 신호였다.

작은 diff는 단순히 코드 줄 수가 적다는 뜻이 아니다. 이 PR이 어떤 행동 하나를 바꾸는지 리뷰어가 빠르게 이해할 수 있다는 뜻에 가깝다.

내가 고치려는 실패가 하나라면, PR도 그 실패 하나를 중심으로 설명되어야 했다.

## 한 PR에는 하나의 행동 변화

작은 PR을 만들 때 가장 먼저 정한 기준은 "한 PR에 하나의 행동 변화만 담기"였다.

예를 들어 어떤 CLI 버그를 보다가 내부 helper 이름이 마음에 들지 않을 수 있다. 테스트를 읽다가 fixture 정리가 필요해 보일 수도 있다. 오래된 formatter 결과가 눈에 밟힐 수도 있다.

그런데 이런 변경이 bugfix와 함께 들어가면 리뷰어 입장에서는 질문이 많아진다.

- 이 rename은 버그 수정에 필요한가
- formatter 변경 때문에 실제 로직 변경이 숨어 있지는 않은가
- lockfile 변경은 의도한 것인가
- 기존 API나 설정 의미가 바뀐 것은 아닌가

작은 diff는 이런 질문을 줄인다.

PR을 읽는 사람이 "이 변경은 이 실패를 고치기 위한 것이구나"라고 바로 이해할 수 있으면 리뷰가 훨씬 쉬워진다.

그래서 작업할 때는 자주 되물었다.

이 줄은 이번 이슈를 고치는 데 필요한가?

대답이 애매하면 빼는 편이 나았다.

## diff를 키우는 흔한 이유

diff가 커지는 이유는 대부분 악의가 아니라 성실함에서 온다.

이왕 보는 김에 더 깨끗하게 만들고 싶고, 비슷한 문제도 같이 고치고 싶고, 주변 테스트도 정리하고 싶어진다. 하지만 첫 PR이나 좁은 bugfix에서는 이 성실함이 오히려 리뷰 비용을 키울 수 있다.

특히 조심하려고 한 것은 네 가지였다.

첫째, unrelated refactor를 넣지 않는 것이다.

함수 분리나 이름 변경이 bugfix를 더 선명하게 만들 때도 있다. 하지만 동작을 바꾸지 않는 정리는 별도 PR이 더 낫다. bugfix PR에서는 원인과 수정이 한눈에 보여야 한다.

둘째, formatter churn을 피하는 것이다.

파일 전체 formatting이 바뀌면 실제 수정 줄을 찾기 어렵다. 프로젝트가 formatter를 요구한다면 필요한 파일에만 적용하고, 그렇지 않다면 주변 줄을 괜히 건드리지 않는 편이 낫다.

셋째, dependency와 lockfile 변경을 조심하는 것이다.

버그 수정에 새 dependency가 꼭 필요한 경우는 생각보다 적었다. lockfile이 바뀌면 유지보수자는 "이게 필요한 변경인가"를 별도로 봐야 한다. 의도한 dependency 변경이 아니라면 PR에 들어가지 않게 확인해야 한다.

넷째, generated file을 조심하는 것이다.

snapshot이나 fixture output처럼 프로젝트가 요구하는 generated file은 포함해야 할 수 있다. 하지만 그 경우에도 diff를 직접 읽고, 의도한 출력만 바뀌었는지 확인해야 한다.

작은 PR은 "아무것도 안 바꿨다"가 아니다. 필요한 것만 바꾸는 쪽에 가깝다.

## 선택한 사례: yazi preview cache directory permission

작은 diff의 의미를 잘 보여준 사례 중 하나가 [sxyazi/yazi#3984](https://github.com/sxyazi/yazi/pull/3984)였다.

이 PR의 제목은 `fix: restrict preview cache directory permissions`이고, 관련 이슈는 [sxyazi/yazi#3983](https://github.com/sxyazi/yazi/issues/3983)이었다.

문제는 preview cache directory 권한이었다. preview cache는 사용자 파일에서 파생된 내용을 담을 수 있는데, 기본 cache directory가 Unix 환경에서 다른 사용자에게 읽힐 수 있는 권한으로 남을 수 있었다.

여기서 넓게 고치려면 여러 방향이 가능했다.

- cache directory 위치를 바꾼다.
- 설정 옵션을 새로 만든다.
- XDG runtime directory를 우선하도록 정책을 바꾼다.
- preview cache 전체 흐름을 다시 설계한다.

하지만 이슈를 해결하는 데 필요한 핵심은 더 작았다.

기존 cache path와 config 의미는 유지하고, Unix에서 cache directory를 만들거나 확인할 때 owner-only permission인 `0700`을 보장하는 것이다.

그래서 PR의 설명도 이 방향에 맞췄다.

사용자에게 보이는 경로나 설정 의미를 바꾸지 않고, Unix cache directory setup에서 최종 directory permission을 제한한다. Windows 동작은 그대로 둔다.

이렇게 scope가 좁아지면 테스트도 좁아진다.

Unix-only regression test는 기존 `0755` cache directory를 만든 뒤 helper를 실행하고, 최종 mode가 `0700`이 되는지 확인하면 된다. 테스트가 요구하는 행동이 작으니 production change도 그 안에 머물 수 있었다.

검증 명령도 그 범위에서 출발했다.

```bash
cargo test -p yazi-config create_cache_dir_restricts_permissions_on_unix
cargo test -p yazi-config
cargo test --workspace --verbose
cargo +nightly-2026-05-06 fmt --check
git diff --check
```

이 사례에서 배운 점은 보안 관련 이슈라고 해서 항상 큰 설계 변경이 필요한 것은 아니라는 점이었다.

물론 장기적으로 더 좋은 cache 위치 정책이 있을 수 있다. 하지만 그 PR에서 해결하려는 것은 "현재 default cache directory가 안전한 permission으로 준비되는가"였다. 그 질문에 답하는 diff가 가장 리뷰하기 쉬웠다.

## 보조 사례: pipx shebang isolation

비슷하게 작은 행동 변화가 중요했던 사례로 [pypa/pipx#1819](https://github.com/pypa/pipx/pull/1819)가 있었다.

이 PR의 제목은 `Fix app script shebang isolation`이고, 관련 이슈는 [pypa/pipx#1584](https://github.com/pypa/pipx/issues/1584)였다.

문제는 pipx가 설치한 Python app script가 실행될 때, 호출자의 ambient `PYTHONPATH` 영향을 받을 수 있다는 점이었다. 그러면 앱 내부 모듈보다 외부 환경의 모듈이 먼저 잡히는 식의 문제가 생길 수 있다.

여기서도 고칠 수 있는 범위는 넓어 보였다.

script generation 전체를 다시 보거나, 설치 방식 전반을 바꾸거나, 모든 platform launcher를 함께 건드릴 수도 있다.

하지만 PR은 더 좁은 방향을 택했다.

non-Windows app script 중 direct Python shebang을 가진 경우에 `-E`를 넣어 Python environment variables를 무시하도록 한다. symlink/copy behavior는 유지하고, manual page나 non-Python executable, 기존 shebang에 arguments가 있는 경우, Windows launcher는 건드리지 않는다.

이렇게 "바꾸는 것"과 "바꾸지 않는 것"을 같이 적으면 PR이 훨씬 안정적으로 보인다.

테스트도 그 경계에 맞춰졌다.

```bash
uv run --group test pytest tests/test_common.py -k ignores_pythonpath --net-pypiserver -q
uv run --group test pytest tests/test_common.py --net-pypiserver -q
uv run --group test pytest tests/test_install.py -k 'test_install_easy_packages' -q
uv run --group lint pre-commit run ruff-check --files src/pipx/commands/common.py tests/test_common.py
uv run --group lint pre-commit run ruff-format --files src/pipx/commands/common.py tests/test_common.py
uv run --group lint pre-commit run --all-files
python3 -m py_compile src/pipx/commands/common.py tests/test_common.py
git diff --check
```

여기서 좋은 점은 PR이 "pipx script isolation을 전반적으로 개선한다"라고 말하지 않았다는 것이다.

대신 "ambient `PYTHONPATH`가 app script 실행에 영향을 주는 문제를, direct Python shebang에 `-E`를 추가해 막는다"라고 설명했다. 유지보수자는 이 범위를 기준으로 diff와 테스트를 읽을 수 있다.

## PR 본문도 diff의 일부다

작은 diff를 만들었다면 PR 본문도 그 크기에 맞춰야 한다.

내부 작업 로그를 길게 쓰는 것보다, 유지보수자가 판단해야 하는 정보를 앞에 놓는 편이 좋았다.

보통 다음 항목을 넣으려고 했다.

- 어떤 동작이 실패했는지
- 무엇을 바꿨는지
- 왜 이 변경이 좁고 안전한지
- 관련 issue
- 실행한 테스트 명령
- 검증하지 못한 부분

특히 "검증하지 못한 부분"은 숨기지 않는 편이 낫다.

full test suite가 너무 오래 걸려서 못 돌렸다면 못 돌렸다고 적는다. 특정 OS에서만 재현되는 문제를 로컬에서 완전히 확인하지 못했다면 그 한계를 적는다. CI가 외부 서비스 문제로 실패했다면 그 로그를 보고 PR diff와 관련 있는지 구분한다.

이런 문장은 PR을 약하게 만드는 것이 아니라 오히려 리뷰를 쉽게 만든다.

리뷰어가 다시 물어볼 질문을 미리 줄여주기 때문이다.

## 리뷰 대응도 작게 한다

작은 diff는 PR을 올린 뒤에도 유지해야 했다.

리뷰 코멘트를 받으면 방어적으로 설명하고 싶어질 때가 있다. 하지만 대부분은 요구사항을 다시 좁히는 것이 먼저였다.

리뷰어가 "이 부분은 너무 넓다"고 하면, 그 말은 보통 PR을 더 작게 만들 기회였다. 내가 생각한 안전장치가 유지보수자에게는 불필요한 확장으로 보일 수 있다.

그래서 follow-up commit도 작게 유지하려고 했다.

- 요청받은 줄만 고친다.
- 새 테스트가 필요하면 그 코멘트와 직접 연결된 테스트만 추가한다.
- unrelated cleanup을 끼워 넣지 않는다.
- 리뷰 답변에는 무엇을 바꿨고 어떤 테스트를 돌렸는지만 짧게 적는다.

좋은 리뷰 대응은 논쟁에서 이기는 것이 아니라, PR의 목적을 더 선명하게 만드는 데 가까웠다.

## 작은 diff 체크리스트

PR을 열기 전에는 마지막으로 이런 식으로 확인했다.

- 이 PR은 하나의 issue나 행동 변화만 다루는가
- 새 테스트가 실패를 직접 표현하는가
- production change가 테스트가 요구하는 범위 안에 있는가
- formatter가 unrelated line을 바꾸지 않았는가
- dependency나 lockfile 변경이 의도된 것인가
- generated file diff를 직접 읽었는가
- PR 본문에 실행한 명령만 적었는가
- 검증하지 못한 부분을 숨기지 않았는가

이 체크리스트는 완벽한 PR을 만들기 위한 것이 아니었다.

리뷰어가 불필요하게 의심해야 하는 지점을 줄이기 위한 장치에 가까웠다.

## 마무리

작은 수정은 소극적인 태도가 아니었다.

오히려 문제를 정확히 이해했을 때 가능한 선택에 가까웠다. 무엇을 바꿔야 하는지 알고, 무엇을 바꾸지 않아야 하는지도 아는 상태가 작은 diff로 나타난다.

오픈소스 PR에서는 이 점이 특히 중요했다.

유지보수자는 낯선 contributor의 PR을 읽는다. 그때 작은 diff, 실패를 고정한 테스트, 검증 명령, 명확한 scope는 신뢰를 만든다.

큰 변경보다 작은 설명 가능한 변경을 먼저 만드는 것.

이 시리즈를 쓰면서 가장 많이 확인한 기준도 결국 그쪽이었다.
