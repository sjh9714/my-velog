# [DAY6] [프로그래머스/Python] 키패드 누르기 - 좌표와 거리 계산으로 손가락 위치 추적하기

## 문제 요약

숫자 배열 `numbers`와 주 손잡이 `hand`가 주어진다.

각 숫자를 누를 때 어느 손을 사용했는지 문자열로 반환해야 한다.

- `1`, `4`, `7`은 왼손으로 누른다.
- `3`, `6`, `9`는 오른손으로 누른다.
- `2`, `5`, `8`, `0`은 현재 양손 위치에서 더 가까운 손으로 누른다.
- 거리가 같으면 `hand`에 따라 왼손 또는 오른손을 사용한다.

문제 링크: [키패드 누르기](https://school.programmers.co.kr/learn/courses/30/lessons/67256)

## 처음 생각한 접근

처음에는 키패드를 실제 모양 그대로 좌표로 바꾸면 되겠다고 생각했다.

예를 들어 `1`은 `(0, 0)`, `2`는 `(0, 1)`, `3`은 `(0, 2)`처럼 표현할 수 있다.
그러면 손가락이 목표 숫자까지 얼마나 떨어져 있는지 행 차이와 열 차이로 계산할 수 있다.

키패드를 좌표로 바꾸면 손가락 이동 거리는 행 차이와 열 차이의 합으로 계산할 수 있다.

## 내가 작성한 코드

```python
def solution(numbers, hand):
    answer = ''

    keypad = {
        1: (0, 0), 2: (0, 1), 3: (0, 2),
        4: (1, 0), 5: (1, 1), 6: (1, 2),
        7: (2, 0), 8: (2, 1), 9: (2, 2),
        '*': (3, 0), 0: (3, 1), '#': (3, 2),
    }

    left_pos = keypad['*']
    right_pos = keypad['#']

    for number in numbers:
        if number in (1, 4, 7):
            answer += 'L'
            left_pos = keypad[number]
        elif number in (3, 6, 9):
            answer += 'R'
            right_pos = keypad[number]
        else:
            target = keypad[number]
            left_dist = abs(left_pos[0] - target[0]) + abs(left_pos[1] - target[1])
            right_dist = abs(right_pos[0] - target[0]) + abs(right_pos[1] - target[1])

            if left_dist < right_dist:
                answer += 'L'
                left_pos = target
            elif right_dist < left_dist:
                answer += 'R'
                right_pos = target
            elif hand == 'left':
                answer += 'L'
                left_pos = target
            else:
                answer += 'R'
                right_pos = target

    return answer
```

## 코드 설명

먼저 키패드의 각 숫자와 특수 문자를 좌표로 저장했다.

```python
keypad = {
    1: (0, 0), 2: (0, 1), 3: (0, 2),
    4: (1, 0), 5: (1, 1), 6: (1, 2),
    7: (2, 0), 8: (2, 1), 9: (2, 2),
    '*': (3, 0), 0: (3, 1), '#': (3, 2),
}
```

처음 왼손은 `*`, 오른손은 `#` 위치에서 시작한다.

```python
left_pos = keypad['*']
right_pos = keypad['#']
```

왼쪽 열 숫자는 무조건 왼손으로 누르고, 오른쪽 열 숫자는 무조건 오른손으로 누른다.

```python
if number in (1, 4, 7):
    answer += 'L'
    left_pos = keypad[number]
elif number in (3, 6, 9):
    answer += 'R'
    right_pos = keypad[number]
```

가운데 열 숫자는 양손의 현재 위치와 목표 위치 사이의 거리를 비교한다.

```python
left_dist = abs(left_pos[0] - target[0]) + abs(left_pos[1] - target[1])
right_dist = abs(right_pos[0] - target[0]) + abs(right_pos[1] - target[1])
```

거리가 더 짧은 손을 사용하고, 거리가 같을 때만 `hand` 값을 사용한다.

```python
elif hand == 'left':
    answer += 'L'
    left_pos = target
else:
    answer += 'R'
    right_pos = target
```

가운데 열의 숫자는 왼손과 오른손의 현재 위치를 비교해야 하므로, 매번 손가락 위치를 갱신하는 것이 중요했다.

## 좋았던 점

처음 작성한 풀이는 문제를 좌표 문제로 잘 바꿨다.

키패드의 모양을 그대로 딕셔너리에 담아두니, 각 숫자의 위치를 빠르게 찾을 수 있었다.
또 왼쪽 열, 오른쪽 열, 가운데 열을 나눠서 처리한 점도 문제 조건과 잘 맞았다.

특히 가운데 열에서 거리 비교 후 손가락 위치를 갱신한 부분이 핵심이었다.

## 거리 계산을 좌표로 생각하기

손가락은 대각선으로 이동하지 않는다.
상하좌우로만 움직일 수 있다.

그래서 두 좌표 사이의 거리는 아래처럼 계산한다.

```python
abs(current_row - target_row) + abs(current_col - target_col)
```

이런 거리를 맨해튼 거리라고 한다.

예를 들어 왼손이 `*`에 있고 `2`를 눌러야 한다면 좌표는 이렇게 된다.

```text
* = (3, 0)
2 = (0, 1)
거리 = abs(3 - 0) + abs(0 - 1) = 4
```

키패드처럼 격자 위에서 상하좌우로 움직이는 문제에서는 좌표와 맨해튼 거리를 먼저 떠올리면 좋다.

## 개선해볼 수 있는 코드

기존 코드는 거리 계산식이 그대로 들어가 있어서 조금 길게 느껴질 수 있다.
거리 계산을 함수로 분리하면 의도가 더 잘 보인다.

또 정답 문자열을 `+=`로 계속 붙이는 대신 리스트에 담아두고 마지막에 `join()`으로 합칠 수 있다.

```python
def solution_refactored(numbers, hand):
    keypad = {
        1: (0, 0), 2: (0, 1), 3: (0, 2),
        4: (1, 0), 5: (1, 1), 6: (1, 2),
        7: (2, 0), 8: (2, 1), 9: (2, 2),
        '*': (3, 0), 0: (3, 1), '#': (3, 2),
    }

    def distance(pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    answer = []
    left_pos = keypad['*']
    right_pos = keypad['#']

    for number in numbers:
        if number in (1, 4, 7):
            answer.append('L')
            left_pos = keypad[number]
            continue

        if number in (3, 6, 9):
            answer.append('R')
            right_pos = keypad[number]
            continue

        target = keypad[number]
        left_dist = distance(left_pos, target)
        right_dist = distance(right_pos, target)

        if left_dist < right_dist or (left_dist == right_dist and hand == 'left'):
            answer.append('L')
            left_pos = target
        else:
            answer.append('R')
            right_pos = target

    return ''.join(answer)
```

## 동률일 때 hand를 사용하는 이유

가운데 열 숫자는 기본적으로 더 가까운 손으로 누른다.

하지만 양손의 거리가 같으면 거리만으로는 어느 손을 쓸지 결정할 수 없다.
이때 문제에서 주어진 주 손잡이 `hand`를 사용한다.

즉, `hand`는 항상 쓰는 값이 아니라 두 손의 거리가 같을 때만 쓰는 조건이다.

두 손의 거리가 같을 때만 `hand` 값을 사용한다.

## 테스트 케이스

| numbers | hand | expected |
|---|---|---|
| `[1,3,4,5,8,2,1,4,5,9,5]` | `"right"` | `"LRLLLRLLRRL"` |
| `[7,0,8,2,8,3,1,5,7,6,2]` | `"left"` | `"LRLLRRLLLRR"` |
| `[1,2,3,4,5,6,7,8,9,0]` | `"right"` | `"LLRLLRLLRL"` |
| `[1,4,7]` | `"right"` | `"LLL"` |
| `[3,6,9]` | `"left"` | `"RRR"` |
| `[2]` | `"left"` | `"L"` |
| `[2]` | `"right"` | `"R"` |

## 시간복잡도

시간복잡도는 `O(n)`이다.

`n`은 `numbers`의 길이다.
각 숫자마다 딕셔너리 조회와 거리 계산을 상수 시간 안에 처리한다.

## 공간복잡도

공간복잡도는 `O(n)`이다.

정답을 저장하는 리스트가 필요하다.
키패드 좌표 딕셔너리는 크기가 고정되어 있으므로 `O(1)`로 볼 수 있다.

## 배운 점

- 키패드나 격자 문제는 좌표로 바꾸면 생각하기 쉬워진다.
- 상하좌우 이동 거리는 행 차이와 열 차이의 합으로 계산한다.
- 왼손과 오른손의 현재 위치처럼 상태가 바뀌는 값은 매번 갱신해야 한다.
- 동률 조건은 마지막에 따로 처리하면 실수를 줄일 수 있다.
- 문자열을 계속 붙이는 것보다 리스트에 모은 뒤 `join()`하는 방식도 기억해두자.

## 다음에 비슷한 문제를 만나면 떠올릴 신호

- 키패드, 격자, 위치 이동이 나오면 좌표 변환을 먼저 생각하자.
- “더 가까운 위치”를 비교해야 하면 맨해튼 거리를 떠올리자.
- 현재 위치가 계속 바뀌면 상태 갱신 시점을 먼저 정리하자.
- 동률 조건이 있으면 일반 조건보다 나중에 처리하자.

## 최종적으로 기억할 코드

```python
def solution_refactored(numbers, hand):
    keypad = {
        1: (0, 0), 2: (0, 1), 3: (0, 2),
        4: (1, 0), 5: (1, 1), 6: (1, 2),
        7: (2, 0), 8: (2, 1), 9: (2, 2),
        '*': (3, 0), 0: (3, 1), '#': (3, 2),
    }

    def distance(pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    answer = []
    left_pos = keypad['*']
    right_pos = keypad['#']

    for number in numbers:
        if number in (1, 4, 7):
            answer.append('L')
            left_pos = keypad[number]
            continue

        if number in (3, 6, 9):
            answer.append('R')
            right_pos = keypad[number]
            continue

        target = keypad[number]
        left_dist = distance(left_pos, target)
        right_dist = distance(right_pos, target)

        if left_dist < right_dist or (left_dist == right_dist and hand == 'left'):
            answer.append('L')
            left_pos = target
        else:
            answer.append('R')
            right_pos = target

    return ''.join(answer)
```

## 마무리

Day6 두 번째 문제는 키패드를 좌표로 바꾸는 순간 훨씬 단순해지는 구현 문제였다.

처음 작성한 코드는 문제 조건을 그대로 잘 옮겼고, 개선 코드에서는 거리 계산을 함수로 분리해서 읽기 쉽게 정리했다.

앞으로 위치 이동 문제가 나오면 먼저 좌표로 바꿀 수 있는지 보고, 거리 계산과 상태 갱신을 차분히 분리해야겠다.
