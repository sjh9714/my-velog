def solution(s):
    # 대소문자를 구분하지 않기 위해 전체 문자열을 소문자로 바꾼 뒤 p와 y의 개수를 비교한다.
    text = s.lower()
    return text.count('p') == text.count('y')


def solution_one_liner(s):
    # 같은 아이디어를 한 줄로 표현한 풀이이다.
    return s.lower().count('p') == s.lower().count('y')


if __name__ == "__main__":
    test_cases = ["pPoooyY", "Pyy", "abc", "ppyy", "pyp", "PYpy"]

    for s in test_cases:
        original = solution(s)
        one_liner = solution_one_liner(s)
        print(f"s={s!r} -> original={original}, one_liner={one_liner}")
        assert original == one_liner
