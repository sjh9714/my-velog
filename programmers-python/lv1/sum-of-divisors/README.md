# 약수의 합

## 문제 요약

정수 `n`이 주어진다.
`n`의 약수를 모두 더한 값을 반환한다.

문제 링크: https://school.programmers.co.kr/learn/courses/30/lessons/12928

## 접근 방식

어떤 수 `i`가 `n`의 약수인지 확인하려면 `n % i == 0`인지 보면 된다.

따라서 1부터 `n`까지 순회하면서 나누어 떨어지는 수만 결과에 더하면 된다.

## 핵심 코드

```python
def solution(n):
    answer = 0
    for i in range(1, n + 1):
        if n % i == 0:
            answer += i

    return answer
```

## 개선한 코드

```python
def solution_refactored(n):
    return sum(i for i in range(1, n + 1) if n % i == 0)
```

## 시간복잡도

O(n)

1부터 `n`까지 모든 수를 한 번씩 확인한다.

## 공간복잡도

O(1)

누적합을 저장하는 변수만 사용한다.

## 배운 점

- 약수 판별은 `n % i == 0`으로 할 수 있다.
- 범위가 1부터 n까지라면 `range(1, n + 1)`을 사용한다.
- 조건에 맞는 값들을 더할 때는 `sum()`과 제너레이터 표현식을 사용할 수 있다.
