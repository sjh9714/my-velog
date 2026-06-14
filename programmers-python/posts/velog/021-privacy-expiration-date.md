# [DAY8] [프로그래머스/Python] 개인정보 수집 유효기간 - 날짜를 28일 기준으로 변환하기

## 문제 요약

오늘 날짜 `today`, 약관별 유효기간 `terms`, 개인정보 수집 정보 `privacies`가 주어진다.

각 개인정보는 `"수집일자 약관종류"` 형태로 들어온다.
약관 종류마다 보관 가능한 기간이 다르고, 오늘 날짜 기준으로 유효기간이 지난 개인정보 번호를 반환해야 한다.

문제에서는 모든 달이 28일까지 있다고 가정한다.

문제 링크: [개인정보 수집 유효기간](https://school.programmers.co.kr/learn/courses/30/lessons/150370)

## 처음 생각한 접근

처음에는 날짜를 그대로 비교하기보다 숫자로 바꿔서 비교하는 방식으로 접근했다.

문제에서 모든 달이 28일이라고 정해줬기 때문에, 실제 달력처럼 월마다 일수가 다르다고 생각할 필요가 없었다.
그래서 `yyyy.mm.dd` 형태의 날짜를 하나의 일수로 바꿨다.

```python
year * 12 * 28 + month * 28 + day
```

이렇게 바꾸면 날짜 비교가 단순한 숫자 비교가 된다.

## 내가 작성한 코드

```python
def solution(today, terms, privacies):
    answer = []
    terms_dict = {}

    for i in terms:
        a, n = i.split()
        terms_dict[a] = int(n)

    def to_days(date):
        y, m, d = map(int, date.split("."))
        return y * 12 * 28 + m * 28 + d

    today_days = to_days(today)
    index = 0
    for i in privacies:
        index += 1
        d, a = i.split()
        if to_days(d) + terms_dict[a] * 28 <= today_days:
            answer.append(index)

    return answer
```

## 코드 설명

먼저 약관 종류별 유효기간을 딕셔너리에 저장했다.

```python
terms_dict[a] = int(n)
```

예를 들어 `["A 6", "B 12"]`가 들어오면 아래처럼 저장된다.

```python
terms_dict = {
    "A": 6,
    "B": 12,
}
```

그다음 날짜를 일수로 바꾸는 `to_days()` 함수를 만들었다.

```python
def to_days(date):
    y, m, d = map(int, date.split("."))
    return y * 12 * 28 + m * 28 + d
```

모든 달이 28일이므로, 연도는 `12 * 28`일 단위로, 월은 `28`일 단위로 바꿀 수 있다.

마지막으로 개인정보마다 수집일과 약관 종류를 분리한 뒤, 만료 여부를 확인했다.

```python
if to_days(d) + terms_dict[a] * 28 <= today_days:
    answer.append(index)
```

수집일에 유효기간을 더한 날짜가 오늘보다 작거나 같으면 이미 파기해야 하는 개인정보다.

## 좋았던 점

날짜를 문자열 그대로 다루지 않고, 비교 가능한 숫자로 바꾼 점이 좋았다.

날짜 문제는 처음에는 복잡해 보이지만, 문제에서 주어진 기준이 있으면 그 기준 단위로 바꾸는 것이 훨씬 단순하다.
이번 문제에서는 모든 달이 28일이라는 조건 덕분에 `to_days()` 함수 하나로 비교를 끝낼 수 있었다.

## 날짜를 일수로 바꾸는 이유

문자열 날짜를 그대로 비교하려고 하면 월이 넘어가는 경우나 연도가 바뀌는 경우를 계속 신경 써야 한다.

예를 들어 아래 두 날짜를 비교한다고 생각해보자.

```python
"2022.12.28"
"2023.01.01"
```

문자열을 쪼개서 연도, 월, 일을 각각 비교할 수도 있지만 조건이 많아진다.
반면 둘 다 일수로 바꾸면 그냥 숫자 두 개를 비교하면 된다.

```python
to_days("2022.12.28") < to_days("2023.01.01")
```

이 문제에서는 모든 달이 28일이므로 이런 변환이 특히 잘 맞는다.

## 만료 조건에서 `<=`를 쓰는 이유

개인정보는 유효기간이 끝나면 파기해야 한다.

코드에서는 아래 조건을 사용했다.

```python
to_days(d) + terms_dict[a] * 28 <= today_days
```

예를 들어 수집일이 `2022.04.19`이고 유효기간이 1개월이라면, 28일을 더한 값은 `2022.05.19`가 된다.
오늘이 `2022.05.19`라면 이미 유효기간이 지난 상태로 보고 파기 대상에 포함해야 한다.

그래서 `<`가 아니라 `<=`를 사용한다.

## 개선해볼 수 있는 코드

처음 풀이도 잘 동작하지만, 개인정보 번호를 따로 `index`로 관리하지 않고 `enumerate()`를 사용하면 더 읽기 쉽다.

```python
def solution_refactored(today, terms, privacies):
    term_months = {}

    for term in terms:
        term_type, month = term.split()
        term_months[term_type] = int(month)

    def to_days(date):
        year, month, day = map(int, date.split("."))
        return year * 12 * 28 + month * 28 + day

    today_days = to_days(today)
    expired_privacies = []

    for index, privacy in enumerate(privacies, start=1):
        collected_date, term_type = privacy.split()
        expiration_days = to_days(collected_date) + term_months[term_type] * 28

        if expiration_days <= today_days:
            expired_privacies.append(index)

    return expired_privacies
```

`enumerate(privacies, start=1)`를 쓰면 문제에서 요구하는 개인정보 번호와 반복문 인덱스를 자연스럽게 맞출 수 있다.

## 테스트 케이스

| today | terms | privacies | expected | 설명 |
|---|---|---|---|---|
| `"2022.05.19"` | `["A 6", "B 12", "C 3"]` | `["2021.05.02 A","2021.07.01 B","2022.02.19 C","2022.02.20 C"]` | `[1,3]` | 공식 예제 |
| `"2020.01.01"` | `["Z 3", "D 5"]` | `["2019.01.01 D","2019.11.15 Z","2019.08.02 D","2019.07.01 D","2018.12.28 Z"]` | `[1,4,5]` | 공식 예제 |
| `"2022.05.19"` | `["A 1"]` | `["2022.04.19 A"]` | `[1]` | 오늘이 정확히 파기일 |
| `"2022.05.19"` | `["A 1"]` | `["2022.04.20 A"]` | `[]` | 아직 유효한 마지막 구간 |
| `"2023.01.01"` | `["A 2"]` | `["2022.11.01 A"]` | `[1]` | 연도 넘어가는 경계 |
| `"2022.12.28"` | `["A 1", "B 2", "C 12"]` | `["2022.11.28 A", "2022.11.01 B", "2021.12.28 C", "2021.12.29 C"]` | `[1,3]` | 여러 약관 종류 혼합 |

## 시간복잡도

시간복잡도는 `O(t + p)`이다.

`t`는 약관 수, `p`는 개인정보 수다.
약관을 딕셔너리에 저장하기 위해 한 번 순회하고, 개인정보 목록을 다시 한 번 순회한다.

## 공간복잡도

공간복잡도는 `O(t + p)`이다.

약관 정보를 저장하는 딕셔너리에 `O(t)` 공간이 필요하고, 파기 대상 번호를 저장하는 결과 리스트에 최대 `O(p)` 공간이 필요하다.

## 배운 점

- 날짜 비교 문제는 같은 기준 단위의 숫자로 바꾸면 단순해진다.
- 문제에서 모든 달이 28일이라고 했으므로 실제 달력 계산을 하지 않아도 된다.
- 만료 여부를 판단할 때는 경계 조건에서 `<`인지 `<=`인지 꼭 확인해야 한다.
- 1번부터 시작하는 번호가 필요하면 `enumerate(..., start=1)`를 떠올리자.

## 다음에 비슷한 문제를 만나면 떠올릴 신호

- 날짜 비교가 나오면 먼저 숫자로 변환할 수 있는지 생각하자.
- 문제에서 별도의 날짜 규칙을 주면 실제 달력보다 문제 규칙을 우선하자.
- “오늘 기준으로 만료” 같은 표현이 나오면 경계값을 직접 만들어보자.
- 결과 번호가 1부터 시작하면 `enumerate(start=1)`를 쓰자.

## 최종적으로 기억할 코드

```python
def solution(today, terms, privacies):
    term_months = {}

    for term in terms:
        term_type, month = term.split()
        term_months[term_type] = int(month)

    def to_days(date):
        year, month, day = map(int, date.split("."))
        return year * 12 * 28 + month * 28 + day

    today_days = to_days(today)
    expired_privacies = []

    for index, privacy in enumerate(privacies, start=1):
        collected_date, term_type = privacy.split()
        expiration_days = to_days(collected_date) + term_months[term_type] * 28

        if expiration_days <= today_days:
            expired_privacies.append(index)

    return expired_privacies
```

## 마무리

Day8 두 번째 문제는 조건이 많은 구현 문제처럼 보이지만, 핵심은 날짜를 비교 가능한 숫자로 바꾸는 것이었다.

처음 작성한 풀이도 `to_days()` 함수를 만들어 날짜 비교를 단순화한 방향이 좋았다.
개선 코드에서는 `enumerate()`를 사용해 개인정보 번호를 더 자연스럽게 처리했다.

이번 문제를 통해 날짜 문제를 만났을 때 바로 복잡한 달력 계산으로 들어가기보다, 문제에서 제공한 규칙을 기준으로 단위를 통일하는 습관이 중요하다는 걸 다시 확인했다.
