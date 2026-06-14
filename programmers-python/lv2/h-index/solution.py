def solution(citations):
    # 인용 횟수를 내림차순으로 정렬하고, rank번째 논문이 rank회 이상 인용됐는지 확인한다.
    citations.sort(reverse=True)

    answer = 0
    for i, citation in enumerate(citations, start=1):
        if citation >= i:
            answer = i

    return answer


def solution_refactored(citations):
    # sorted()를 사용해 원본 리스트를 바꾸지 않고 같은 조건을 확인한다.
    answer = 0

    for rank, citation in enumerate(sorted(citations, reverse=True), start=1):
        if citation >= rank:
            answer = rank

    return answer


if __name__ == "__main__":
    cases = [
        [3, 0, 6, 1, 5],
        [0, 0, 0],
        [10, 8, 5, 4, 3],
        [1],
    ]

    for citations in cases:
        original = solution(citations[:])
        refactored = solution_refactored(citations)
        print(citations, original, refactored, original == refactored)
