def solution(n):
    # 1부터 n까지 확인하면서 n을 나누어 떨어뜨리는 수만 더한다.
    answer = 0
    for i in range(1, n + 1):
        if n % i == 0:
            answer += i

    return answer


def solution_refactored(n):
    # 약수 조건을 만족하는 값만 제너레이터 표현식으로 만들고 sum()으로 더한다.
    return sum(i for i in range(1, n + 1) if n % i == 0)


if __name__ == "__main__":
    test_cases = [12, 5, 1, 16, 25, 2]

    for n in test_cases:
        original = solution(n)
        refactored = solution_refactored(n)
        print(f"n={n} -> original={original}, refactored={refactored}")
        assert original == refactored
