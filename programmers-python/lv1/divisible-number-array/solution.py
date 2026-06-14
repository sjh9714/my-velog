def solution(arr, divisor):
    # 배열을 오름차순으로 정렬한 뒤 divisor로 나누어 떨어지는 값만 answer에 담는다.
    answer = []
    arr.sort()
    for i in arr:
        if i % divisor == 0:
            answer.append(i)
    return answer if answer else [-1]


def solution_refactored(arr, divisor):
    # sorted()와 리스트 컴프리헨션으로 정렬과 조건 필터링을 한 번에 표현한다.
    answer = [num for num in sorted(arr) if num % divisor == 0]
    return answer if answer else [-1]


if __name__ == "__main__":
    test_cases = [
        ([5, 9, 7, 10], 5),
        ([2, 36, 1, 3], 1),
        ([3, 2, 6], 10),
        ([1, 3, 5, 7], 3),
    ]

    for arr, divisor in test_cases:
        original = solution(arr[:], divisor)
        refactored = solution_refactored(arr[:], divisor)
        print(
            f"arr={arr}, divisor={divisor} -> "
            f"original={original}, refactored={refactored}"
        )
        assert original == refactored
