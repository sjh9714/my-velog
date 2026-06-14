# [DAY9] [프로그래머스/Python] 완주하지 못한 선수 - dict로 이름별 개수 세기

## 문제 요약

마라톤에 참여한 선수들의 이름이 담긴 `participant`와 완주한 선수들의 이름이 담긴 `completion`이 주어진다.

완주하지 못한 선수는 단 한 명이고, 그 선수의 이름을 반환하면 된다.

문제 링크: [완주하지 못한 선수](https://school.programmers.co.kr/learn/courses/30/lessons/42576)

이 문제에서 중요한 조건은 동명이인이 있을 수 있다는 점이다.
그래서 단순히 이름이 있는지 없는지만 확인하면 안 되고, 이름별 개수를 세야 한다.

## Day3 때 놓쳤던 점 복습

Day3에 처음 이 문제를 풀 때는 `list.remove()`로 접근했다.

```python
def solution(participant, completion):
    for i in completion:
        participant.remove(i)
    return participant[0]
```

이 풀이는 작은 입력에서는 정답이 나온다.
하지만 `remove()`는 리스트에서 값을 찾기 위해 매번 앞에서부터 탐색한다.

그래서 완주자 목록을 돌 때마다 참가자 목록을 다시 찾게 되고, 입력이 커지면 `O(n^2)`에 가까워진다.
정확성 테스트는 통과했지만 효율성 테스트에서 실패한 이유가 여기에 있었다.

Day9에는 이 문제를 다시 보면서 “빠른 조회와 빈도 계산”이라는 해시의 관점으로 정리해보려고 한다.

## 이번에 작성한 dict 코드

이번에는 `Counter`를 쓰지 않고, `dict`로 이름별 개수를 직접 세었다.

```python
def solution(participant, completion):
    counts = {}

    for name in participant:
        counts[name] = counts.get(name, 0) + 1

    for name in completion:
        counts[name] -= 1

    for name, count in counts.items():
        if count > 0:
            return name
```

## 코드 설명

먼저 참가자 이름을 하나씩 보면서 몇 번 등장했는지 센다.

```python
counts[name] = counts.get(name, 0) + 1
```

예를 들어 참가자가 아래처럼 주어진다고 해보자.

```python
participant = ["mislav", "stanko", "mislav", "ana"]
```

참가자 목록을 모두 세고 나면 `counts`는 이런 의미가 된다.

```python
{
    "mislav": 2,
    "stanko": 1,
    "ana": 1,
}
```

그다음 완주자 이름을 보면서 개수를 하나씩 줄인다.

```python
for name in completion:
    counts[name] -= 1
```

완주한 사람은 참가자 목록에서 한 명씩 빠진다고 생각하면 된다.

마지막으로 아직 개수가 남아 있는 이름을 찾는다.

```python
for name, count in counts.items():
    if count > 0:
        return name
```

개수가 0보다 큰 이름이 완주하지 못한 선수다.

## 왜 `set`이 아니라 `dict`가 필요한가

처음 보면 참가자 목록과 완주자 목록을 비교하는 문제라서 `set`을 떠올릴 수 있다.
하지만 이 문제에는 동명이인이 있을 수 있다.

예를 들어 아래 입력을 보자.

```python
participant = ["mislav", "stanko", "mislav", "ana"]
completion = ["stanko", "ana", "mislav"]
```

`set`으로 바꾸면 참가자 목록은 이렇게 된다.

```python
{"mislav", "stanko", "ana"}
```

이렇게 되면 `"mislav"`가 2명 있었다는 정보가 사라진다.
따라서 존재 여부만 보는 `set`으로는 부족하다.

이 문제는 이름이 있는지 확인하는 문제가 아니라, 이름별 개수를 비교하는 문제다.
그래서 `dict`나 `Counter`처럼 빈도를 저장할 수 있는 자료구조가 필요하다.

## `dict.get(name, 0)`의 의미

`dict.get(name, 0)`은 딕셔너리에 `name`이 있으면 기존 값을 가져오고, 없으면 0을 반환한다.

```python
counts[name] = counts.get(name, 0) + 1
```

이 코드는 아래 의미다.

- 처음 보는 이름이면 `0 + 1`로 1을 저장한다.
- 이미 본 이름이면 기존 개수에 1을 더한다.

즉 이름이 처음 등장하는 경우와 이미 등장한 경우를 따로 `if`로 나누지 않아도 된다.

```python
if name not in counts:
    counts[name] = 0
counts[name] += 1
```

위 코드를 한 줄로 줄인 형태라고 생각하면 이해하기 쉽다.

## Counter 풀이와 dict 풀이 비교

`Counter`를 사용하면 참가자 이름별 개수 계산을 더 짧게 쓸 수 있다.

```python
from collections import Counter


def solution(participant, completion):
    counts = Counter(participant)

    for name in completion:
        counts[name] -= 1

    for name, count in counts.items():
        if count > 0:
            return name
```

`Counter`는 편리하지만, 핵심 아이디어는 `dict` 풀이와 같다.

- 참가자 이름별 개수를 센다.
- 완주자 이름의 개수를 줄인다.
- 남은 개수가 있는 이름을 찾는다.

이번 dict 풀이는 `Counter`를 직접 구현한 해시 풀이로 이해하면 된다.

## 테스트 케이스

| participant | completion | expected | 설명 |
|---|---|---|---|
| `["leo", "kiki", "eden"]` | `["eden", "kiki"]` | `"leo"` | 기본 예제 |
| `["marina", "josipa", "nikola", "vinko", "filipa"]` | `["josipa", "filipa", "marina", "nikola"]` | `"vinko"` | 미완주자가 중간에 있음 |
| `["mislav", "stanko", "mislav", "ana"]` | `["stanko", "ana", "mislav"]` | `"mislav"` | 동명이인 |
| `["alice", "bob", "charlie"]` | `["bob", "charlie"]` | `"alice"` | 첫 번째 선수가 미완주 |
| `["alice", "bob", "charlie"]` | `["alice", "bob"]` | `"charlie"` | 마지막 선수가 미완주 |
| `["a", "a", "a", "b"]` | `["a", "a", "b"]` | `"a"` | 같은 이름이 여러 번 등장 |

## 시간복잡도

시간복잡도는 `O(n)`이다.

참가자 목록을 한 번 순회하고, 완주자 목록을 한 번 순회한다.
마지막으로 `counts`에 남은 이름을 확인한다.

딕셔너리의 조회와 수정은 평균적으로 `O(1)`에 가깝기 때문에 전체 시간복잡도는 `O(n)`으로 볼 수 있다.

## 공간복잡도

공간복잡도는 `O(n)`이다.

참가자 이름별 개수를 저장하는 `counts` 딕셔너리가 필요하다.

## 배운 점

- 두 배열을 비교할 때 중복이 가능하면 개수를 세야 한다.
- `set`은 중복 정보를 없애므로 동명이인 문제에는 맞지 않을 수 있다.
- 이름별 개수나 빈도 계산은 `dict` 또는 `Counter`를 떠올리자.
- `dict.get(name, 0)`을 사용하면 처음 등장한 값도 자연스럽게 셀 수 있다.
- 효율성 테스트가 있는 문제에서는 리스트에서 매번 값을 찾는 `remove()`, `index()`, `in list`를 조심하자.

## 다음에 비슷한 문제를 만나면 떠올릴 신호

- “동명이인”, “중복”, “개수”가 나오면 `set`보다 `dict`를 먼저 생각하자.
- 두 리스트의 차이를 찾아야 하면 값별 개수를 세는 방식으로 접근하자.
- 빠른 조회가 필요하면 해시 기반 자료구조를 떠올리자.
- `Counter`를 써도 되지만, 직접 구현해야 한다면 `dict.get()`으로 빈도를 세자.

## 최종적으로 기억할 코드

```python
def solution(participant, completion):
    counts = {}

    for name in participant:
        counts[name] = counts.get(name, 0) + 1

    for name in completion:
        counts[name] -= 1

    for name, count in counts.items():
        if count > 0:
            return name
```

## 마무리

Day9 첫 번째 문제는 Day3에 풀었던 `완주하지 못한 선수`를 해시 관점으로 다시 정리한 문제였다.

처음에는 `Counter`가 더 편하게 느껴졌지만, `dict.get()`으로 직접 개수를 세어보니 해시 풀이의 구조가 더 분명하게 보였다.
참가자 이름별 개수를 세고, 완주자 이름을 하나씩 빼고, 마지막에 남은 이름을 찾는 흐름이다.

이번 복습을 통해 해시 문제의 핵심은 “빠른 조회”와 “빈도 계산”이라는 점을 다시 확인했다.
