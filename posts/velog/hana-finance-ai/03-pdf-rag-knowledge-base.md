# [RAG 챗봇] PDF 문서를 검색 가능한 지식베이스로 바꾸기

## 한 줄 요약

RAG는 LLM에게 문서를 그냥 던지는 것이 아니라, 문서를 쪼개고 임베딩하고 검색 가능한 형태로 바꾸는 파이프라인이다.

## 문제 정의

LLM은 질문에 그럴듯하게 답할 수 있지만, 내가 가진 특정 문서의 내용을 항상 알고 있는 것은 아니다.

그래서 PDF 문서를 기반으로 답하게 하려면 먼저 문서를 검색 가능한 구조로 바꿔야 한다.

처음에는 RAG를 “PDF 넣으면 답변해주는 기능” 정도로 생각했다. 하지만 실습해보니 실제로는 여러 단계가 필요했다.

```text
PDF
-> 텍스트 추출
-> 전처리
-> chunking
-> embedding
-> vector store 저장
-> retriever 검색
-> prompt에 context 주입
-> LLM 답변
```

## 실습 코드와 구조

`day13~day15`에서는 PDF 처리와 Chroma 기반 RAG 구조를 단계적으로 실습했다.

대표적으로 vector store를 로드하는 코드는 이런 흐름이었다.

```python
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from config.settings import *


def load_vector_store():
    embedding_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL
    )

    return Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=PERSIST_DIRECTORY,
        embedding_function=embedding_model
    )
```

여기서 중요한 것은 Chroma 자체보다 “문서를 바로 답변에 쓰는 것이 아니라, 임베딩 저장소를 거쳐 검색한다”는 구조였다.

## retriever는 검색 범위를 정한다

벡터 저장소를 만든 뒤에는 retriever로 검색 인터페이스를 만든다.

```python
from config.settings import TOP_K
from vectorstores.chroma_store import load_vector_store


def get_retriever():
    vector_store = load_vector_store()

    return vector_store.as_retriever(
        search_kwargs={
            "k": TOP_K
        }
    )
```

`TOP_K`는 검색 결과를 몇 개 가져올지 정하는 값이다.

이 값이 너무 작으면 필요한 문서를 놓칠 수 있고, 너무 크면 관련 없는 문맥이 prompt에 섞일 수 있다.

RAG에서 검색 품질은 LLM 답변 품질에 직접 영향을 준다. 모델이 아무리 좋아도 잘못된 context를 받으면 답변이 흔들릴 수 있다.

## 출처와 페이지 정보도 같이 다루기

문서 기반 답변에서는 “무슨 내용을 참고했는지”도 중요하다.

실습 코드에서는 검색된 문서의 본문과 출처 정보를 함께 포맷팅했다.

```python
def format_docs_with_pages(docs):
    context = "\n\n".join(doc.page_content for doc in docs)

    references = []
    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page", "?")
        references.append(f"{source} (page {page})")

    page_text = "\n".join(sorted(set(references)))

    return {
        "context": context,
        "page_text": page_text
    }
```

이 부분이 좋았던 이유는 RAG를 단순 답변 생성으로 보지 않고, 근거 문서와 연결하려고 했기 때문이다.

금융 문서나 약관, 안내 문서를 다룰 때는 답변 자체보다 근거를 어디에서 가져왔는지가 중요해질 수 있다.

## 헷갈린 점

처음에는 vector DB를 붙이면 답변 품질이 자동으로 좋아질 것이라고 생각했다.

하지만 RAG는 그런 마법 버튼이 아니었다.

- PDF 추출이 깨지면 검색도 흔들린다.
- chunk가 너무 크거나 작으면 context 품질이 떨어진다.
- 검색 결과가 부정확하면 LLM은 엉뚱한 근거로 답할 수 있다.
- 출처가 없으면 사용자가 답변을 검증하기 어렵다.

결국 RAG는 “LLM에 검색 기능을 붙인다”보다 “문서를 검색 가능한 지식베이스로 정리한다”에 가까웠다.

## 금융 서비스와 연결

금융 서비스에서 RAG를 쓴다면 다음과 같은 곳에 연결할 수 있다.

- 상품 설명서 기반 질의응답
- 약관 또는 안내 문서 검색
- 내부 업무 매뉴얼 챗봇
- 금융 초보자를 위한 절차 안내

다만 실제 서비스라면 반드시 주의해야 한다.

RAG 답변이 항상 정답이라는 뜻은 아니다. 검색된 근거, 문서 버전, 최신성, 답변 한계를 함께 보여줘야 한다.

## GitHub 근거 링크

- [day13 PDF/RAG 실습](https://github.com/sjh9714/hana_power_on_study/tree/main/day13)
- [day14 Chroma/RAG 실습](https://github.com/sjh9714/hana_power_on_study/tree/main/day14)
- [day15 RAG 챗봇 구조](https://github.com/sjh9714/hana_power_on_study/tree/main/day15/agri_rag_chatbot)
- [Chroma store](https://github.com/sjh9714/hana_power_on_study/blob/main/day15/agri_rag_chatbot/vectorstores/chroma_store.py)
- [Retriever](https://github.com/sjh9714/hana_power_on_study/blob/main/day15/agri_rag_chatbot/retrievers/retriever.py)

## 한계와 개선점

이번 실습은 RAG 구조를 이해하는 데 초점이 있었다.

아직 부족한 부분은 다음과 같다.

- 문서별 검색 품질을 정량적으로 평가하지 못했다.
- chunk 크기와 overlap에 따른 비교 실험이 부족했다.
- 공개 가능한 샘플 PDF와 재생성 절차가 분리되어 있지 않다.
- 실제 금융 문서라면 버전 관리와 출처 표시 정책이 더 필요하다.

다음에는 같은 질문에 대해 `TOP_K`, chunk 크기, embedding model을 바꿔가며 답변 품질을 비교해보고 싶다.

## 마무리

RAG를 배우면서 가장 크게 바뀐 생각은 이것이다.

> 답변 생성보다 먼저 문서를 검색 가능한 형태로 만드는 과정이 중요하다.

LLM은 마지막에 답변을 만드는 역할을 하지만, 그 전에 문서를 어떻게 쪼개고, 저장하고, 검색하고, 근거로 붙일지가 RAG의 핵심이었다.
