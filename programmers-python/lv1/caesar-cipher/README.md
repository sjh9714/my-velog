# 시저 암호

## 문제 요약

문자열 `s`와 이동할 칸 수 `n`이 주어진다.
문자열의 각 알파벳을 `n`칸씩 밀어서 새 문자열을 반환한다.

공백은 그대로 두고, `z` 다음은 `a`, `Z` 다음은 `A`로 돌아와야 한다.

문제 링크: https://school.programmers.co.kr/learn/courses/30/lessons/12926

## 접근 방식

알파벳을 밀어야 하는 문제는 문자 자체보다 문자 코드의 위치를 숫자로 바꿔 생각하면 쉽다.

`ord()`로 문자를 ASCII 코드로 바꾸고, 알파벳 시작점인 `A` 또는 `a`를 빼서 0부터 25 사이의 위치로 만든다.
그다음 `n`을 더하고 `% 26`으로 알파벳 범위 안에서 순환시킨다.

## 핵심 코드

```python
def solution(s, n):
    answer = []

    for char in s:
        if char == " ":
            answer.append(char)
        elif "A" <= char <= "Z":
            answer.append(chr((ord(char) - 65 + n) % 26 + 65))
        else:
            answer.append(chr((ord(char) - 97 + n) % 26 + 97))

    return "".join(answer)
```

## 시간복잡도

O(n)

문자열을 한 번 순회한다.

## 공간복잡도

O(n)

결과 문자열을 만들기 위한 리스트가 필요하다.

## 배운 점

- 문자를 숫자로 다룰 때는 `ord()`와 `chr()`를 사용할 수 있다.
- 알파벳이 끝에서 다시 처음으로 돌아와야 하면 `% 26`을 떠올리자.
- 대문자와 소문자는 ASCII 기준점이 다르므로 각각 `A`, `a`를 기준으로 계산해야 한다.
- 공백은 암호화 대상이 아니므로 그대로 결과에 넣는다.
