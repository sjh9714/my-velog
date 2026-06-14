def solution(n):
    # 정수를 문자열로 바꾼 뒤 각 자릿수를 리스트에 담고 내림차순으로 정렬한다.
    answer = ""
    arr = []
    text = str(n)
    for i in text:
        arr.append(i)
    arr.sort(reverse=True)
    for i in arr:
        answer += i
    return int(answer)


def solution_refactored(n):
    # sorted()와 join()으로 자릿수 정렬과 문자열 합치기를 한 줄로 표현한다.
    return int("".join(sorted(str(n), reverse=True)))


if __name__ == "__main__":
    test_cases = [118372, 15, 1000000, 9876543210, 10200, 999]

    for n in test_cases:
        original = solution(n)
        refactored = solution_refactored(n)
        print(f"n={n} -> original={original}, refactored={refactored}")
        assert original == refactored
