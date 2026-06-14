import math


def solution(n, m):
    # math 모듈의 최대공약수/최소공배수 함수를 사용해서 바로 결과를 만든다.
    return [gcd(n, m), lcm(n, m)]


def gcd(n, m):
    return math.gcd(n, m)


def lcm(n, m):
    return math.lcm(n, m)


def solution_refactored(n, m):
    # 최소공배수는 두 수의 곱을 최대공약수로 나누어 구할 수 있다.
    gcd_value = math.gcd(n, m)
    lcm_value = n * m // gcd_value
    return [gcd_value, lcm_value]


if __name__ == "__main__":
    test_cases = [
        (3, 12),
        (2, 5),
        (6, 6),
        (4, 8),
        (9, 27),
        (14, 21),
    ]

    for n, m in test_cases:
        original = solution(n, m)
        refactored = solution_refactored(n, m)
        print(f"n={n}, m={m} -> original={original}, refactored={refactored}")
        assert original == refactored
