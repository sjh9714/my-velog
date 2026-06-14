# [DAY6] [프로그래머스/Python] 크레인 인형뽑기 게임 - 스택으로 사라지는 인형 처리하기

## 문제 요약

2차원 배열 `board`와 크레인이 움직이는 위치 `moves`가 주어진다.

크레인은 `moves`에 적힌 열에서 가장 위에 있는 인형을 하나 뽑는다.
뽑은 인형은 바구니에 쌓인다.

이때 바구니의 가장 위 인형과 새로 뽑은 인형이 같으면 두 인형이 사라진다.
최종적으로 사라진 인형의 개수를 반환하면 된다.

문제 링크: [크레인 인형뽑기 게임](https://school.programmers.co.kr/learn/courses/30/lessons/64061)

## 처음 생각한 접근

이 문제는 크게 두 가지를 처리해야 한다.

1. 크레인이 선택한 열에서 가장 위에 있는 인형을 찾는다.
2. 바구니의 마지막 인형과 비교해서 같으면 제거한다.

바구니에서는 항상 마지막에 넣은 인형만 확인하면 된다.
그래서 리스트를 스택처럼 사용하면 된다고 생각했다.

## 내가 작성한 코드

```python
def solution(board, moves):
    stack = []
    result = 0
    for move in moves:
        for i in range(len(board)):
            cur = board[i][move - 1]
            if cur != 0:
                if stack:
                    if stack[-1] == cur:
                        stack.pop()
                        result += 2
                    else:
                        stack.append(cur)
                else:
                    stack.append(cur)
                board[i][move - 1] = 0
                break
    return result
```

## 코드 설명

먼저 바구니 역할을 할 `stack`과 사라진 인형 수를 저장할 `result`를 만든다.

```python
stack = []
result = 0
```

`moves`를 하나씩 순회한다.

```python
for move in moves:
```

문제에서 열 번호는 1부터 시작한다.
하지만 Python 리스트 인덱스는 0부터 시작하므로 실제 열 인덱스는 `move - 1`이다.

```python
cur = board[i][move - 1]
```

각 열에서 위에서 아래로 내려가며 0이 아닌 값을 찾는다.
0은 빈 칸이고, 0이 아닌 값은 인형이다.

```python
if cur != 0:
```

인형을 찾았다면 바구니의 마지막 인형과 비교한다.

```python
if stack[-1] == cur:
```

같은 인형이면 기존 인형을 꺼내고, 새로 뽑은 인형까지 함께 사라졌으므로 `result`에 2를 더한다.

```python
stack.pop()
result += 2
```

같지 않다면 새 인형을 바구니에 넣는다.

```python
stack.append(cur)
```

인형을 뽑은 위치는 빈 칸이 되었으므로 0으로 바꾼다.

```python
board[i][move - 1] = 0
```

한 번의 move에서는 인형 하나만 뽑으므로 인형을 찾은 뒤에는 `break`로 다음 move로 넘어간다.

## 좋았던 점

처음 작성한 풀이는 문제의 핵심인 스택 구조를 잘 사용했다.

바구니의 마지막 인형만 확인하면 되기 때문에 `stack[-1]`로 비교하고, 같은 경우 `pop()`으로 제거하는 흐름이 자연스럽다.
또 인형을 뽑은 뒤 `board`를 0으로 바꾼 것도 실제 게임 상태를 잘 반영한 부분이다.

## 스택을 사용한 이유

이 문제에서 바구니는 아래에서 위로 인형이 쌓이는 구조다.

새 인형이 들어올 때 확인해야 하는 것은 가장 마지막에 들어온 인형뿐이다.
즉, 마지막에 넣은 값을 먼저 확인하는 LIFO 구조다.

Python 리스트는 `append()`와 `pop()`으로 스택처럼 사용할 수 있다.

```python
stack.append(doll)
stack.pop()
```

그래서 별도의 자료구조 없이 리스트 하나로 바구니를 표현할 수 있다.

## 개선해볼 수 있는 코드

기존 코드는 `if stack:` 안에서 다시 `if stack[-1] == cur:`를 확인한다.
같은 로직을 조금 더 평평하게 쓰면 읽기 쉬워진다.

```python
def solution_refactored(board, moves):
    basket = []
    removed = 0

    for move in moves:
        col = move - 1

        for row in range(len(board)):
            doll = board[row][col]

            if doll == 0:
                continue

            board[row][col] = 0

            if basket and basket[-1] == doll:
                basket.pop()
                removed += 2
            else:
                basket.append(doll)

            break

    return removed
```

`doll == 0`이면 바로 `continue`로 넘기고, 인형을 찾은 뒤에는 바구니 처리만 집중해서 보면 된다.

## board를 직접 바꿀 때 테스트에서 주의할 점

이 풀이는 인형을 뽑은 뒤 아래처럼 `board`를 직접 수정한다.

```python
board[row][col] = 0
```

그래서 같은 `board`를 여러 테스트나 여러 함수에 그대로 넘기면 앞선 실행 결과가 뒤 실행에 영향을 줄 수 있다.

테스트에서는 `copy.deepcopy(board)`로 복사해서 넘기는 것이 안전하다.

```python
solution(copy.deepcopy(board), moves)
solution_refactored(copy.deepcopy(board), moves)
```

## 테스트 케이스

| 케이스 | expected | 설명 |
|---|---:|---|
| 공식 예제 | `4` | 같은 인형 두 쌍 제거 |
| 빈 열만 선택 | `0` | 아무 인형도 뽑히지 않음 |
| 같은 인형 연속 | `2` | 바로 한 쌍 제거 |
| 제거 없음 | `0` | 인형은 뽑히지만 같은 인형이 만나지 않음 |
| 여러 번 제거 | `4` | 두 쌍 제거 |

## 시간복잡도

시간복잡도는 `O(m * n)`이다.

여기서 `m`은 `moves`의 길이, `n`은 `board`의 행 개수다.
각 move마다 위에서 아래로 최대 `n`칸을 확인할 수 있다.

## 공간복잡도

공간복잡도는 `O(m)`이다.

최악의 경우 뽑은 인형이 제거되지 않고 모두 바구니에 쌓일 수 있다.

## 배운 점

- 마지막에 넣은 값과 비교해야 하면 스택을 떠올리자.
- Python 리스트는 `append()`와 `pop()`으로 스택처럼 사용할 수 있다.
- 문제의 열 번호가 1부터 시작하면 실제 인덱스는 `move - 1`이다.
- 상태를 바꾸는 문제에서는 `board[row][col] = 0`처럼 변경 지점을 명확히 해야 한다.
- 입력 배열을 직접 수정하는 함수는 테스트에서 `copy.deepcopy()`로 보호하자.

## 다음에 비슷한 문제를 만나면 떠올릴 신호

- “마지막 값과 비교”, “쌓인다”, “사라진다”가 나오면 스택을 먼저 생각하자.
- 2차원 배열에서 열을 선택하면 행을 위에서 아래로 순회해야 하는지 확인하자.
- 1-based 위치가 주어지면 0-based 인덱스로 바꾸는 `-1` 처리를 잊지 말자.
- 시뮬레이션 문제에서는 상태 변경이 언제 일어나는지 먼저 정리하자.

## 최종적으로 기억할 코드

```python
def solution_refactored(board, moves):
    basket = []
    removed = 0

    for move in moves:
        col = move - 1

        for row in range(len(board)):
            doll = board[row][col]

            if doll == 0:
                continue

            board[row][col] = 0

            if basket and basket[-1] == doll:
                basket.pop()
                removed += 2
            else:
                basket.append(doll)

            break

    return removed
```

## 마무리

Day6 첫 문제는 시뮬레이션과 스택을 함께 쓰는 문제였다.

처음 작성한 코드는 크레인이 인형을 뽑고, 바구니에서 같은 인형이 만나면 제거하는 흐름을 잘 구현했다.
개선 코드에서는 빈 칸 처리와 바구니 처리를 조금 더 분리해서 읽기 쉽게 정리했다.

앞으로 비슷한 시뮬레이션 문제가 나오면 “상태를 어디서 바꾸는지”와 “마지막 값만 보면 되는지”를 먼저 확인해야겠다.
