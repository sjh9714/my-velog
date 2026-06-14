def solution(s):
    # 숫자 문자열과 영어 단어를 같은 인덱스에 두고, 영어 단어를 숫자 문자로 치환한다.
    num = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    text = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]

    for i in range(len(num)):
        s = s.replace(text[i], num[i])

    return int(s)


def solution_refactored(s):
    # enumerate()로 숫자와 영어 단어를 함께 꺼내서 인덱스의 의미를 더 명확히 한다.
    number_words = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]

    for digit, word in enumerate(number_words):
        s = s.replace(word, str(digit))

    return int(s)


if __name__ == "__main__":
    test_cases = [
        "one4seveneight",
        "23four5six7",
        "2three45sixseven",
        "123",
        "zero",
        "zero9eight",
    ]

    for s in test_cases:
        original = solution(s)
        refactored = solution_refactored(s)
        print(f"s={s!r} -> original={original}, refactored={refactored}")
        assert original == refactored
