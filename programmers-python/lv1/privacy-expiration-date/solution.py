def solution(today, terms, privacies):
    # 모든 날짜를 28일 기준의 일수로 바꾼 뒤, 유효기간이 지난 개인정보 번호를 찾는다.
    answer = []
    terms_dict = {}

    for i in terms:
        a, n = i.split()
        terms_dict[a] = int(n)

    def to_days(date):
        y, m, d = map(int, date.split("."))
        return y * 12 * 28 + m * 28 + d

    today_days = to_days(today)
    index = 0
    for i in privacies:
        index += 1
        d, a = i.split()
        if to_days(d) + terms_dict[a] * 28 <= today_days:
            answer.append(index)

    return answer


def solution_refactored(today, terms, privacies):
    # enumerate로 개인정보 번호를 함께 순회해 수동 index 증가를 줄인다.
    term_months = {}

    for term in terms:
        term_type, month = term.split()
        term_months[term_type] = int(month)

    def to_days(date):
        year, month, day = map(int, date.split("."))
        return year * 12 * 28 + month * 28 + day

    today_days = to_days(today)
    expired_privacies = []

    for index, privacy in enumerate(privacies, start=1):
        collected_date, term_type = privacy.split()
        expiration_days = to_days(collected_date) + term_months[term_type] * 28

        if expiration_days <= today_days:
            expired_privacies.append(index)

    return expired_privacies


if __name__ == "__main__":
    cases = [
        (
            "2022.05.19",
            ["A 6", "B 12", "C 3"],
            ["2021.05.02 A", "2021.07.01 B", "2022.02.19 C", "2022.02.20 C"],
        ),
        (
            "2020.01.01",
            ["Z 3", "D 5"],
            ["2019.01.01 D", "2019.11.15 Z", "2019.08.02 D", "2019.07.01 D", "2018.12.28 Z"],
        ),
    ]

    for today, terms, privacies in cases:
        original = solution(today, terms, privacies)
        refactored = solution_refactored(today, terms, privacies)
        print(today, original, refactored, original == refactored)
