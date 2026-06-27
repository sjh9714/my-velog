# [LangGraph] 금융/문서 챗봇에 Tool Router를 붙이며 배운 점

## 한 줄 요약

LangGraph를 사용하면서 챗봇 흐름을 `전처리 -> Agent -> Tool -> 후처리` 노드로 나누어 생각할 수 있었다.

## 문제 정의

기본 챗봇은 사용자의 질문을 받아서 모델에 넘기고, 답변을 그대로 보여주는 구조로 시작할 수 있다.

하지만 문서 검색, 시간 확인, 계산 같은 기능이 붙으면 흐름이 복잡해진다.

```text
사용자 질문
-> 모델 답변
```

이 구조만으로는 다음 질문에 답하기 어렵다.

- 언제 RAG 검색을 해야 하는가?
- 언제 계산 도구를 써야 하는가?
- Tool 호출 결과를 다시 모델에게 어떻게 전달할 것인가?
- 최종 답변을 어디에서 정리할 것인가?

그래서 `day16`에서는 LangGraph를 사용해 Agent와 Tool 흐름을 나눠보았다.

## 실습 코드와 구조

핵심 구조는 `StateGraph`로 노드를 만들고, 조건에 따라 다음 노드로 이동하는 방식이었다.

```python
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode


builder = StateGraph(AgentState)

builder.add_node("preprocess", preprocess_node)
builder.add_node("agent", agent_node)
builder.add_node("tools", tool_node)
builder.add_node("postprocess", postprocess_node)

builder.add_edge(START, "preprocess")
builder.add_edge("preprocess", "agent")
builder.add_edge("tools", "agent")
builder.add_edge("postprocess", END)
```

이 흐름을 처음 봤을 때 좋았던 점은 챗봇을 하나의 긴 함수가 아니라, 상태가 흐르는 그래프로 볼 수 있다는 점이었다.

## Tool 호출 여부를 라우팅하기

Agent가 항상 Tool을 쓰는 것은 아니다.

그래서 마지막 메시지에 `tool_calls`가 있는지 보고 다음 노드를 결정했다.

```python
def route_after_agent(state: AgentState):
    last_message = state["messages"][-1]

    if hasattr(last_message, "tool_calls"):
        if last_message.tool_calls:
            return "tools"

    return "postprocess"
```

이 코드는 짧지만 의미가 컸다.

모델이 도구가 필요하다고 판단하면 `tools` 노드로 보내고, 최종 답변이면 `postprocess`로 보낸다.

즉, 대화 흐름이 고정된 if문이 아니라 Agent의 판단과 상태에 따라 움직인다.

## RAG Chain을 Tool로 감싸기

기존 RAG Chain을 그대로 버리지 않고, ReAct Agent에서 사용할 Tool로 감싼 점도 중요했다.

```python
from langchain_core.tools import tool
from chains.rag_chain import create_chain


def create_rag_tool(llm, session_id: str):
    rag_chain = create_chain(llm)

    @tool
    def rag_answer(question: str) -> str:
        result = rag_chain.invoke(
            {"query": question},
            config={
                "configurable": {
                    "session_id": session_id
                }
            }
        )
        return str(result)

    return rag_answer
```

이렇게 하면 Agent는 필요할 때 `rag_answer`를 호출할 수 있고, RAG Chain 내부의 prompt, memory, retriever 구조는 유지할 수 있다.

Tool로 감싼다는 것은 기존 기능을 없애는 것이 아니라, Agent가 호출할 수 있는 인터페이스로 바꾸는 일에 가깝다.

## 전처리와 후처리 노드를 둔 이유

실습 코드에는 `preprocess_node`와 `postprocess_node`가 있다.

현재는 질문을 꺼내고 최종 답변을 저장하는 정도지만, 주석에는 나중에 붙일 수 있는 기능이 적혀 있었다.

```text
preprocess
- JWT 인증
- 사용자 조회
- 권한 검사
- 요청 로그

postprocess
- DB 저장
- Audit Log
- 사용량 기록
```

이 부분이 백엔드 관점에서 특히 흥미로웠다.

AI 챗봇도 결국 서비스라면 인증, 권한, 로깅, 저장, 사용량 관리가 필요하다. 모델 호출만으로는 운영 가능한 구조가 되기 어렵다.

## 헷갈린 점

처음에는 LangGraph가 단순히 LangChain보다 복잡한 도구처럼 느껴졌다.

하지만 그래프 구조를 보고 나니 목적이 조금 분명해졌다.

- Chain은 정해진 흐름을 표현하기 좋다.
- Agent는 도구 사용 여부를 판단할 수 있다.
- Graph는 그 판단 이후의 흐름을 노드와 엣지로 명확히 나눌 수 있다.

즉, 복잡한 챗봇일수록 “어디서 무엇을 결정하는가”를 분리해야 했다.

## 금융 서비스와 연결

금융/문서 챗봇에 Tool Router를 붙이면 이런 흐름을 생각할 수 있다.

```text
사용자 질문
-> 인증/권한 확인
-> 질문 의도 판단
-> 문서 검색 Tool
-> 계산 Tool
-> 시간/날짜 Tool
-> 최종 답변 정리
-> 로그 저장
```

예를 들어 사용자가 “이 설명서 기준으로 필요한 서류를 알려줘”라고 물으면 RAG Tool이 필요하다.

반면 “상환일이 오늘 기준 며칠 남았는지 계산해줘” 같은 질문에는 계산이나 날짜 Tool이 필요할 수 있다.

질문마다 필요한 도구가 달라지기 때문에, Tool Router 구조가 의미를 갖는다.

## GitHub 근거 링크

- [day16 LangGraph 실습](https://github.com/sjh9714/hana_power_on_study/tree/main/day16)
- [LangGraph Agent 코드](https://github.com/sjh9714/hana_power_on_study/blob/main/day16/agri_rag_chatbot_langgraph2/agents/react_rag_agent.py)
- [RAG Tool 코드](https://github.com/sjh9714/hana_power_on_study/blob/main/day16/agri_rag_chatbot_langgraph2/tools/rag_chain_tool.py)
- [Chat Service 코드](https://github.com/sjh9714/hana_power_on_study/blob/main/day16/agri_rag_chatbot_langgraph2/services/chat_service.py)

## 한계와 개선점

이번 실습은 Agent 구조를 이해하는 단계였다.

아직 부족한 부분은 다음과 같다.

- Tool 선택이 실제로 얼마나 정확한지 평가하지 못했다.
- 사용자 인증이나 권한 검사는 구조상 자리만 남겨둔 상태다.
- Tool 실행 실패 시 사용자에게 어떤 메시지를 줄지 정책이 약하다.
- 실제 금융 서비스라면 감사 로그와 답변 근거 저장이 더 중요하다.

다음에는 Tool 호출 로그를 남기고, 질문 유형별로 어떤 Tool이 선택됐는지 테스트해보고 싶다.

## 마무리

LangGraph를 쓰면서 챗봇을 “모델 호출 한 번”으로 보지 않게 됐다.

좋은 AI 서비스는 모델이 똑똑한 것만으로 만들어지지 않는다.

사용자 요청을 받고, 필요한 도구를 고르고, 검색 결과를 반영하고, 최종 답변을 정리하는 흐름을 나눠야 한다.

이번 실습은 그 경계를 처음으로 그래프 형태로 이해한 경험이었다.
