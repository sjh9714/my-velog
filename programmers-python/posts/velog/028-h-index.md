# [DAY12] [프로그래머스/Python] H-Index - 내림차순 정렬과 citation >= i 이해하기

## 문제 요약

논문의 인용 횟수 목록 `citations`가 주어진다.

H-Index는 어떤 연구자가 발표한 논문 중 `h`번 이상 인용된 논문이 `h`편 이상일 때, 가능한 `h`의 최댓값이다.

문제 링크: [H-Index](https://school.programmers.co.kr/learn/courses/30/lessons/42747)

예를 들어 아래 입력이 있다고 해보자.

```python
citations = [3, 0, 6, 1, 5]
```

이 연구자는 3회 이상 인용된 논문이 3편 있다.

```text
6, 5, 3
```

하지만 4회 이상 인용된 논문은 2편뿐이다.
그래서 H-Index는 `3`이다.

## 처음 생각한 접근

처음에는 H-Index의 정의가 조금 헷갈렸다.

핵심은 “몇 번 인용됐는가”와 “그런 논문이 몇 편 있는가”를 동시에 봐야 한다는 점이다.

그래서 인용 횟수가 큰 논문부터 확인하면 좋겠다고 생각했다.
인용 횟수를 내림차순으로 정렬하면, 앞에서부터 `i`번째까지는 현재 보고 있는 논문보다 인용 횟수가 크거나 같다.

즉 `i`번째 논문의 인용 횟수가 `i` 이상이면, 최소 `i`편의 논문이 `i`회 이상 인용되었다고 볼 수 있다.

## 내가 작성한 코드

```python
def solution(citations):
    citations.sort(reverse=True)

    answer = 0
    for i, citation in enumerate(citations, start=1):
        if citation >= i:
            answer = i

    return answer
```

## 코드 설명

먼저 인용 횟수를 내림차순으로 정렬했다.

```python
citations.sort(reverse=True)
```

예제 입력은 아래처럼 바뀐다.

```python
[6, 5, 3, 1, 0]
```

그다음 `enumerate(citations, start=1)`로 논문 순서를 1부터 세었다.

```python
for i, citation in enumerate(citations, start=1):
```

여기서 `i`는 현재까지 확인한 논문 수라고 볼 수 있다.

조건은 이 부분이다.

```python
if citation >= i:
    answer = i
```

내림차순 정렬 상태에서 `i`번째 논문의 인용 수가 `i` 이상이라면, 앞의 `i`개 논문은 모두 `i`회 이상 인용된 논문이다.

그래서 그때의 `i`는 가능한 H-Index 후보가 된다.
더 큰 값이 가능할 수도 있으므로 조건을 만족할 때마다 `answer`를 갱신했다.

## H-Index를 쉽게 이해하기

H-Index를 말로만 보면 조금 복잡하다.

나는 이렇게 이해했다.

```text
h번 이상 인용된 논문이 h편 이상 있는가?
```

예를 들어 H-Index가 3이라는 말은 아래 뜻이다.

```text
3번 이상 인용된 논문이 최소 3편 있다.
```

H-Index가 4가 되려면 아래 조건을 만족해야 한다.

```text
4번 이상 인용된 논문이 최소 4편 있다.
```

예제에서는 4번 이상 인용된 논문이 `6`, `5` 두 편뿐이라서 4는 불가능하다.

## 왜 내림차순 정렬을 하는가

내림차순 정렬을 하면 인용 횟수가 많은 논문부터 볼 수 있다.

```python
[6, 5, 3, 1, 0]
```

이 상태에서 3번째 논문을 보고 있다고 해보자.

```text
1번째: 6회
2번째: 5회
3번째: 3회
```

3번째 논문의 인용 횟수가 3 이상이다.
그러면 앞의 논문들은 더 많이 인용되었으므로, 최소 3편의 논문이 3회 이상 인용되었다고 말할 수 있다.

정렬을 해두면 `몇 편 이상인가`를 인덱스 하나로 확인할 수 있어서 조건이 단순해진다.

## 왜 `citation >= i`이면 answer를 갱신하는가

`i`는 현재까지 확인한 논문 수다.
`citation`은 그 `i`번째 논문의 인용 횟수다.

내림차순 정렬 상태에서 아래 조건이 참이라고 해보자.

```python
citation >= i
```

이 말은 `i`번째 논문도 `i`회 이상 인용되었다는 뜻이다.

그리고 앞에 있는 `i - 1`개의 논문은 현재 논문보다 인용 횟수가 크거나 같다.
따라서 총 `i`편의 논문이 `i`회 이상 인용된 상태다.

그래서 `i`는 H-Index 후보가 된다.

조건을 만족할 때마다 `answer = i`로 갱신하면, 마지막에는 가능한 가장 큰 값이 남는다.

## 개선해볼 수 있는 코드

내가 작성한 코드는 `citations.sort(reverse=True)`를 사용한다.
이 방식은 원본 리스트를 직접 바꾼다.

원본을 바꾸고 싶지 않다면 `sorted()`를 사용할 수 있다.

```python
def solution_refactored(citations):
    answer = 0

    for rank, citation in enumerate(sorted(citations, reverse=True), start=1):
        if citation >= rank:
            answer = rank

    return answer
```

그리고 `i` 대신 `rank`라는 이름을 쓰면 “현재 몇 번째 논문까지 보고 있는지”가 조금 더 잘 드러난다.

## 테스트 케이스

| citations | expected | 설명 |
|---|---:|---|
| `[3, 0, 6, 1, 5]` | `3` | 공식 예제 |
| `[0, 0, 0]` | `0` | 인용된 논문이 없는 경우 |
| `[1, 3, 5, 7, 9]` | `3` | 정렬이 필요한 경우 |
| `[10, 8, 5, 4, 3]` | `4` | H-Index가 4인 경우 |
| `[25, 8, 5, 3, 3]` | `3` | 큰 인용 수가 섞인 경우 |
| `[1]` | `1` | 논문이 하나이고 1회 인용 |
| `[0]` | `0` | 논문이 하나이고 0회 인용 |

## 시간복잡도

시간복잡도는 `O(n log n)`이다.

인용 횟수 목록을 정렬하는 데 `O(n log n)`이 걸린다.
정렬 후에는 한 번만 순회하므로 `O(n)`이다.

전체 시간복잡도는 정렬이 지배하므로 `O(n log n)`이다.

## 공간복잡도

내가 작성한 풀이는 `citations.sort(reverse=True)`를 사용한다.
이 방식은 리스트를 제자리에서 정렬하므로 추가 공간은 크지 않다.

다만 개선 풀이처럼 `sorted(citations, reverse=True)`를 사용하면 새 리스트를 만들기 때문에 `O(n)`의 추가 공간이 필요하다.

## 배운 점

- H-Index는 정의를 코드 조건으로 바꾸는 것이 핵심이다.
- 내림차순 정렬을 하면 현재 순서 `i`가 “최소 i편”이라는 의미를 갖게 된다.
- `citation >= i`는 “i번째 논문까지 최소 i회 이상 인용되었다”는 뜻으로 해석할 수 있다.
- `list.sort()`는 원본을 바꾸고, `sorted()`는 새 리스트를 반환한다.

## 다음에 비슷한 문제를 만나면 떠올릴 신호

- “최소 h편”, “h번 이상”처럼 개수와 기준값이 같이 나오면 정렬을 의심하자.
- 큰 값부터 확인해야 조건이 쉬워지면 내림차순 정렬을 생각하자.
- 정렬 후 인덱스가 의미를 갖는지 확인하자.
- `enumerate(..., start=1)`로 문제의 1부터 세는 개념을 코드에 맞출 수 있는지 보자.

## 최종적으로 기억할 코드

```python
def solution(citations):
    answer = 0

    for rank, citation in enumerate(sorted(citations, reverse=True), start=1):
        if citation >= rank:
            answer = rank

    return answer
```

## 마무리

H-Index는 처음에는 정의가 어렵게 느껴졌지만, 내림차순으로 정렬하고 나니 조건이 훨씬 단순해졌다.

이번 문제에서 가장 중요한 문장은 이것이다.

```text
i번째 논문의 인용 횟수가 i 이상이면, 최소 i편의 논문이 i회 이상 인용된 것이다.
```

이 문장을 코드로 옮기면 `citation >= i`가 된다.
정렬 문제에서 인덱스가 어떤 의미를 갖는지 보는 연습으로 좋은 문제였다.
