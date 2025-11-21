# 대표 에이전트 (Representative Agent) 가이드

대표 에이전트는 하이브리드 RAG 시스템의 지식을 외부 에이전트와 소통할 수 있게 해주는 인터페이스입니다.

## 개요

이 에이전트는 REST API를 제공하여 다른 시스템이 다음과 같은 작업을 수행할 수 있게 합니다:
1. **질의 (Query)**: 자연어로 질문하고 답변을 받습니다.
2. **검색 (Retrieve)**: 답변 생성 없이 관련 문서만 가져옵니다.
3. **인덱싱 (Index)**: 새로운 문서를 시스템에 등록합니다.

## 시작하기

### 필수 조건
의존성 패키지가 설치되어 있어야 합니다:
```bash
pip install -r requirements.txt
```

### 에이전트 실행
다음 명령어로 서버를 실행합니다:
```bash
python run_representative_agent.py
```

옵션:
- `--port`: 포트 지정 (기본값: 8000)
- `--reload`: 개발용 자동 재시작 활성화
- `--index-docs`: 시작 시 `data/documents` 폴더의 모든 문서 인덱싱

### API 사용법

#### 1. 상태 확인
**GET** `/status`
시스템의 현재 상태와 통계를 반환합니다.

#### 2. 질의 (질문하기)
**POST** `/query`
에이전트에게 질문을 합니다.

**요청:**
```json
{
  "query": "하이브리드 병합 전략이란 무엇인가요?",
  "top_k": 5
}
```

**응답:**
```json
{
  "answer": "하이브리드 병합 전략은...",
  "retrieved_documents": [...],
  "query": "하이브리드 병합 전략이란 무엇인가요?"
}
```

#### 3. 검색 (문서만 가져오기)
**POST** `/retrieve`
답변 생성 없이 관련 문서만 검색합니다. 다른 에이전트가 직접 정보를 처리해야 할 때 유용합니다.

**요청:**
```json
{
  "query": "머신러닝",
  "top_k": 3
}
```

**응답:**
```json
{
  "query": "머신러닝",
  "documents": [...]
}
```

## 외부 에이전트 연동 예시

외부 에이전트는 표준 HTTP 요청을 통해 이 시스템과 통신할 수 있습니다.

### Python 예시
```python
import requests

def ask_representative_agent(question):
    url = "http://localhost:8000/query"
    payload = {"query": question}
    response = requests.post(url, json=payload)
    return response.json()["answer"]

answer = ask_representative_agent("이 프로젝트의 아키텍처를 요약해 줘")
print(answer)
```

### Curl 예시
```bash
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{"query": "이 시스템은 무엇인가요?"}'
```
