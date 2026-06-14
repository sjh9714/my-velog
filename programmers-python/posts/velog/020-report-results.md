# [DAY8] [프로그래머스/Python] 신고 결과 받기 - set과 dict로 중복 신고 처리하기

## 문제 요약

유저 목록 `id_list`, 신고 기록 `report`, 정지 기준 `k`가 주어진다.

각 신고 기록은 `"신고한 유저 신고당한 유저"` 형태의 문자열이다.
한 유저가 같은 유저를 여러 번 신고해도 신고 횟수는 1번으로 처리된다.

정지 기준 `k`번 이상 신고당한 유저가 정지되고, 각 유저는 자신이 신고한 유저 중 정지된 유저 수만큼 결과 메일을 받는다.

문제 링크: [신고 결과 받기](https://school.programmers.co.kr/learn/courses/30/lessons/92334)

## 처음 생각한 접근

처음에는 신고한 사람을 기준으로 생각했다.

예를 들어 `muzi`가 `frodo`와 `neo`를 신고했다면, `muzi`가 신고한 사람 목록을 따로 저장해두는 방식이다.
그런데 중복 신고는 한 번만 인정되므로 리스트보다는 `set`이 더 잘 맞았다.

그래서 신고자별 신고 대상은 `dict`와 `set`으로 관리했다.

## 내가 작성한 코드

```python
def solution(id_list, report, k):
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
```

## 코드 설명

먼저 모든 유저에 대해 두 개의 딕셔너리를 초기화했다.

```python
id_dict[i] = set()
reported_count[i] = 0
```

`id_dict`에는 각 유저가 신고한 사람들을 저장한다.
이때 값이 `set`이기 때문에 같은 신고가 여러 번 들어와도 한 번만 남는다.

```python
user, reported_user = i.split()
id_dict[user].add(reported_user)
```

그다음 신고자별 신고 목록을 다시 돌면서, 신고당한 유저의 횟수를 올린다.

```python
reported_count[reported_user] += 1
```

마지막으로 각 유저가 신고한 사람 중 신고 횟수가 `k` 이상인 사람만 세어 메일 수를 구했다.

```python
if reported_count[reported_user] >= k:
    mail_count += 1
```

## 좋았던 점

이 풀이에서 좋았던 점은 중복 신고를 `set`으로 자연스럽게 처리했다는 점이다.

같은 유저가 같은 유저를 여러 번 신고해도 신고 횟수는 1번으로 처리해야 한다.
이 조건을 직접 `if`로 검사하지 않아도, `set.add()`를 사용하면 같은 값은 한 번만 저장된다.

또 신고당한 횟수 계산과 메일 수 계산을 나눠서 처리한 점도 좋았다.
한 번에 모든 것을 계산하려고 하면 헷갈릴 수 있는데, 단계를 나누면 문제 조건이 더 잘 보인다.

## 중복 신고를 왜 제거해야 하는가

이 문제는 신고 목록을 그대로 세는 문제가 아니라, 중복을 제거한 신고 관계를 기준으로 정지 여부와 메일 수를 계산하는 문제였다.

예를 들어 아래처럼 `ryan`이 `con`을 4번 신고해도 실제 신고 횟수는 1번이다.

```python
report = ["ryan con", "ryan con", "ryan con", "ryan con"]
```

만약 이걸 그대로 세면 `con`이 4번 신고당한 것처럼 계산된다.
하지만 문제 조건상 같은 유저가 같은 유저를 여러 번 신고한 것은 1번으로만 인정된다.

그래서 이 문제의 핵심은 “신고 문자열 개수”가 아니라 “고유한 신고 관계 개수”를 세는 것이다.

## 개선해볼 수 있는 코드

처음 풀이도 잘 동작하지만, 중복 신고를 처음부터 `set(report)`로 제거하면 흐름을 조금 더 직접적으로 볼 수 있다.

```python
def solution_refactored(id_list, report, k):
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
```

이렇게 하면 “중복 제거 → 신고당한 횟수 계산 → 정지 유저 확인 → 메일 수 계산” 흐름이 더 분명해진다.

## 테스트 케이스

| id_list | report | k | expected | 설명 |
|---|---|---:|---|---|
| `["muzi","frodo","apeach","neo"]` | `["muzi frodo","apeach frodo","frodo neo","muzi neo","apeach muzi"]` | 2 | `[2,1,1,0]` | 공식 예제 |
| `["con","ryan"]` | `["ryan con","ryan con","ryan con","ryan con"]` | 3 | `[0,0]` | 중복 신고는 1번만 인정 |
| `["a","b","c"]` | `["a b","a b","c b"]` | 2 | `[1,0,1]` | 중복 신고 제거 후 기준 도달 |
| `["a","b"]` | `[]` | 1 | `[0,0]` | 신고가 없음 |
| `["a","b","c","d"]` | `["a d","b d","c a"]` | 2 | `[1,1,0,0]` | 신고 횟수가 k에 정확히 도달 |
| `["a","b","c"]` | `["a b","c a"]` | 2 | `[0,0,0]` | 정지 기준 미달 |

## 시간복잡도

시간복잡도는 `O(n + r)`이다.

`n`은 `id_list`의 길이, `r`은 `report`의 길이다.
유저 목록을 초기화하고, 신고 기록을 순회하며, 다시 메일 수를 계산한다.

개선 풀이에서는 `set(report)`를 만들 때도 신고 기록 길이만큼 순회하므로 전체적으로 선형 시간이다.

## 공간복잡도

공간복잡도는 `O(n + r)`이다.

유저별 신고 목록, 신고당한 횟수, 메일 수를 저장한다.
중복 제거된 신고 관계도 별도로 저장하므로 신고 기록 수에 비례하는 공간이 필요하다.

## 배운 점

- 중복 신고처럼 “같은 관계는 한 번만 인정”되는 조건은 `set`으로 먼저 정리할 수 있다.
- 신고당한 횟수처럼 이름별 개수를 세야 할 때는 `dict`가 잘 맞는다.
- 정지 여부 계산과 메일 수 계산을 분리하면 조건을 더 안전하게 다룰 수 있다.
- 결과 순서는 `id_list` 순서를 따라야 하므로 마지막에는 `id_list`를 기준으로 값을 꺼내야 한다.

## 다음에 비슷한 문제를 만나면 떠올릴 신호

- “중복은 한 번만 인정”이라는 문장이 보이면 `set`을 먼저 떠올리자.
- “유저별”, “이름별”, “개수별” 계산이 나오면 `dict`로 매핑하자.
- 신고자와 신고 대상처럼 관계가 있는 데이터는 `user -> target` 형태로 나눠서 생각하자.
- 중복 제거가 필요하고 조회가 많다면 `set`과 `dict`를 먼저 떠올리자.

## 최종적으로 기억할 코드

```python
def solution(id_list, report, k):
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
```

## 마무리

Day8 첫 번째 문제는 `set`과 `dict`를 함께 쓰는 구현 문제였다.

처음 작성한 풀이도 중복 신고를 `set`으로 처리하고 있어서 방향이 좋았다.
개선 코드에서는 `set(report)`로 중복 신고를 먼저 제거해서 문제의 핵심 흐름을 조금 더 앞에 드러냈다.

이번 문제를 통해 “중복 제거가 필요한 관계 데이터”는 먼저 고유한 관계로 정리한 뒤 계산하면 훨씬 깔끔해진다는 점을 다시 확인했다.
