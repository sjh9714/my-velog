def solution(a, b):
    # 두 수 사이의 거리 홀짝에 따라 가운데 항 처리 방식을 나누어 합을 계산한다.
    answer = 0
    if abs(a - b) % 2:
        answer = ((abs(a - b) + 1) / 2) * (a + b)
    else:
        answer = (abs(a - b) / 2) * (a + b) + ((a + b) / 2)
    return int(answer)


def solution_refactored(a, b):
    # 등차수열 합 공식: 항의 개수 * (첫 항 + 마지막 항) // 2
    return (abs(a - b) + 1) * (a + b) // 2


if __name__ == "__main__":
    test_cases = [
        (3, 5),
        (3, 3),
        (5, 3),
        (-3, 1),
        (-5, -3),
        (0, 0),
    ]

    for a, b in test_cases:
        original = solution(a, b)
        refactored = solution_refactored(a, b)
        print(f"a={a}, b={b} -> original={original}, refactored={refactored}")
        assert original == refactored
