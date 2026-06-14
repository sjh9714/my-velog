def solution(board, moves):
    # 크레인으로 각 열의 가장 위 인형을 뽑고, 바구니의 마지막 인형과 같으면 제거한다.
    stack = []
    result = 0
    for move in moves:
        for i in range(len(board)):
            cur = board[i][move - 1]
            if cur != 0:
                if stack:
                    if stack[-1] == cur:
                        stack.pop()
                        result += 2
                    else:
                        stack.append(cur)
                else:
                    stack.append(cur)
                board[i][move - 1] = 0
                break
    return result


def solution_refactored(board, moves):
    # 빈 칸은 건너뛰고, 인형을 뽑은 뒤 바구니 처리 흐름을 한 번만 분기한다.
    basket = []
    removed = 0

    for move in moves:
        col = move - 1

        for row in range(len(board)):
            doll = board[row][col]

            if doll == 0:
                continue

            board[row][col] = 0

            if basket and basket[-1] == doll:
                basket.pop()
                removed += 2
            else:
                basket.append(doll)

            break

    return removed


if __name__ == "__main__":
    import copy

    test_cases = [
        (
            [
                [0, 0, 0, 0, 0],
                [0, 0, 1, 0, 3],
                [0, 2, 5, 0, 1],
                [4, 2, 4, 4, 2],
                [3, 5, 1, 3, 1],
            ],
            [1, 5, 3, 5, 1, 2, 1, 4],
        ),
        ([[0, 0], [0, 0]], [1, 2, 1]),
        ([[1, 1], [0, 0]], [1, 2]),
    ]

    for board, moves in test_cases:
        original = solution(copy.deepcopy(board), moves)
        refactored = solution_refactored(copy.deepcopy(board), moves)
        print(f"moves={moves} -> original={original}, refactored={refactored}")
        assert original == refactored
