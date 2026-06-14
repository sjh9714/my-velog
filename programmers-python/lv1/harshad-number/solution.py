def solution(x):
    # 정수를 문자열로 바꾼 뒤 각 자릿수를 더해서 x가 그 합으로 나누어지는지 확인한다.
    arr = list(str(x))
    s = 0
    for i in arr:
        s += int(i)
    return False if x % s else True


def solution_refactored(x):
    # sum()과 map()으로 자릿수 합을 더 간결하게 구한다.
    digit_sum = sum(map(int, str(x)))
    return x % digit_sum == 0


if __name__ == "__main__":
    test_cases = [10, 12, 11, 13, 18, 100, 101]

    for x in test_cases:
        original = solution(x)
        refactored = solution_refactored(x)
        print(f"x={x} -> original={original}, refactored={refactored}")
        assert original == refactored
