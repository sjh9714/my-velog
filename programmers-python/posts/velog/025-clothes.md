# [DAY10] [프로그래머스/Python] 의상 - 종류별 개수와 곱의 법칙으로 풀기

## 문제 요약

스파이가 가진 의상 목록 `clothes`가 주어진다.

각 의상은 `[옷 이름, 종류]` 형태로 주어진다.
매일 최소 한 개 이상의 의상을 입어야 하고, 서로 다른 의상 조합의 수를 구해야 한다.

문제 링크: [의상](https://school.programmers.co.kr/learn/courses/30/lessons/42578)

예를 들어 아래처럼 의상이 주어진다고 해보자.

```python
clothes = [
    ["yellow_hat", "headgear"],
    ["blue_sunglasses", "eyewear"],
    ["green_turban", "headgear"],
]
```

`headgear`는 2개, `eyewear`는 1개다.

각 종류에서 하나를 고르거나 아예 고르지 않을 수 있다.
다만 모든 종류를 고르지 않는 경우는 제외해야 한다.

## 처음 생각한 접근

처음에는 의상 종류별로 옷 이름을 모아야겠다고 생각했다.

같은 종류끼리 묶으면 각 종류마다 몇 개의 옷이 있는지 알 수 있고, 그 개수를 이용해 조합 수를 계산할 수 있다.

이 문제는 실제로 어떤 옷 이름을 선택하는지가 아니라, 종류별로 선택지가 몇 개인지가 핵심이었다.

## 내가 작성한 코드

```python
def solution(clothes):
    clothes_dict = {}
    for i in clothes:
        clothes_dict.setdefault(i[1], []).append(i[0])

    answer = 1
    for i in list(clothes_dict.values()):
        answer *= len(i) + 1

    return answer - 1
```

## 코드 설명

먼저 `clothes_dict`를 만들어 의상 종류별로 옷 이름을 모았다.

```python
clothes_dict.setdefault(i[1], []).append(i[0])
```

예를 들어 예제 입력을 처리하면 이런 형태가 된다.

```python
{
    "headgear": ["yellow_hat", "green_turban"],
    "eyewear": ["blue_sunglasses"],
}
```

그다음 각 종류별 옷 개수를 이용해 경우의 수를 곱했다.

```python
answer *= len(i) + 1
```

마지막에는 아무것도 입지 않는 경우를 빼기 위해 `answer - 1`을 반환했다.

## `setdefault()`의 의미

`setdefault(key, default)`는 딕셔너리에 `key`가 있으면 기존 값을 반환하고, 없으면 `default`를 넣은 뒤 그 값을 반환한다.

```python
clothes_dict.setdefault(i[1], []).append(i[0])
```

이 코드는 아래 흐름을 한 줄로 줄인 것과 비슷하다.

```python
if i[1] not in clothes_dict:
    clothes_dict[i[1]] = []

clothes_dict[i[1]].append(i[0])
```

종류별로 리스트를 만들고, 그 리스트에 옷 이름을 추가하는 구조다.

## 왜 `len(i) + 1`을 곱하는가

각 종류에서 할 수 있는 선택은 두 가지 방향으로 나뉜다.

- 그 종류의 옷 중 하나를 입는다.
- 그 종류의 옷을 입지 않는다.

예를 들어 `headgear`가 2개라면 선택지는 아래 3개다.

```text
yellow_hat
green_turban
입지 않음
```

그래서 옷 개수 2개에 “입지 않음” 1개를 더해 `2 + 1`이 된다.

즉 각 종류의 선택지 수는 `count + 1`이다.

## 마지막에 `-1`을 하는 이유

모든 종류에서 “입지 않음”을 선택하는 경우도 곱셈 과정에 포함된다.

하지만 문제에서는 최소 한 개 이상의 의상을 입어야 한다.

따라서 아무것도 입지 않는 경우 1개를 마지막에 빼야 한다.

```python
return answer - 1
```

이 `-1`을 빼먹으면 문제 조건을 만족하지 않는 조합까지 세게 된다.

## 개선해볼 수 있는 코드

내가 작성한 풀이는 종류별 옷 이름을 리스트로 저장했다.
하지만 실제 계산에 필요한 것은 옷 이름이 아니라 종류별 개수다.

그래서 리스트 대신 개수만 저장해도 된다.

```python
def solution_refactored(clothes):
    counts = {}

    for _, category in clothes:
        counts[category] = counts.get(category, 0) + 1

    answer = 1
    for count in counts.values():
        answer *= count + 1

    return answer - 1
```

이렇게 하면 의상 이름을 저장하지 않고도 같은 답을 구할 수 있다.

## 테스트 케이스

| clothes | expected | 설명 |
|---|---:|---|
| `[["yellow_hat", "headgear"], ["blue_sunglasses", "eyewear"], ["green_turban", "headgear"]]` | `5` | 공식 예제 |
| `[["crow_mask", "face"], ["blue_sunglasses", "face"], ["smoky_makeup", "face"]]` | `3` | 종류가 하나뿐인 경우 |
| `[["hat", "headgear"]]` | `1` | 옷이 하나뿐인 경우 |
| `[["hat", "headgear"], ["sunglasses", "eyewear"], ["shirt", "top"]]` | `7` | 각 종류에 하나씩 있는 경우 |
| `[["hat", "headgear"], ["cap", "headgear"], ["sunglasses", "eyewear"], ["glasses", "eyewear"], ["shirt", "top"]]` | `17` | 종류별 개수가 다른 경우 |

## 시간복잡도

시간복잡도는 `O(n)`이다.

의상 목록을 한 번 순회하면서 종류별로 묶고, 이후 종류 수만큼 다시 순회한다.
종류 수는 전체 의상 수보다 작거나 같으므로 전체 시간복잡도는 `O(n)`으로 볼 수 있다.

## 공간복잡도

공간복잡도는 `O(n)`이다.

내가 작성한 풀이는 종류별로 옷 이름 리스트를 저장하기 때문에 최악의 경우 전체 옷 이름을 모두 저장한다.

개선 풀이처럼 종류별 개수만 저장하면 공간은 `O(k)`로 볼 수 있다.
여기서 `k`는 의상 종류 수다.

## 배운 점

- 종류별 선택지를 계산할 때는 곱의 법칙을 떠올리자.
- “선택하지 않는 경우”가 가능하면 각 종류의 개수에 `+1`을 해준다.
- 단, 아무것도 선택하지 않는 경우가 문제 조건에 맞지 않으면 마지막에 `-1`을 한다.
- 실제 계산에 이름이 필요 없다면 리스트보다 개수만 저장하는 편이 더 단순하다.
- `setdefault()`는 딕셔너리 안에 리스트를 모을 때 유용하다.

## 다음에 비슷한 문제를 만나면 떠올릴 신호

- “종류별로 하나 선택”, “조합 수”, “최소 하나”가 나오면 곱의 법칙을 생각하자.
- 각 종류에서 선택하지 않는 경우가 있으면 `count + 1`을 곱하자.
- “아무것도 선택하지 않는 경우”가 불가능하면 마지막에 `-1`을 확인하자.
- 이름 자체가 필요하지 않으면 `dict`로 개수만 세자.

## 최종적으로 기억할 코드

```python
def solution(clothes):
    counts = {}

    for _, category in clothes:
        counts[category] = counts.get(category, 0) + 1

    answer = 1
    for count in counts.values():
        answer *= count + 1

    return answer - 1
```

## 마무리

의상 문제는 처음 보면 조합을 직접 만들어야 할 것처럼 보인다.

하지만 종류별 개수만 세고, 각 종류에서 입지 않는 경우까지 포함해 곱하면 훨씬 단순해진다.

이번 문제에서 기억할 핵심은 `count + 1`과 마지막 `-1`이다.
이 두 부분이 곱의 법칙과 문제 조건을 연결해주는 지점이었다.
