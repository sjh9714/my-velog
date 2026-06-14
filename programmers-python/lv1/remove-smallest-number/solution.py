def solution(arr):
    # 정렬된 배열의 첫 번째 값으로 최솟값을 찾고, 원본 배열에서 그 값을 제거한다.
    arr_c = sorted(arr)
    arr.pop(arr.index(arr_c[0]))
    return arr if arr else [-1]


def solution_refactored(arr):
    # min()으로 최솟값만 찾은 뒤, 최솟값이 아닌 원소만 새 리스트에 담는다.
    if len(arr) == 1:
        return [-1]

    min_value = min(arr)
    return [num for num in arr if num != min_value]


if __name__ == "__main__":
    test_cases = [
        [4, 3, 2, 1],
        [10],
        [1, 2, 3, 4],
        [2, 1],
        [5, 3, 7, 2],
    ]

    for arr in test_cases:
        original = solution(arr[:])
        refactored = solution_refactored(arr[:])
        print(f"arr={arr} -> original={original}, refactored={refactored}")
        assert original == refactored
