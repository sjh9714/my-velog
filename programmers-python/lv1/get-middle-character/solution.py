def solution(s):
    # 문자열 길이의 절반 인덱스를 기준으로 홀수면 한 글자, 짝수면 두 글자를 반환한다.
    mid = len(s) // 2

    if len(s) % 2:
        return s[mid]

    return s[mid - 1:mid + 1]


def solution_refactored(s):
    # 홀수와 짝수 모두 처리할 수 있도록 시작/끝 인덱스를 슬라이싱 공식으로 계산한다.
    return s[(len(s) - 1) // 2:len(s) // 2 + 1]


if __name__ == "__main__":
    test_cases = ["abcde", "qwer", "a", "ab", "hello", "python"]

    for s in test_cases:
        original = solution(s)
        refactored = solution_refactored(s)
        print(f"s={s!r} -> original={original!r}, refactored={refactored!r}")
        assert original == refactored
