# [오픈소스 기여] 좋은 첫 PR은 작지만 선명하다

## 들어가며

첫 오픈소스 PR을 준비할 때 가장 먼저 고민한 것은 "무엇을 고칠 것인가"였다.

처음에는 자연스럽게 유명한 저장소나 큰 기능 개선에 눈이 갔다. 하지만 실제로 후보를 살펴보면, 첫 PR로 좋은 이슈는 크고 화려한 이슈가 아니었다. 오히려 작고, 재현 가능하고, 테스트로 고정할 수 있는 문제가 더 좋은 출발점이었다.

큰 기능 추가는 설계 판단이 많다. 프로젝트의 방향, API 호환성, 유지보수자의 선호, 문서화 범위까지 같이 따라온다. 반면 작은 버그는 현재 동작과 기대 동작이 비교적 분명하다. 그래서 PR의 범위를 좁게 유지하기 좋고, 리뷰어도 "이 변경이 왜 필요한지"를 빠르게 판단할 수 있다.

좋은 첫 PR은 큰 개선보다 작은 재현 가능한 버그에서 시작하는 편이 낫다고 느꼈다.

## 좋은 첫 PR의 조건

내가 이슈를 고를 때 가장 먼저 본 것은 재현 가능성이었다.

이슈 본문에 입력값, 명령어, 에러 로그, 기대 결과가 있으면 시작하기 좋다. 반대로 "가끔 안 된다", "이상하게 동작한다"처럼 증상이 넓게만 적혀 있으면 첫 PR로는 부담이 커진다. 버그가 실제로 남아 있는지부터 확인하기 어렵고, 고쳤다고 말하기도 조심스럽기 때문이다.

두 번째 기준은 테스트 가능성이었다.

좋은 이슈는 실패 조건을 작은 테스트로 분리할 수 있다. CLI라면 최소 명령어와 출력이 있고, parser라면 작은 입력 문자열이 있고, 라이브러리라면 특정 함수 호출 결과가 있다. 이런 경우에는 수정 전 실패하는 테스트를 만들고, 수정 후 같은 테스트가 통과하는지 확인하는 흐름을 만들기 쉽다.

세 번째는 중복 PR 여부였다.

좋아 보이는 이슈라도 이미 누군가 같은 문제를 고치고 있다면 들어가지 않는 편이 낫다. open PR이 직접 issue를 닫고 있거나, 같은 파일과 같은 실패 경로를 다루고 있다면 사실상 경합이 된다. 이런 경우에는 새 PR을 여는 것보다 다른 이슈를 찾는 쪽이 유지보수자에게도 낫다.

네 번째는 저장소의 기여 정책이었다.

기여 가이드, PR 템플릿, 테스트 명령, 라이선스, CLA나 DCO, AI-assisted contribution 정책을 먼저 확인했다. 특히 AI 사용을 금지하거나 제한하는 저장소라면 기술적으로 고칠 수 있는 문제가 있어도 진행하지 않는 것이 맞다. 오픈소스 기여는 코드를 맞히는 일만이 아니라, 프로젝트의 규칙을 지키는 일이기도 했다.

## 체크리스트로 먼저 걸러보기

후보 이슈를 찾으면 바로 코드를 고치기보다 간단한 체크리스트를 먼저 봤다.

- 라이선스가 명확한가
- `CONTRIBUTING` 문서가 있는가
- PR 템플릿이나 issue 템플릿이 있는가
- 테스트 명령이 문서화되어 있는가
- 어떤 package manager를 쓰는지 분명한가
- lockfile이나 generated file을 건드리지 않아도 되는가
- CLA나 DCO가 필요한가
- AI-assisted contribution 정책이 있는가
- 같은 이슈를 해결하는 open PR이 없는가

이 체크리스트는 시간을 아끼는 장치였다.

어떤 이슈는 기술적으로 좋아 보여도 테스트 환경이 너무 크거나, 외부 계정이 필요하거나, 이미 다른 PR이 거의 해결 중이었다. 그런 경우에는 아깝더라도 넘겼다. 첫 PR에서 중요한 것은 어려운 문제를 억지로 잡는 것이 아니라, 내가 끝까지 재현하고 설명할 수 있는 문제를 고르는 것이었다.

## 선택한 사례: pipx app script shebang isolation

좋은 예시 중 하나가 [pypa/pipx#1819](https://github.com/pypa/pipx/pull/1819)였다.

이 PR의 제목은 `Fix app script shebang isolation`이고, 관련 이슈는 [pypa/pipx#1584](https://github.com/pypa/pipx/issues/1584)였다. 문제는 pipx가 설치한 Python app script가 실행될 때, 호출하는 쪽의 `PYTHONPATH` 영향을 받을 수 있다는 점이었다.

이슈 자체가 첫 PR 후보로 괜찮았던 이유는 비교적 분명했다.

- 문제 상황이 사용자 환경 변수와 app script 실행 경로로 좁혀져 있었다.
- 기대 동작은 app 실행이 ambient `PYTHONPATH`에 흔들리지 않는 것이었다.
- 수정 범위가 app script를 노출하는 코드 경로로 제한될 수 있었다.
- 회귀 테스트를 통해 "설치된 app script가 환경 변수 영향을 무시하는지" 확인할 수 있었다.

실제 변경도 넓지 않았다.

PR에서는 `src/pipx/commands/common.py`, `tests/test_common.py`, `changelog.d/1584.bugfix.md`만 바뀌었다. 핵심 수정은 non-Windows app script의 직접 Python shebang에 `-E`를 넣어, Python이 환경 변수 영향을 무시하도록 만드는 것이었다.

중요한 점은 이 PR이 "pipx의 실행 환경을 전부 다시 설계한다"가 아니었다는 것이다. 기존 symlink/copy 흐름은 유지하고, manual page나 non-Python executable, 이미 인자를 가진 shebang, Windows launcher는 건드리지 않았다. 전체 리팩터링보다 유지보수자가 빠르게 리뷰할 수 있는 최소 변경을 우선한 셈이다.

테스트도 PR의 설득력을 만드는 부분이었다.

PR 본문에는 다음 흐름이 남아 있었다.

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

그리고 새 regression test는 수정 전에는 실패했다. exposed app script가 원래 shebang을 유지해서 `-E`가 들어가지 않았기 때문이다.

이런 기록이 있으면 리뷰어 입장에서도 PR을 훨씬 빨리 볼 수 있다. 어떤 문제가 있었고, 어떤 범위만 바꿨고, 어떤 명령으로 확인했는지가 한눈에 들어오기 때문이다.

## 하지 않기로 한 후보들

반대로 하지 않기로 결정한 후보들도 있었다.

첫 번째는 AI-assisted contribution을 금지하는 저장소였다. 기술적으로는 고칠 수 있는 작은 버그가 있어도, 프로젝트가 그런 방식의 기여를 받지 않겠다고 명시했다면 멈추는 게 맞다. 기여 정책을 우회하거나 표현만 바꿔서 들어가는 것은 좋은 기여가 아니다.

두 번째는 이미 open PR이 같은 문제를 해결 중인 이슈였다. 이 경우 새 PR을 만들면 유지보수자는 같은 문제를 두 번 비교해야 한다. 내가 더 빨리 고칠 수 있을 것 같다는 생각보다, 이미 진행 중인 기여를 존중하는 쪽이 낫다.

세 번째는 테스트 경로가 불명확한 이슈였다. 재현에 유료 서비스, private credential, 특정 운영 환경이 필요하면 첫 PR로는 위험했다. 그런 이슈를 고치려면 추측이 많이 들어가고, 검증하지 못한 부분을 숨기기 쉬워진다.

하지 않는 결정도 중요했다.

오픈소스 기여를 하다 보면 "이 정도면 고칠 수 있을 것 같은데" 싶은 후보가 많다. 하지만 좋은 PR은 고칠 수 있는 문제보다 설명할 수 있는 문제에서 나온다고 느꼈다.

## 좋은 이슈는 PR 본문까지 상상된다

이슈를 고를 때 도움이 됐던 기준이 하나 더 있다.

후보를 봤을 때 PR 본문이 대략 상상되면 좋은 신호였다.

예를 들면 이런 식이다.

```text
Before: 특정 입력에서 기존 동작이 잘못됐다.
After: 같은 입력에서 기대 동작을 반환한다.
Testing: 이 실패 조건을 고정한 regression test와 관련 테스트를 실행했다.
```

반대로 PR 본문이 계속 흐릿하다면 아직 문제가 충분히 좁혀지지 않은 경우가 많았다. "어딘가 이상하다", "전반적으로 개선했다", "관련 코드를 정리했다" 같은 설명밖에 떠오르지 않는다면 첫 PR로는 조금 위험했다.

좋은 첫 PR은 작지만 선명하다.

바꾸는 줄 수가 적어서 선명한 것이 아니라, 어떤 행동 하나가 어떻게 달라지는지 설명할 수 있어서 선명하다.

## 마무리

첫 PR을 고를 때 중요한 것은 큰 저장소에서 큰 문제를 고르는 것이 아니었다.

내가 재현할 수 있고, 테스트로 고정할 수 있고, 기존 코드 흐름 안에서 작게 고칠 수 있는 문제를 찾는 것이 더 중요했다. 그리고 그 과정에서 하지 않을 후보를 걸러내는 판단도 기여의 일부였다.

다음 글에서는 이 기준으로 고른 이슈를 실제로 어떻게 재현하는지 정리해보려고 한다. 버그를 고치기 전에 실패를 내 손으로 확인하는 과정이 왜 PR의 절반에 가까운지 이야기해볼 생각이다.
