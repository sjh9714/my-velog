# 숫자 문자열과 영단어

## 문제 요약

숫자의 일부 자리가 영단어로 바뀐 문자열 `s`가 주어진다.
`zero`부터 `nine`까지의 영단어를 숫자로 바꾼 뒤 정수로 반환한다.

문제 링크: https://school.programmers.co.kr/learn/courses/30/lessons/81301

## 접근 방식

각 숫자와 대응되는 영어 단어가 정해져 있으므로, 문자열에서 영어 단어를 숫자 문자로 치환하면 된다.

Python의 `replace()`는 문자열 안에 있는 특정 부분 문자열을 모두 바꿔준다.
따라서 `zero`부터 `nine`까지 순회하면서 발견되는 단어를 해당 숫자로 바꾸면 최종적으로 숫자만 남는다.

## 핵심 코드

```python
def solution(s):
    num = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    text = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]

    for i in range(len(num)):
        s = s.replace(text[i], num[i])

    return int(s)
```

## 개선한 코드

```python
def solution_refactored(s):
    number_words = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]

    for digit, word in enumerate(number_words):
        s = s.replace(word, str(digit))

    return int(s)
```

## 시간복잡도

O(n)

숫자 영단어는 10개로 고정되어 있고, 각 `replace()`가 문자열 길이만큼 확인한다.
상수 10을 제외하면 문자열 길이에 비례한다.

## 공간복잡도

O(n)

문자열은 불변 객체이므로 `replace()`를 할 때마다 새 문자열이 만들어질 수 있다.

## 배운 점

- 정해진 단어를 다른 값으로 바꾸는 문제에서는 `replace()`를 떠올릴 수 있다.
- 숫자와 단어처럼 순서가 대응되는 데이터는 `enumerate()`로 함께 꺼내면 읽기 좋아진다.
- 최종 결과가 정수라면 마지막에 `int()`로 변환하면 된다.
