def solution_failed(num):
    # 처음 작성한 풀이: num이 처음부터 1인 경우를 반복문 전에 처리하지 못한다.
    index = 0
    while index < 500:
        if num % 2:
            num = num * 3 + 1
        else:
            num /= 2
        index += 1
        if num == 1:
            return index
    return -1


def solution(num):
    # 반복문 시작 조건에서 num == 1을 먼저 확인하고, 나눗셈은 정수 나눗셈으로 유지한다.
    count = 0

    while num != 1:
        if count == 500:
            return -1

        if num % 2:
            num = num * 3 + 1
        else:
            num //= 2

        count += 1

    return count


def solution_refactored(num):
    # 최대 500번 반복이라는 조건을 for range(500)으로 직접 표현한다.
    for count in range(500):
        if num == 1:
            return count

        if num % 2:
            num = num * 3 + 1
        else:
            num //= 2

    return -1


if __name__ == "__main__":
    test_cases = [6, 16, 626331, 1, 2, 3]

    for num in test_cases:
        result = solution(num)
        refactored = solution_refactored(num)
        print(f"num={num} -> result={result}, refactored={refactored}")
        assert result == refactored
