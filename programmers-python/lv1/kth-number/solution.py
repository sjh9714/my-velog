def solution(array, commands):
    # 각 command가 지정한 구간을 자르고 정렬한 뒤, k번째 값을 결과에 담는다.
    answer = []
    for i in commands:
        sliced_array = sorted(array[i[0] - 1:i[1]])
        answer.append(sliced_array[i[2] - 1])
    return answer


def solution_refactored(array, commands):
    # command를 start, end, k로 구조분해해 slicing 기준을 더 명확히 표현한다.
    return [sorted(array[start - 1:end])[k - 1] for start, end, k in commands]


if __name__ == "__main__":
    cases = [
        ([1, 5, 2, 6, 3, 7, 4], [[2, 5, 3], [4, 4, 1], [1, 7, 3]]),
        ([1, 2, 3, 4, 5], [[1, 5, 2], [2, 4, 3]]),
        ([9, 8, 7, 6], [[1, 4, 1], [1, 4, 4]]),
    ]

    for array, commands in cases:
        original = solution(array, commands)
        refactored = solution_refactored(array, commands)
        print(array, commands, original, refactored, original == refactored)
