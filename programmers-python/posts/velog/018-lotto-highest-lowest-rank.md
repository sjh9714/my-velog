# [DAY6] [프로그래머스/Python] 로또의 최고 순위와 최저 순위 - 0 처리와 순위 계산하기

## 문제 요약

민우가 산 로또 번호 `lottos`와 당첨 번호 `win_nums`가 주어진다.

`lottos`에는 `0`이 들어올 수 있는데, `0`은 알아볼 수 없는 번호를 의미한다.
즉, `0`은 어떤 번호가 될 수도 있고, 당첨 번호가 아닐 수도 있다.

구해야 하는 값은 두 가지다.

- 가능한 최고 순위
- 가능한 최저 순위

문제 링크: [로또의 최고 순위와 최저 순위](https://school.programmers.co.kr/learn/courses/30/lessons/77484)

## 처음 작성한 코드

처음에는 순위를 `rank = 7`에서 시작해서, 맞힌 번호가 나올 때마다 1씩 줄이는 방식으로 풀었다.

```python
def solution(lottos, win_nums):
    answer = []
    rank = 7
    zero = 0
    for i in lottos:
        if i in win_nums:
            rank -= 1
        elif i == 0:
            zero += 1
    return [rank - zero, rank] if rank < 7 else [rank - zero - 1, rank - 1]
```

대부분의 테스트는 통과했지만 테스트 15번만 실패했다.

## 테스트 15번만 실패한 이유

문제는 맞힌 번호가 하나도 없고, `0`만 있는 경우였다.

예를 들면 아래 케이스다.

```python
lottos = [0, 0, 0, 0, 0, 0]
win_nums = [38, 19, 20, 40, 15, 25]
```

이 경우 `0`이 모두 당첨 번호라고 가정하면 6개를 모두 맞힐 수 있다.
그래서 최고 순위는 1등이다.

반대로 `0`이 모두 당첨 번호가 아니라고 가정하면 맞힌 번호가 0개다.
그래서 최저 순위는 6등이다.

정답은 `[1, 6]`이다.

하지만 처음 작성한 코드는 이 케이스에서 `[0, 6]`을 반환했다.
로또에는 0등이 없기 때문에 잘못된 값이다.

테스트 15번은 `0`이 모두 당첨 번호가 될 수 있는 경우처럼 최고 순위가 1등까지 올라가는 경계 케이스로 볼 수 있었다.

## `0`이 6개인 반례 확인

처음 코드의 흐름을 보면 `rank`는 그대로 7이고, `zero`는 6이 된다.

```python
rank = 7
zero = 6
```

마지막 조건에서 `rank < 7`이 아니므로 아래 식을 탄다.

```python
[rank - zero - 1, rank - 1]
```

값을 대입하면 이렇게 된다.

```python
[7 - 6 - 1, 7 - 1]
```

즉 `[0, 6]`이 된다.

여기서 핵심은 순위를 직접 빼면서 계산하다 보니, `0등`이라는 존재하지 않는 값이 나왔다는 점이다.

## 순위를 개수에서 바로 계산하지 말고 함수로 분리하기

로또 순위는 맞힌 개수와 이렇게 연결된다.

| 맞힌 개수 | 순위 |
|---:|---:|
| 6 | 1 |
| 5 | 2 |
| 4 | 3 |
| 3 | 4 |
| 2 | 5 |
| 1 | 6 |
| 0 | 6 |

맞힌 개수가 0개 또는 1개일 때는 모두 6등이므로, 단순히 `7 - count`로만 계산하면 안 된다.

그래서 순위를 계산하는 함수를 따로 만들었다.

```python
def get_rank(count):
    return 6 if count < 2 else 7 - count
```

순위 변환은 별도 함수로 빼두면 0등 같은 잘못된 값이 나오는 실수를 줄일 수 있다.

## 개선한 코드

먼저 현재 확실히 맞힌 번호 개수와 `0`의 개수를 따로 센다.

```python
def get_rank(count):
    return 6 if count < 2 else 7 - count


def solution(lottos, win_nums):
    match_count = 0
    zero_count = 0

    for number in lottos:
        if number == 0:
            zero_count += 1
        elif number in win_nums:
            match_count += 1

    best_count = match_count + zero_count
    worst_count = match_count

    return [get_rank(best_count), get_rank(worst_count)]
```

`0`은 모두 맞을 수도 있고 모두 틀릴 수도 있다.

그래서 최고 순위는 `match_count + zero_count`로 계산하고, 최저 순위는 `match_count`만으로 계산한다.

## `set(win_nums)`로 조금 더 정리하기

당첨 번호에 포함되어 있는지 확인하는 부분은 `set`을 사용하면 의도가 더 명확해진다.

```python
def solution_refactored(lottos, win_nums):
    win_set = set(win_nums)
    zero_count = lottos.count(0)
    match_count = sum(1 for number in lottos if number in win_set)

    return [get_rank(match_count + zero_count), get_rank(match_count)]
```

문제에서는 번호가 6개뿐이라 성능 차이는 크지 않다.
그래도 “포함 여부를 자주 확인한다”는 상황에서는 `set`을 떠올리면 좋다.

## 테스트 케이스

| lottos | win_nums | expected | 설명 |
|---|---|---|---|
| `[44,1,0,0,31,25]` | `[31,10,45,1,6,19]` | `[3,5]` | 공식 예제 |
| `[0,0,0,0,0,0]` | `[38,19,20,40,15,25]` | `[1,6]` | 테스트 15번 성격의 경계 케이스 |
| `[45,4,35,20,3,9]` | `[20,9,3,45,4,35]` | `[1,1]` | 전부 일치 |
| `[1,2,3,4,5,6]` | `[7,8,9,10,11,12]` | `[6,6]` | 전부 불일치 |
| `[1,2,3,4,5,6]` | `[1,8,9,10,11,12]` | `[6,6]` | 1개만 일치 |
| `[0,0,1,2,3,4]` | `[1,2,5,6,7,8]` | `[3,5]` | 0과 일부 정답 혼합 |

## 시간복잡도

시간복잡도는 `O(n)`이다.

`n`은 `lottos`의 길이다.
다만 문제에서 로또 번호는 항상 6개이므로 실제로는 상수 시간에 가깝다.

## 공간복잡도

공간복잡도는 `O(1)`이다.

개수 변수만 사용한다.
개선 풀이에서 `set(win_nums)`를 만들지만, 당첨 번호 개수도 6개로 고정되어 있어 상수 공간으로 볼 수 있다.

## 배운 점

- 맞힌 개수가 0개와 1개일 때 모두 6등이라는 조건을 놓치면 안 된다.
- 직접 순위를 빼면서 계산하기보다, 맞힌 개수를 센 뒤 순위로 변환하는 편이 안전하다.
- `0`처럼 미확정 값을 포함하는 문제는 최고 경우와 최저 경우를 따로 생각하자.
- 포함 여부를 여러 번 확인할 때는 `set`을 떠올리자.

## 다음에 비슷한 문제를 만나면 떠올릴 신호

- “최고/최저”가 나오면 확정된 값과 미확정 값을 분리해서 세자.
- 순위표나 등급표가 나오면 변환 함수를 따로 만들자.
- 0개, 1개처럼 같은 결과로 묶이는 경계값을 먼저 확인하자.
- 테스트 하나만 실패하면 가장 작은 값, 가장 큰 값, 전부 같은 값 같은 경계 케이스를 의심하자.

## 최종적으로 기억할 코드

```python
def get_rank(count):
    return 6 if count < 2 else 7 - count


def solution(lottos, win_nums):
    win_set = set(win_nums)
    zero_count = lottos.count(0)
    match_count = sum(1 for number in lottos if number in win_set)

    return [get_rank(match_count + zero_count), get_rank(match_count)]
```

## 마무리

Day6 세 번째 문제는 로직 자체보다 순위 변환의 경계값이 중요했던 문제였다.

처음 작성한 코드는 맞힌 번호와 0의 개수를 이용하려는 방향은 좋았다.
다만 순위를 직접 빼면서 처리하다 보니, `0`이 6개인 경우에 0등이라는 잘못된 값이 나왔다.

앞으로 순위나 등급을 계산하는 문제에서는 먼저 개수를 정확히 세고, 그다음 변환 함수로 안전하게 바꾸는 흐름을 기억해야겠다.
