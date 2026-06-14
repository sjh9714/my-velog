def solution_partial(s):
    # split()은 연속 공백과 앞뒤 공백 정보를 잃어버려 일부 정확성 테스트에서 실패한다.
    answer = ""
    arr = s.split()
    for i in arr:
        for j in range(len(i)):
            if j % 2:
                answer += i[j].lower()
            else:
                answer += i[j].upper()
        answer += " "
    return answer.strip()


def solution(s):
    # 공백을 그대로 보존하면서 단어 안에서의 인덱스만 따로 관리한다.
    answer = []
    index = 0

    for char in s:
        if char == " ":
            answer.append(char)
            index = 0
        else:
            answer.append(char.upper() if index % 2 == 0 else char.lower())
            index += 1

    return "".join(answer)


def solution_refactored(s):
    # solution과 같은 흐름을 조금 더 설명적인 변수명으로 표현한다.
    result = []
    word_index = 0

    for char in s:
        if char == " ":
            result.append(char)
            word_index = 0
            continue

        if word_index % 2 == 0:
            result.append(char.upper())
        else:
            result.append(char.lower())
        word_index += 1

    return "".join(result)


if __name__ == "__main__":
    test_cases = [
        "try hello world",
        "hello",
        "a b c",
        "  hello",
        "hello  world",
        "hello ",
        "  multiple   spaces  ",
    ]

    for s in test_cases:
        original = solution(s)
        refactored = solution_refactored(s)
        print(f"s={s!r} -> original={original!r}, refactored={refactored!r}")
        assert original == refactored
