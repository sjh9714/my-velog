# 크레인 인형뽑기 게임

## 문제 요약

2차원 배열 `board`와 크레인의 이동 위치 `moves`가 주어진다.
각 이동마다 해당 열에서 가장 위에 있는 인형을 뽑아 바구니에 넣는다.

바구니의 마지막 인형과 새로 뽑은 인형이 같으면 두 인형이 사라지고, 사라진 인형의 개수를 반환한다.

문제 링크: https://school.programmers.co.kr/learn/courses/30/lessons/64061

## 접근 방식

각 `move`는 열 번호를 의미한다.
문제의 열 번호는 1부터 시작하므로 실제 인덱스로 사용할 때는 `move - 1`을 사용한다.

각 열에서 위에서 아래로 내려가며 0이 아닌 값을 찾고, 인형을 뽑으면 해당 칸을 0으로 바꾼다.
바구니는 마지막 값과 비교해야 하므로 스택처럼 사용한다.

## 핵심 코드

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

## 개선한 코드

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

## 시간복잡도

O(m * n)

`m`은 moves의 길이, `n`은 board의 행 개수다.
각 move마다 위에서 아래로 최대 n칸을 확인한다.

## 공간복잡도

O(m)

뽑은 인형을 담는 바구니가 필요하다.

## 배운 점

- 마지막 값과 새 값을 비교해야 하는 문제에서는 스택을 떠올릴 수 있다.
- 문제의 위치 번호가 1부터 시작하면 인덱스로 바꿀 때 `move - 1`이 필요하다.
- 인형을 뽑은 뒤에는 `board[row][col] = 0`으로 상태를 갱신해야 한다.
- 함수가 입력 배열을 직접 바꾸면 테스트에서는 `copy.deepcopy()`로 복사해서 검증하는 것이 안전하다.
