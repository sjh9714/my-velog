# 완주하지 못한 선수

## 문제 요약

마라톤에 참여한 선수 배열 `participant`와 완주한 선수 배열 `completion`이 주어진다.
완주하지 못한 선수는 한 명이며, 그 선수의 이름을 반환해야 한다.

동명이인이 있을 수 있으므로 이름이 한 번 등장했는지만 보면 안 되고, 이름별 개수를 함께 관리해야 한다.

문제 링크: https://school.programmers.co.kr/learn/courses/30/lessons/42576

## 접근 방식

처음에는 완주자 이름을 하나씩 보면서 `participant.remove(name)`으로 참가자 목록에서 제거했다.
정확성 테스트는 통과했지만, `remove()`가 리스트에서 값을 찾기 위해 매번 앞에서부터 탐색하므로 효율성 테스트에서 시간 초과가 발생했다.

개선 풀이에서는 `Counter`로 참가자 이름별 개수를 세고, 완주자 이름을 하나씩 빼서 최종적으로 개수가 남아 있는 사람을 찾았다.

## 핵심 코드

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

## 시간복잡도

O(n)

`participant`를 한 번 순회하고, `completion`을 한 번 순회한다.
이름별 개수 조회와 수정은 평균적으로 `O(1)`이므로 전체 시간복잡도는 `O(n)`이다.

처음 작성한 `remove()` 풀이는 완주자마다 리스트를 탐색하므로 전체적으로 `O(n^2)`에 가까워질 수 있다.

## 공간복잡도

O(n)

참가자 이름별 개수를 저장하는 `Counter` 또는 `dict`가 필요하다.

## 배운 점

- `list.remove(value)`는 값을 찾기 위해 리스트를 순회한다.
- 반복문 안에서 `remove()`를 사용하면 입력이 커질 때 쉽게 시간 초과가 날 수 있다.
- 동명이인이 있는 문제는 `set`만으로는 부족하고, 이름별 개수를 세는 `Counter`나 `dict`가 필요하다.
- 효율성 테스트가 있는 문제는 입력 크기와 자료구조 선택을 먼저 확인하자.
