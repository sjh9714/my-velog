def solution(nums):
    # 중복을 제거한 종류 수와 고를 수 있는 마리 수를 비교한다.
    set_p = set(nums)
    return len(nums) // 2 if len(nums) / 2 < len(set_p) else len(set_p)


def solution_refactored(nums):
    # 정답은 고를 수 있는 마리 수와 서로 다른 종류 수 중 더 작은 값이다.
    return min(len(nums) // 2, len(set(nums)))


if __name__ == "__main__":
    test_cases = [
        [3, 1, 2, 3],
        [3, 3, 3, 2, 2, 4],
        [3, 3, 3, 2, 2, 2],
        [1, 2, 3, 4],
        [1, 1],
        [1, 2, 1, 2],
    ]

    for nums in test_cases:
        original = solution(nums)
        refactored = solution_refactored(nums)
        print(f"nums={nums} -> original={original}, refactored={refactored}")
        assert original == refactored
