# [DAY9] [프로그래머스/Python] 전화번호 목록 - startswith 방향과 정렬로 효율성 통과하기

## 문제 요약

전화번호 목록 `phone_book`이 주어진다.
어떤 번호가 다른 번호의 접두어인 경우가 있으면 `False`, 접두어 관계가 없으면 `True`를 반환해야 한다.

문제 링크: [전화번호 목록](https://school.programmers.co.kr/learn/courses/30/lessons/42577)

예를 들어 아래 전화번호 목록에서는 `"119"`가 `"1195524421"`의 접두어다.

```python
phone_book = ["119", "97674223", "1195524421"]
```

따라서 정답은 `False`다.

## 처음 작성한 코드

처음에는 전화번호 하나를 꺼내고, 나머지 전화번호들 중 하나로 시작하는지 확인하려고 했다.

```python
def solution(phone_book):
    for i in phone_book:
        phone_book.remove(i)
        phone_book_tuple = tuple(phone_book)
        if i.startswith(phone_book_tuple):
            return False
        phone_book.append(i)
    return True
```

이 코드로 제출했을 때 정확성 테스트 3, 15, 19가 실패했고, 효율성 테스트 3, 4도 실패했다.

## 정확성 3, 15, 19가 실패한 이유

가장 큰 문제는 반복 중인 리스트를 직접 수정했다는 점이다.

```python
for i in phone_book:
    phone_book.remove(i)
    ...
    phone_book.append(i)
```

`for i in phone_book`으로 리스트를 순회하는 중에 `remove()`와 `append()`로 같은 리스트를 바꾸면, 반복문이 다음 원소를 바라보는 흐름이 꼬일 수 있다.

아주 작은 반례로 보면 더 잘 보인다.

```python
phone_book = ["1", "11"]
```

이 경우 `"1"`은 `"11"`의 접두어이므로 정답은 `False`여야 한다.
하지만 기존 풀이는 리스트를 순회하면서 원소를 제거하고 다시 붙이기 때문에 이 케이스에서 `True`가 나올 수 있다.

또 하나 조심해야 할 점은 `startswith()`의 방향이다.

```python
i.startswith(phone_book_tuple)
```

이 코드는 `i`가 다른 번호들 중 하나로 시작하는지 확인한다.
하지만 우리가 확인해야 하는 것은 어떤 번호가 다른 번호의 접두어인지다.

예를 들어 `"1"`과 `"11"`이 있다면 확인해야 하는 방향은 아래와 같다.

```python
"11".startswith("1")
```

짧은 번호가 긴 번호의 앞에 붙어 있는지 봐야 하므로, 비교 방향을 조심해야 한다.

## 효율성 3, 4가 실패한 이유

두 번째 문제는 효율성이다.

기존 풀이는 전화번호 하나를 볼 때마다 나머지 전화번호 전체를 `tuple`로 만든다.

```python
phone_book_tuple = tuple(phone_book)
```

그리고 `startswith()`에 여러 후보를 넣어 비교한다.
결국 모든 번호를 모든 번호와 비교하는 구조에 가까워진다.

문제의 제한에서 `phone_book`의 길이는 최대 1,000,000까지 가능하다.
이 정도 크기에서는 모든 쌍을 비교하는 `O(n^2)` 방식은 효율성 테스트를 통과하기 어렵다.

## 왜 정렬하면 인접한 번호만 보면 되는가

전화번호는 문자열이다.
문자열을 정렬하면 비슷한 접두어를 가진 값들이 서로 가까이 붙는다.

예를 들어 아래 목록을 보자.

```python
phone_book = ["1235", "12", "567"]
```

정렬하면 이렇게 된다.

```python
["12", "1235", "567"]
```

`"12"`와 `"1235"`가 바로 이웃하게 된다.
따라서 접두어 관계가 있는지 모든 번호끼리 비교할 필요 없이, 정렬된 상태에서 인접한 두 번호만 확인하면 된다.

핵심은 이 비교다.

```python
sorted_phone_book[i + 1].startswith(sorted_phone_book[i])
```

뒤 번호가 앞 번호로 시작하면 앞 번호가 뒤 번호의 접두어라는 뜻이다.

## 개선한 코드

정렬 후 인접한 번호만 비교하는 방식으로 풀었다.

```python
def solution(phone_book):
    sorted_phone_book = sorted(phone_book)

    for i in range(len(sorted_phone_book) - 1):
        if sorted_phone_book[i + 1].startswith(sorted_phone_book[i]):
            return False

    return True
```

## 코드 설명

먼저 전화번호 목록을 정렬한다.

```python
sorted_phone_book = sorted(phone_book)
```

그다음 인접한 두 번호를 비교한다.

```python
for i in range(len(sorted_phone_book) - 1):
```

마지막 원소는 뒤에 비교할 원소가 없으므로 `len(sorted_phone_book) - 1`까지만 순회한다.

접두어 관계는 아래처럼 확인한다.

```python
if sorted_phone_book[i + 1].startswith(sorted_phone_book[i]):
    return False
```

뒤 번호가 앞 번호로 시작한다면 접두어 관계가 있는 것이다.
하나라도 발견하면 바로 `False`를 반환한다.

끝까지 접두어 관계가 없으면 `True`를 반환한다.

## `all()`로 표현한 코드

같은 아이디어를 `all()`로도 표현할 수 있다.

```python
def solution_refactored(phone_book):
    sorted_phone_book = sorted(phone_book)

    return all(
        not sorted_phone_book[i + 1].startswith(sorted_phone_book[i])
        for i in range(len(sorted_phone_book) - 1)
    )
```

모든 인접 쌍이 접두어 관계가 아니어야 `True`라는 의미다.
개인적으로는 처음에는 `for`문 풀이가 더 읽기 쉽고, 익숙해진 뒤 `all()` 표현을 보는 게 좋다고 느꼈다.

## 테스트 케이스

| phone_book | expected | 설명 |
|---|---:|---|
| `["119", "97674223", "1195524421"]` | `False` | 공식 예제 |
| `["123", "456", "789"]` | `True` | 접두어 없음 |
| `["12", "123", "1235", "567", "88"]` | `False` | 공식 예제 |
| `["1", "11"]` | `False` | 최소 반례 |
| `["911", "97625999", "91125426"]` | `False` | 접두어가 뒤에 숨어 있는 경우 |
| `["1235", "12", "567"]` | `False` | 정렬 전 순서가 섞인 경우 |
| `["123", "124", "125"]` | `True` | 비슷하지만 접두어는 아님 |
| `["987654321"]` | `True` | 전화번호가 하나뿐인 경우 |

## 시간복잡도

시간복잡도는 `O(n log n)`이다.

전화번호 목록을 정렬하는 데 `O(n log n)`이 걸린다.
그다음 인접한 번호를 한 번씩 비교하므로 순회 자체는 `O(n)`이다.

전체 시간복잡도는 정렬이 지배하므로 `O(n log n)`으로 볼 수 있다.

## 공간복잡도

공간복잡도는 `O(n)`이다.

`sorted(phone_book)`으로 정렬된 새 리스트를 만들기 때문이다.

## 배운 점

- 반복 중인 리스트를 `remove()`나 `append()`로 직접 수정하면 순회가 꼬일 수 있다.
- `startswith()`는 방향이 중요하다.
- 접두어 관계는 정렬하면 인접한 값끼리만 확인해도 된다.
- 모든 쌍을 비교하는 방식은 입력이 커질 때 효율성 테스트에서 실패하기 쉽다.
- 해시 문제로 분류되어 있어도 정렬로 더 간단하게 풀 수 있는 경우가 있다.

## 다음에 비슷한 문제를 만나면 떠올릴 신호

- 접두어, 사전순, 문자열 비교가 나오면 정렬을 먼저 떠올리자.
- 리스트를 순회하면서 같은 리스트를 수정하고 있다면 위험 신호로 보자.
- `startswith()`를 쓸 때는 어느 문자열이 더 긴지, 어느 방향으로 비교해야 하는지 먼저 확인하자.
- 입력 크기가 크면 모든 쌍 비교를 피할 방법을 찾자.

## 최종적으로 기억할 코드

```python
def solution(phone_book):
    sorted_phone_book = sorted(phone_book)

    for i in range(len(sorted_phone_book) - 1):
        if sorted_phone_book[i + 1].startswith(sorted_phone_book[i]):
            return False

    return True
```

## 마무리

Day9 두 번째 문제는 처음 코드가 꽤 아슬아슬하게 보이는 문제였다.

`startswith(tuple)`을 사용한 방향 자체는 흥미로웠지만, 반복 중인 리스트를 직접 바꾸는 점과 모든 번호를 반복 비교하는 구조 때문에 정확성과 효율성에서 모두 문제가 생겼다.

정렬 후 인접한 번호만 비교한다는 아이디어를 알고 나면 코드는 훨씬 짧아진다.
이번 문제를 통해 문자열 접두어 문제에서는 정렬이 강력한 힌트가 될 수 있다는 점을 기억해야겠다.
