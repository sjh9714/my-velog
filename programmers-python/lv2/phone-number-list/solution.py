def solution_failed(phone_book):
    # 실패 풀이: 순회 중 같은 리스트를 수정하고, 모든 번호를 반복 비교해 효율성도 불리하다.
    for i in phone_book:
        phone_book.remove(i)
        phone_book_tuple = tuple(phone_book)
        if i.startswith(phone_book_tuple):
            return False
        phone_book.append(i)
    return True


def solution(phone_book):
    # 정렬하면 접두어 관계가 있는 번호들이 서로 이웃하므로 인접한 번호만 비교한다.
    sorted_phone_book = sorted(phone_book)

    for i in range(len(sorted_phone_book) - 1):
        if sorted_phone_book[i + 1].startswith(sorted_phone_book[i]):
            return False

    return True


def solution_refactored(phone_book):
    # 같은 로직을 all()로 표현한다. 모든 인접 쌍이 접두어 관계가 아니어야 True다.
    sorted_phone_book = sorted(phone_book)

    return all(
        not sorted_phone_book[i + 1].startswith(sorted_phone_book[i])
        for i in range(len(sorted_phone_book) - 1)
    )


if __name__ == "__main__":
    cases = [
        ["119", "97674223", "1195524421"],
        ["123", "456", "789"],
        ["12", "123", "1235", "567", "88"],
        ["1", "11"],
    ]

    for phone_book in cases:
        original = solution(phone_book[:])
        refactored = solution_refactored(phone_book[:])
        print(phone_book, original, refactored, original == refactored)
