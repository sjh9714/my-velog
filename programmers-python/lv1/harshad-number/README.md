# 하샤드 수

## 문제 요약

양의 정수 `x`가 주어진다.
`x`가 `x`의 자릿수 합으로 나누어 떨어지면 하샤드 수이므로 `True`를 반환하고, 아니면 `False`를 반환한다.

문제 링크: https://school.programmers.co.kr/learn/courses/30/lessons/12947

## 접근 방식

정수의 각 자릿수를 더해야 하므로 먼저 `str(x)`로 문자열로 바꾼다.
문자열을 순회하면서 각 문자를 `int()`로 다시 숫자로 변환해 더한다.

마지막으로 원래 숫자 `x`를 자릿수 합으로 나누었을 때 나머지가 0인지 확인한다.

## 핵심 코드

```python
def solution(x):
    arr = list(str(x))
    s = 0
    for i in arr:
        s += int(i)
    return False if x % s else True
```

## 개선한 코드

```python
def solution_refactored(x):
    digit_sum = sum(map(int, str(x)))
    return x % digit_sum == 0
```

## 시간복잡도

O(n)

`n`은 숫자 `x`의 자릿수다.
각 자릿수를 한 번씩 확인한다.

## 공간복잡도

O(n)

`str(x)`로 자릿수만큼의 문자열을 만든다.

## 배운 점

- 정수의 자릿수를 다룰 때는 `str(x)`로 문자열로 바꾸면 쉽다.
- 문자열 숫자는 계산하기 전에 `int()`로 변환해야 한다.
- 여러 값을 더할 때는 `sum()`을 사용할 수 있다.
- 반복 가능한 값 전체에 같은 변환을 적용할 때는 `map()`을 사용할 수 있다.
