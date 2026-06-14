# [DAY4] [프로그래머스/Python] 숫자 문자열과 영단어 - replace로 문자열 숫자 변환하기

## 문제 요약

문자열 `s`가 주어진다.

이 문자열에는 숫자와 숫자를 뜻하는 영어 단어가 섞여 있다.
영어 단어로 적힌 숫자를 실제 숫자로 바꾼 뒤, 전체 값을 정수로 반환하면 된다.

문제 링크: [숫자 문자열과 영단어](https://school.programmers.co.kr/learn/courses/30/lessons/81301)

예를 들어 다음 문자열이 있다.

```python
s = "one4seveneight"
```

`one`은 `1`, `seven`은 `7`, `eight`은 `8`이므로 결과는 `1478`이다.

## 처음 생각한 접근

이 문제는 숫자 영단어가 정해져 있다.

`zero`, `one`, `two`, `three`, `four`, `five`, `six`, `seven`, `eight`, `nine`

즉, 문자열 안에 있는 이 단어들을 각각 `0`부터 `9`까지의 숫자 문자로 바꾸면 된다.

문자열에서 특정 단어를 다른 문자열로 바꿔야 하므로 `replace()`를 사용하면 자연스럽게 풀 수 있다.

## 내가 작성한 코드

```python
def solution(s):
    num = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    text = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]

    for i in range(len(num)):
        s = s.replace(text[i], num[i])

    return int(s)
```

## 코드 설명

먼저 숫자 문자와 숫자 영단어를 각각 리스트로 만든다.

```python
num = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
text = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
```

두 리스트는 같은 인덱스끼리 서로 대응된다.

예를 들어 `text[1]`은 `"one"`이고, `num[1]`은 `"1"`이다.

그다음 인덱스를 기준으로 0부터 9까지 순회한다.

```python
for i in range(len(num)):
```

각 숫자 영단어를 해당 숫자 문자로 바꾼다.

```python
s = s.replace(text[i], num[i])
```

예를 들어 문자열 안에 `"seven"`이 있으면 `"7"`로 바뀐다.

마지막에는 숫자 문자만 남은 문자열을 정수로 변환한다.

```python
return int(s)
```

## 좋았던 점

처음 작성한 풀이는 문제의 핵심을 잘 잡았다.

이 문제는 복잡하게 문자를 하나씩 파싱하기보다, 정해진 영단어를 숫자로 치환하면 되는 문제였다.
`replace()`를 사용해서 문자열 변환 문제로 단순화한 점이 좋았다.

또 숫자와 영단어를 같은 인덱스에 맞춰 둔 덕분에 `text[i]`를 `num[i]`로 바꾸는 흐름이 직관적이었다.

## 개선해볼 수 있는 코드

같은 아이디어를 `enumerate()`로 표현하면 인덱스의 의미가 조금 더 분명해진다.

```python
def solution_refactored(s):
    number_words = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]

    for digit, word in enumerate(number_words):
        s = s.replace(word, str(digit))

    return int(s)
```

여기서 `digit`은 숫자 값이고, `word`는 그 숫자를 뜻하는 영어 단어다.

예를 들어 `digit = 2`, `word = "two"`라면 문자열 안의 `"two"`를 `"2"`로 바꾼다.

## replace()를 사용할 때 생각할 점

`replace()`는 문자열 안에 있는 모든 대상 문자열을 한 번에 바꾼다.

```python
"oneone".replace("one", "1")  # "11"
```

이 문제에서는 같은 숫자 영단어가 여러 번 나와도 모두 숫자로 바뀌어야 하므로 `replace()`가 잘 맞는다.

다만 문자열은 불변 객체라서 `replace()`를 호출하면 원래 문자열이 직접 바뀌는 것이 아니라 새 문자열이 만들어진다.
그래서 결과를 다시 `s`에 넣어줘야 한다.

```python
s = s.replace(word, str(digit))
```

## 테스트 케이스

| s | expected | 설명 |
|---|---:|---|
| `"one4seveneight"` | `1478` | 영단어와 숫자 혼합 |
| `"23four5six7"` | `234567` | 중간에 영단어 포함 |
| `"2three45sixseven"` | `234567` | 여러 영단어 포함 |
| `"123"` | `123` | 숫자만 있는 문자열 |
| `"zero"` | `0` | 0 하나만 있는 경우 |
| `"zero9eight"` | `98` | 앞에 zero가 있는 경우 |

## 시간복잡도

시간복잡도는 `O(n)`이다.

숫자 영단어는 10개로 고정되어 있다.
각 `replace()`는 문자열 길이 `n`에 비례해 확인하므로, 전체적으로는 `10 * n`이고 상수를 제외하면 `O(n)`으로 볼 수 있다.

## 공간복잡도

공간복잡도는 `O(n)`이다.

`replace()`를 할 때 새 문자열이 만들어질 수 있고, 최종 문자열 역시 입력 길이에 비례한다.

## 배운 점

- 정해진 단어를 다른 값으로 바꾸는 문제에서는 `replace()`를 먼저 떠올릴 수 있다.
- 숫자와 단어처럼 순서가 대응되는 데이터는 리스트와 인덱스로 연결할 수 있다.
- `enumerate()`를 사용하면 인덱스와 값을 함께 꺼낼 수 있어 코드 의도가 더 잘 보인다.
- 문자열 변환이 끝난 뒤 정수로 반환해야 한다면 마지막에 `int()`를 적용하면 된다.

## 다음에 비슷한 문제를 만나면 떠올릴 신호

- 정해진 단어 목록을 숫자나 기호로 바꿔야 하면 `replace()`를 떠올리자.
- 문자열 전체를 직접 파싱하기 전에, 치환만으로 해결할 수 있는지 먼저 보자.
- 두 리스트가 같은 인덱스로 대응된다면 `enumerate()`로 더 간단히 표현할 수 있는지 확인하자.
- 결과 타입이 문자열인지 정수인지 마지막 반환 타입을 꼭 확인하자.

## 최종적으로 기억할 코드

```python
def solution_refactored(s):
    number_words = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]

    for digit, word in enumerate(number_words):
        s = s.replace(word, str(digit))

    return int(s)
```

## 마무리

이번 문제는 Day4 문자열 변환 문제의 마무리로 딱 좋은 문제였다.

처음 작성한 코드는 `replace()`를 사용해서 문제를 깔끔하게 풀었다.
여기에 `enumerate()`를 적용하면 숫자와 영단어가 어떻게 대응되는지 더 잘 드러난다.

문자열 안의 정해진 패턴을 바꾸는 문제가 나오면, 먼저 `replace()`로 단순하게 해결할 수 있는지 떠올려봐야겠다.
