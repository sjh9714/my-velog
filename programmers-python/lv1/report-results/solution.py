def solution(id_list, report, k):
    # 신고자별 신고 대상은 set으로 저장해 같은 유저에 대한 중복 신고를 한 번만 센다.
    answer = []
    id_dict = {}
    reported_count = {}

    for i in id_list:
        id_dict[i] = set()
        reported_count[i] = 0

    for i in report:
        user, reported_user = i.split()
        id_dict[user].add(reported_user)

    for i in id_list:
        for reported_user in id_dict[i]:
            reported_count[reported_user] += 1

    for i in id_list:
        mail_count = 0
        for reported_user in id_dict[i]:
            if reported_count[reported_user] >= k:
                mail_count += 1
        answer.append(mail_count)

    return answer


def solution_refactored(id_list, report, k):
    # 전체 신고 목록에서 중복을 먼저 제거한 뒤, 신고 횟수와 메일 수를 각각 계산한다.
    unique_reports = set(report)
    reported_count = {user_id: 0 for user_id in id_list}
    mail_count = {user_id: 0 for user_id in id_list}

    for item in unique_reports:
        _, reported_user = item.split()
        reported_count[reported_user] += 1

    suspended_users = {user_id for user_id, count in reported_count.items() if count >= k}

    for item in unique_reports:
        user, reported_user = item.split()
        if reported_user in suspended_users:
            mail_count[user] += 1

    return [mail_count[user_id] for user_id in id_list]


if __name__ == "__main__":
    cases = [
        (
            ["muzi", "frodo", "apeach", "neo"],
            ["muzi frodo", "apeach frodo", "frodo neo", "muzi neo", "apeach muzi"],
            2,
        ),
        (
            ["con", "ryan"],
            ["ryan con", "ryan con", "ryan con", "ryan con"],
            3,
        ),
    ]

    for id_list, report, k in cases:
        original = solution(id_list, report, k)
        refactored = solution_refactored(id_list, report, k)
        print(id_list, original, refactored, original == refactored)
