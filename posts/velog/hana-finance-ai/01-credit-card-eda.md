# [금융 데이터 분석] Pandas로 신용카드 거래 데이터 EDA 구조 잡기

## 한 줄 요약

신용카드 거래 데이터는 단순한 표가 아니라 고객, 시간, 금액, 위치, 위험 신호가 함께 들어 있는 이벤트 데이터로 봐야 한다.

## 문제 정의

Pandas를 처음 배울 때는 `read_csv()`, `head()`, `groupby()` 같은 함수 사용법에 집중하게 된다.

하지만 금융 데이터 분석에서는 함수 사용법보다 더 중요한 질문이 있다.

> 이 데이터에서 하나의 행은 무엇을 의미하는가?

신용카드 거래 데이터에서 하나의 행은 단순한 숫자 묶음이 아니라 “어떤 고객이, 언제, 어디서, 얼마를 결제했는가”라는 이벤트다.

그래서 EDA도 평균 금액 하나만 보는 식으로 끝나면 부족하다. 시간, 고객, 거래 금액, 위험 신호를 함께 봐야 한다.

## 실습 코드와 구조

`step1/notebooks/step_credit.ipynb`에서는 먼저 데이터 경로를 고정하지 않고, 현재 위치에서 `step1` 루트를 찾도록 정리했다.

```python
from pathlib import Path


def find_step1_root():
    current_dir = Path.cwd()
    for path in [current_dir, *current_dir.parents]:
        if path.name == "step1":
            return path
        if (path / "step1").is_dir():
            return path / "step1"
    return current_dir


STEP1_ROOT = find_step1_root()
DATA_DIR = STEP1_ROOT / "data"
OUTPUT_DIR = STEP1_ROOT / "outputs"
```

처음에는 사소해 보였지만, 노트북은 실행 위치가 자주 바뀐다. 그래서 데이터 경로를 상대 경로로만 두면 쉽게 깨질 수 있다.

이 부분은 “분석 코드도 재현 가능해야 한다”는 점을 배운 지점이었다.

## 기본 EDA 흐름

CSV를 읽은 뒤에는 먼저 데이터의 모양을 확인한다.

```python
import pandas as pd

csv_path = DATA_DIR / "credit_card_transactions.csv"
df = pd.read_csv(csv_path)

print(df.head())
print(df.info())
print(df.describe())
```

여기까지는 일반적인 Pandas EDA와 비슷하다.

하지만 금융 거래 데이터에서는 여기서 한 단계 더 나아가야 한다.

- 거래 시간은 언제인가?
- 고객별 거래 횟수와 금액은 어떤가?
- 시간대별로 결제 패턴이 달라지는가?
- 위험 신호가 있는 거래는 어떤 조건에서 많이 보이는가?

## 시간 컬럼을 먼저 다룬 이유

거래 데이터에서 시간은 거의 항상 중요하다.

실습에서는 거래 시간을 `datetime`으로 변환한 뒤 시간대와 요일을 뽑았다.

```python
df["trans_date_trans_time"] = pd.to_datetime(df["trans_date_trans_time"])

df["hour"] = df["trans_date_trans_time"].dt.hour
df["day"] = df["trans_date_trans_time"].dt.day_name()
```

문자열 상태의 날짜는 정렬과 집계가 불편하다. 반대로 `datetime`으로 바꾸면 시간대별, 요일별, 월별 분석이 가능해진다.

금융 서비스에서는 “언제 발생했는가”가 행동 패턴과 이상 탐지의 중요한 단서가 될 수 있다.

## 고객 단위로 묶어보기

거래 데이터는 개별 거래만 보면 흩어진 점처럼 보인다.

그래서 고객 단위로 묶어보면 행동 패턴을 보기 쉬워진다.

```python
customer_group = df.groupby("cc_num")

customer_behavior = customer_group.agg(
    총소비금액=("amt", "sum"),
    평균소비금액=("amt", "mean"),
    거래횟수=("amt", "count"),
)
```

이 코드는 단순하지만 관점이 중요했다.

`groupby("cc_num")`은 “거래 목록”을 “고객별 행동 요약”으로 바꾸는 단계다. 금융 데이터에서는 이런 식으로 원본 이벤트를 분석 가능한 feature로 바꾸는 과정이 자주 등장한다.

## 헷갈린 점

처음에는 EDA를 그래프를 그리는 단계 정도로 생각했다.

하지만 실제로는 그래프보다 먼저 해야 할 일이 있었다.

- 행의 의미를 정의하기
- 주요 엔티티를 찾기
- 시간 컬럼을 분석 가능한 형태로 바꾸기
- 집계 기준을 정하기

그래프는 그 다음이다.

특히 금융 데이터에서는 고객, 거래, 시간, 위치, 위험 신호가 각각 다른 분석 축이 될 수 있다. 어떤 축으로 묶느냐에 따라 완전히 다른 질문을 하게 된다.

## 금융 서비스와 연결

이 실습은 FDS나 리스크 분석으로 바로 이어질 수 있다.

예를 들어 다음과 같은 질문을 만들 수 있다.

- 평소보다 큰 금액의 거래인가?
- 특정 시간대에 갑자기 거래가 몰렸는가?
- 고객의 평균 결제 패턴과 다른가?
- 위험 라벨이 있는 거래는 어떤 특성을 갖는가?

아직 모델을 만들지는 않았지만, 이런 질문을 만들 수 있어야 이후 feature engineering과 모델링으로 넘어갈 수 있다.

## GitHub 근거 링크

- [step1 README](https://github.com/sjh9714/hana_power_on_study/tree/main/step1)
- [step_credit.ipynb](https://github.com/sjh9714/hana_power_on_study/blob/main/step1/notebooks/step_credit.ipynb)
- [day5 금융 데이터 구조](https://github.com/sjh9714/hana_power_on_study/tree/main/day5)
- [day6 EDA와 Feature 구조](https://github.com/sjh9714/hana_power_on_study/tree/main/day6)

## 한계와 개선점

이번 실습은 EDA 구조를 잡는 단계였다.

아직 부족한 점은 다음과 같다.

- 공개 가능한 샘플 데이터가 따로 분리되어 있지 않다.
- 그래프와 요약 결과를 포트폴리오용 이미지로 정리하지 못했다.
- 이상 거래 후보를 정량적으로 정의하는 규칙은 아직 약하다.

다음에 개선한다면 샘플 데이터를 따로 만들고, 고객별/시간대별 요약 결과를 `outputs/`에 저장하는 구조까지 정리해보고 싶다.

## 마무리

Pandas 함수 사용법을 아는 것과 금융 데이터를 분석하는 것은 조금 달랐다.

이번 실습에서 가장 크게 배운 점은 “데이터를 어떤 단위로 볼 것인가”였다.

신용카드 거래 데이터는 행 하나가 하나의 이벤트이고, 그 이벤트를 고객·시간·금액·위험 신호 관점으로 다시 묶을 때 분석이 시작된다.
