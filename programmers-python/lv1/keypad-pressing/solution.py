def solution(numbers, hand):
    # 키패드를 좌표로 표현하고, 가운데 열 숫자는 양손의 거리와 주 손잡이로 결정한다.
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


def solution_refactored(numbers, hand):
    # 맨해튼 거리 계산을 함수로 분리하고, 결과 문자는 리스트에 모아 마지막에 합친다.
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


if __name__ == "__main__":
    cases = [
        ([1, 3, 4, 5, 8, 2, 1, 4, 5, 9, 5], "right"),
        ([7, 0, 8, 2, 8, 3, 1, 5, 7, 6, 2], "left"),
        ([1, 2, 3, 4, 5, 6, 7, 8, 9, 0], "right"),
    ]

    for numbers, hand in cases:
        original = solution(numbers, hand)
        refactored = solution_refactored(numbers, hand)
        print(numbers, hand, original, refactored, original == refactored)
