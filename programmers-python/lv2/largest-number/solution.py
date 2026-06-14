def solution(numbers):
    # 숫자를 문자열로 바꾼 뒤, 이어 붙였을 때 큰 순서가 되도록 반복 문자열을 기준으로 정렬한다.
    str_number = list(map(str, numbers))
    str_number.sort(key=lambda x: x * 3, reverse=True)
    answer = "".join(str_number)
    return "0" if answer[0] == "0" else answer


def solution_refactored(numbers):
    # 같은 풀이를 설명적인 변수명으로 정리한다.
    number_strings = list(map(str, numbers))
    number_strings.sort(key=lambda number: number * 3, reverse=True)

    answer = "".join(number_strings)
    return "0" if answer[0] == "0" else answer


if __name__ == "__main__":
    cases = [
        [6, 10, 2],
        [3, 30, 34, 5, 9],
        [0, 0, 0],
        [12, 121],
    ]

    for numbers in cases:
        original = solution(numbers)
        refactored = solution_refactored(numbers)
        print(numbers, original, refactored, original == refactored)
