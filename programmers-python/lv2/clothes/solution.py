def solution(clothes):
    # 종류별로 옷 이름을 모은 뒤, 각 종류에서 입지 않는 경우까지 함께 계산한다.
    clothes_dict = {}
    for i in clothes:
        clothes_dict.setdefault(i[1], []).append(i[0])

    answer = 1
    for i in list(clothes_dict.values()):
        answer *= len(i) + 1

    return answer - 1


def solution_refactored(clothes):
    # 실제 옷 이름은 필요 없으므로 종류별 개수만 세어 곱의 법칙을 적용한다.
    counts = {}

    for _, category in clothes:
        counts[category] = counts.get(category, 0) + 1

    answer = 1
    for count in counts.values():
        answer *= count + 1

    return answer - 1


if __name__ == "__main__":
    cases = [
        [
            ["yellow_hat", "headgear"],
            ["blue_sunglasses", "eyewear"],
            ["green_turban", "headgear"],
        ],
        [
            ["crow_mask", "face"],
            ["blue_sunglasses", "face"],
            ["smoky_makeup", "face"],
        ],
        [
            ["hat", "headgear"],
            ["shirt", "top"],
            ["jeans", "bottom"],
        ],
    ]

    for clothes in cases:
        original = solution(clothes)
        refactored = solution_refactored(clothes)
        print(clothes, original, refactored, original == refactored)
