# 최대공약수와 최소공배수

## 문제 요약

두 자연수 `n`, `m`이 주어진다.
두 수의 최대공약수와 최소공배수를 배열에 담아 반환한다.

문제 링크: https://school.programmers.co.kr/learn/courses/30/lessons/12940

## 접근 방식

Python의 `math` 모듈에는 최대공약수를 구하는 `math.gcd()`와 최소공배수를 구하는 `math.lcm()`이 있다.

두 함수를 사용하면 문제 조건을 그대로 코드로 옮길 수 있다.

## 핵심 코드

```python
import math


def solution(n, m):
    return [gcd(n, m), lcm(n, m)]


def gcd(n, m):
    return math.gcd(n, m)


def lcm(n, m):
    return math.lcm(n, m)
```

## 개선한 코드

```python
def solution_refactored(n, m):
    gcd_value = math.gcd(n, m)
    lcm_value = n * m // gcd_value
    return [gcd_value, lcm_value]
```

## 핵심 공식

최소공배수는 다음 공식으로 구할 수 있다.

```python
lcm = n * m // gcd
```

## 시간복잡도

O(log min(n, m))

`math.gcd()`는 유클리드 호제법 기반으로 동작한다.

## 공간복잡도

O(1)

결과 배열과 몇 개의 변수만 사용한다.

## 배운 점

- 최대공약수는 `math.gcd()`로 구할 수 있다.
- 최소공배수는 `math.lcm()`으로 구할 수 있다.
- `math.lcm()`을 사용할 수 없는 환경이라면 `n * m // gcd` 공식을 사용할 수 있다.
- 최대공약수와 최소공배수는 서로 연결되어 있다.
