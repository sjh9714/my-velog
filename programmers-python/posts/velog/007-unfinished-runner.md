# [DAY3] [프로그래머스/Python] 완주하지 못한 선수 - list.remove 시간 초과와 Counter 풀이

## 문제 요약

마라톤에 참여한 선수들의 이름이 담긴 `participant` 배열과 완주한 선수들의 이름이 담긴 `completion` 배열이 주어진다.

완주하지 못한 선수는 단 한 명이다.
그 선수의 이름을 반환하면 된다.

문제 링크: [완주하지 못한 선수](https://school.programmers.co.kr/learn/courses/30/lessons/42576)

예를 들어 다음과 같은 입력이 있다.

```python
participant = ["leo", "kiki", "eden"]
completion = ["eden", "kiki"]
```

완주자 목록에 없는 선수는 `"leo"`이므로 정답은 `"leo"`다.

주의할 점은 동명이인이 있을 수 있다는 것이다.
그래서 이름이 존재하는지만 보는 `set` 방식으로는 부족하고, 이름별 개수를 세야 한다.

## 처음 작성한 코드

처음에는 완주한 선수 이름을 하나씩 보면서 참가자 목록에서 제거하면 된다고 생각했다.

```python
def solution(participant, completion):
    for i in completion:
        participant.remove(i)
    return participant[0]
```

흐름 자체는 단순하다.

1. `completion`을 순회한다.
2. 완주한 이름을 `participant`에서 제거한다.
3. 마지막에 남은 한 명을 반환한다.

작은 입력에서는 이 방식이 잘 동작한다.
그래서 정확성 테스트는 통과했다.

## 정확성은 통과했지만 효율성에서 실패한 이유

정확성 테스트는 통과했지만, `remove()`가 리스트를 매번 앞에서부터 찾기 때문에 전체적으로 O(n^2)에 가까워져 효율성 테스트에서 시간 초과가 났다.

`participant.remove(i)`는 리스트에서 `i`를 찾아서 제거한다.
문제는 리스트가 특정 값을 바로 찾을 수 있는 자료구조가 아니라는 점이다.

예를 들어 참가자가 100,000명이라면, `remove()`는 최악의 경우 리스트를 거의 끝까지 훑어야 한다.
이 작업을 완주자 수만큼 반복하면 시간이 크게 늘어난다.

즉 처음 풀이는 이런 구조였다.

```text
완주자 1명 확인 -> participant에서 이름 찾기
완주자 1명 확인 -> participant에서 이름 찾기
완주자 1명 확인 -> participant에서 이름 찾기
...
```

리스트에서 매번 찾는 비용이 반복되기 때문에 효율성 테스트에서 버티기 어렵다.

## list.remove()가 왜 느린지

리스트는 순서가 있는 자료구조다.
인덱스로 접근할 때는 빠르지만, 특정 값을 찾으려면 앞에서부터 비교해야 한다.

```python
participant.remove("leo")
```

이 코드는 내부적으로 `"leo"`가 어디 있는지 찾는다.
처음에 있으면 빨리 찾지만, 뒤쪽에 있으면 오래 걸린다.

그리고 값을 찾은 뒤 제거하면 뒤에 있던 원소들이 한 칸씩 앞으로 이동한다.
그래서 반복문 안에서 `remove()`를 계속 호출하는 방식은 입력이 커질수록 불리하다.

이번 문제는 효율성 테스트가 있는 문제라서, 리스트에서 매번 찾는 방식보다 이름별 개수를 빠르게 조회할 수 있는 자료구조가 필요했다.

## 해시/Counter로 생각 바꾸기

이 문제의 핵심은 이름별 개수다.

동명이인이 있을 수 있으므로 `set`만으로는 부족하고, 이름별 개수를 세는 `Counter`나 `dict`가 필요했다.

예를 들어 참가자가 다음과 같다고 해보자.

```python
participant = ["mislav", "stanko", "mislav", "ana"]
completion = ["stanko", "ana", "mislav"]
```

`"mislav"`는 참가자 목록에 2번 나오고, 완주자 목록에는 1번 나온다.
따라서 완주하지 못한 선수는 `"mislav"`다.

이런 경우에는 이름이 있는지 없는지가 아니라, 몇 번 등장했는지를 봐야 한다.

## 개선한 코드

`collections.Counter`를 사용하면 리스트 안의 값이 몇 번 등장하는지 쉽게 셀 수 있다.

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

## 개선 코드 설명

먼저 참가자 이름별 개수를 센다.

```python
counts = Counter(participant)
```

예를 들어 참가자가 다음과 같다면,

```python
["mislav", "stanko", "mislav", "ana"]
```

`counts`는 이런 의미가 된다.

```python
{
    "mislav": 2,
    "stanko": 1,
    "ana": 1
}
```

그다음 완주자 이름을 하나씩 보면서 개수를 1씩 줄인다.

```python
for name in completion:
    counts[name] -= 1
```

완주한 사람은 참가자 목록에서 한 명씩 빠진다고 생각하면 된다.

마지막으로 개수가 0보다 큰 이름을 찾는다.

```python
for name, count in counts.items():
    if count > 0:
        return name
```

끝까지 개수가 남아 있는 사람이 완주하지 못한 선수다.

## dict로 직접 풀어보기

`Counter`는 편리하지만, 내부적으로는 이름별 개수를 관리하는 해시 기반 자료구조라고 볼 수 있다.
같은 아이디어를 `dict`로 직접 구현할 수도 있다.

```python
def solution_with_dict(participant, completion):
    counts = {}

    for name in participant:
        counts[name] = counts.get(name, 0) + 1

    for name in completion:
        counts[name] -= 1

    for name, count in counts.items():
        if count > 0:
            return name
```

여기서 핵심은 `dict.get()`이다.

```python
counts[name] = counts.get(name, 0) + 1
```

`counts.get(name, 0)`은 `name`이 이미 딕셔너리에 있으면 기존 값을 가져오고, 없으면 0을 반환한다.
그래서 이름이 처음 등장하는 경우에도 자연스럽게 1부터 셀 수 있다.

## 테스트 케이스

| participant | completion | expected | 설명 |
|---|---|---|---|
| `["leo", "kiki", "eden"]` | `["eden", "kiki"]` | `"leo"` | 기본 예시 |
| `["marina", "josipa", "nikola", "vinko", "filipa"]` | `["josipa", "filipa", "marina", "nikola"]` | `"vinko"` | 완주하지 못한 선수가 중간에 있음 |
| `["mislav", "stanko", "mislav", "ana"]` | `["stanko", "ana", "mislav"]` | `"mislav"` | 동명이인 |
| `["alice", "bob", "charlie"]` | `["bob", "charlie"]` | `"alice"` | 첫 번째 선수가 미완주 |
| `["alice", "bob", "charlie"]` | `["alice", "bob"]` | `"charlie"` | 마지막 선수가 미완주 |
| `["a", "a", "a", "b"]` | `["a", "a", "b"]` | `"a"` | 같은 이름이 여러 번 등장 |

## 시간복잡도

개선 풀이의 시간복잡도는 `O(n)`이다.

`participant`를 한 번 순회하면서 이름별 개수를 세고, `completion`을 한 번 순회하면서 개수를 줄인다.
마지막으로 `counts`를 순회하면서 남은 사람을 찾는다.

각 이름의 조회와 수정은 해시 기반으로 평균 `O(1)`에 가깝다.
따라서 전체 시간복잡도는 `O(n)`으로 볼 수 있다.

처음 작성한 `remove()` 풀이는 반복문 안에서 리스트 탐색이 발생한다.
그래서 입력이 커지면 `O(n^2)`에 가까워질 수 있다.

## 공간복잡도

공간복잡도는 `O(n)`이다.

참가자 이름별 개수를 저장하는 `Counter` 또는 `dict`가 필요하기 때문이다.

## 배운 점

- 정확성 테스트를 통과해도 효율성 테스트에서 실패할 수 있다.
- `list.remove()`는 특정 값을 찾기 위해 리스트를 앞에서부터 탐색한다.
- 반복문 안에서 `remove()`를 사용하면 입력이 커질 때 시간 초과가 날 수 있다.
- 동명이인이 있는 문제는 `set`이 아니라 개수를 세는 자료구조가 필요하다.
- 이름별 개수, 빈도, 중복 처리가 나오면 `Counter` 또는 `dict`를 먼저 떠올리자.

## 다음에 비슷한 문제를 만나면 떠올릴 신호

- 두 배열을 비교하면서 빠진 값을 찾는 문제라면 해시를 먼저 생각하자.
- 중복 이름이나 중복 값이 가능하면 `set`만으로 충분한지 의심하자.
- 값별 등장 횟수가 필요하면 `Counter`나 `dict.get()`을 떠올리자.
- 효율성 테스트가 있는 문제에서는 반복문 안의 `remove()`, `in list`, `index()`를 조심하자.

## 최종적으로 기억할 코드

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

## 마무리

이번 문제는 정답 자체보다 효율성 테스트에서 왜 실패했는지를 이해하는 게 더 중요했다.

처음 작성한 `remove()` 풀이는 작은 입력에서는 직관적이고 정답도 잘 나온다.
하지만 입력이 커지면 리스트에서 매번 값을 찾는 비용 때문에 시간 초과가 발생한다.

Day3의 주제가 `dict`, `set` 입문인 만큼, 이번 문제를 통해 해시 기반 자료구조가 왜 필요한지 확실히 느낄 수 있었다.
다음에 비슷한 문제를 만나면 먼저 “값의 존재 여부를 볼 것인가, 등장 횟수를 셀 것인가”부터 생각해봐야겠다.
