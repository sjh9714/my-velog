def solution_failed(lottos, win_nums):
    # 테스트 15번에서 실패한 풀이: 전체가 0이면 최고 순위가 0등처럼 계산된다.
    answer = []
    rank = 7
    zero = 0
    for i in lottos:
        if i in win_nums:
            rank -= 1
        elif i == 0:
            zero += 1
    return [rank - zero, rank] if rank < 7 else [rank - zero - 1, rank - 1]


def get_rank(count):
    # 맞힌 개수 0개와 1개는 모두 6등이고, 2개부터는 7 - count로 순위를 계산한다.
    return 6 if count < 2 else 7 - count


def solution(lottos, win_nums):
    # 0은 모두 맞을 수도 있고 모두 틀릴 수도 있으므로, 현재 맞힌 개수와 0의 개수를 따로 센다.
    match_count = 0
    zero_count = 0

    for number in lottos:
        if number == 0:
            zero_count += 1
        elif number in win_nums:
            match_count += 1

    best_count = match_count + zero_count
    worst_count = match_count

    return [get_rank(best_count), get_rank(worst_count)]


def solution_refactored(lottos, win_nums):
    # 당첨 번호 조회는 set으로 명확하게 처리하고, 같은 순위 변환 함수를 재사용한다.
    win_set = set(win_nums)
    zero_count = lottos.count(0)
    match_count = sum(1 for number in lottos if number in win_set)

    return [get_rank(match_count + zero_count), get_rank(match_count)]


if __name__ == "__main__":
    cases = [
        ([44, 1, 0, 0, 31, 25], [31, 10, 45, 1, 6, 19]),
        ([0, 0, 0, 0, 0, 0], [38, 19, 20, 40, 15, 25]),
        ([45, 4, 35, 20, 3, 9], [20, 9, 3, 45, 4, 35]),
    ]

    for lottos, win_nums in cases:
        original = solution(lottos, win_nums)
        refactored = solution_refactored(lottos, win_nums)
        print(lottos, win_nums, original, refactored, original == refactored)
