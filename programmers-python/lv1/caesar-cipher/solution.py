def solution(s, n):
    # 공백은 그대로 두고, 대문자와 소문자는 각각의 ASCII 기준점에서 n칸 이동한다.
    answer = []

    for char in s:
        if char == " ":
            answer.append(char)
        elif "A" <= char <= "Z":
            answer.append(chr((ord(char) - 65 + n) % 26 + 65))
        else:
            answer.append(chr((ord(char) - 97 + n) % 26 + 97))

    return "".join(answer)


def solution_refactored(s, n):
    # 기준 문자를 helper 함수로 분리해서 대문자/소문자 처리 의도를 더 명확히 한다.
    def shift(char, base):
        return chr((ord(char) - ord(base) + n) % 26 + ord(base))

    answer = []

    for char in s:
        if char == " ":
            answer.append(char)
        elif char.isupper():
            answer.append(shift(char, "A"))
        else:
            answer.append(shift(char, "a"))

    return "".join(answer)


if __name__ == "__main__":
    test_cases = [
        ("AB", 1),
        ("z", 1),
        ("a B z", 4),
        ("Z", 1),
        ("Hello World", 5),
        ("A a Z z", 25),
        ("   ", 3),
    ]

    for s, n in test_cases:
        original = solution(s, n)
        refactored = solution_refactored(s, n)
        print(f"s={s!r}, n={n} -> original={original!r}, refactored={refactored!r}")
        assert original == refactored
