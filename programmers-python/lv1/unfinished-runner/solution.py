from collections import Counter


def solution_timeout(participant, completion):
    # 정확성은 통과하지만 remove()가 매번 리스트를 탐색해서 효율성 테스트에서 느려진다.
    for i in completion:
        participant.remove(i)
    return participant[0]


def solution(participant, completion):
    # Counter로 참가자 이름별 개수를 세고, 완주자 이름을 하나씩 빼서 남은 사람을 찾는다.
    counts = Counter(participant)

    for name in completion:
        counts[name] -= 1

    for name, count in counts.items():
        if count > 0:
            return name


def solution_with_dict(participant, completion):
    # Counter 없이 dict.get()으로 이름별 개수를 직접 관리한다.
    counts = {}

    for name in participant:
        counts[name] = counts.get(name, 0) + 1

    for name in completion:
        counts[name] -= 1

    for name, count in counts.items():
        if count > 0:
            return name


if __name__ == "__main__":
    test_cases = [
        (["leo", "kiki", "eden"], ["eden", "kiki"]),
        (
            ["marina", "josipa", "nikola", "vinko", "filipa"],
            ["josipa", "filipa", "marina", "nikola"],
        ),
        (["mislav", "stanko", "mislav", "ana"], ["stanko", "ana", "mislav"]),
    ]

    for participant, completion in test_cases:
        counter_result = solution(participant[:], completion[:])
        dict_result = solution_with_dict(participant[:], completion[:])
        print(
            f"participant={participant}, completion={completion} -> "
            f"counter={counter_result}, dict={dict_result}"
        )
        assert counter_result == dict_result
