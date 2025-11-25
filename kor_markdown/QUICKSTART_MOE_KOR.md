# MoE 아키텍처 - 빠른 시작 가이드

## 🚀 빠른 시작

Mixture of Experts 아키텍처를 몇 분 안에 실행하세요!

### 1단계: 의존성 설치

모든 의존성이 설치되어 있는지 확인:
```bash
pip install -r requirements.txt
```

### 2단계: MoE 통합 테스트 실행

완전한 MoE 시스템을 시연합니다:

```bash
python test_moe_system.py
```

**무슨 일이 일어나는가:**
1. 메시지 버스와 모든 에이전트(라우터 + 3개 전문가) 생성
2. 각 전문가에 샘플 문서 로드
3. 8개의 테스트 쿼리를 적절한 전문가에게 라우팅
4. 라우팅 결정 및 전문가 응답 표시
5. 라우팅 통계 및 부하 분산 표시

**예상 출력:**
```
================================================================================
MIXTURE OF EXPERTS (MoE) 시스템 - 통합 테스트
================================================================================

Mixture of Experts (MoE) 시스템 설정
================================================================================
1. 메시지 버스 생성 중...
   ✓ 메시지 버스 시작됨
2. RAG 설정 생성 중...
   ✓ RAG 설정 생성됨
3. 전문가 에이전트 생성 중...
   ✓ General RAG Agent 생성됨
   ✓ Technical RAG Agent 생성됨
   ✓ Code RAG Agent 생성됨
4. 라우터 에이전트 생성 중...
   ✓ Router Agent 생성됨 (전략: round_robin)
5. 라우터에 전문가 등록 중...
   ✓ 모든 전문가 등록됨
6. 에이전트 시작 중...
   ✓ 모든 에이전트 시작됨

MoE 시스템 준비 완료
================================================================================

전문가 에이전트에 테스트 문서 로드 중
...

8개 테스트 쿼리 실행
================================================================================

테스트 1/8
쿼리: How do I write a Python function to calculate factorial?
✓ 라우팅됨: code_expert_001 (카테고리: code)
  라우팅 시간: 0.002s

[CODE 에이전트의 전문가 응답]
답변: ...
출처: 3개 문서
전체 시간: 1.523s
...
```

### 3단계: 대시보드로 모니터링 (선택 사항)

MoE 라우팅을 시각화하는 모니터링 대시보드 실행:

```bash
streamlit run ui/agent_monitor.py
```

**대시보드 기능:**
- 실시간 라우터 메트릭
- 카테고리별 쿼리 분포 (파이 차트)
- 전문가 간 부하 분산 (막대 차트)
- 전문가 전문화 정보
- 성능 추적

### 4단계: 코드에서 사용하기

MoE를 애플리케이션에 통합:

```python
import asyncio
from agents import RouterAgent, GeneralRAGAgent, TechnicalRAGAgent, CodeRAGAgent
from agents.message_bus import InMemoryMessageBus
from ragc_core.config import RAGConfig

async def main():
    # 1. 메시지 버스 생성
    message_bus = InMemoryMessageBus()
    await message_bus.start()

    # 2. 설정 생성
    config = RAGConfig(
        collection_name="my_collection",
        chroma_persist_directory="./chroma_db"
    )

    # 3. 전문가 에이전트 생성
    general_agent = GeneralRAGAgent(
        agent_id="general_001",
        config=config,
        message_bus=message_bus
    )

    technical_agent = TechnicalRAGAgent(
        agent_id="technical_001",
        config=config,
        message_bus=message_bus
    )

    code_agent = CodeRAGAgent(
        agent_id="code_001",
        config=config,
        message_bus=message_bus
    )

    # 4. 라우터 생성
    router = RouterAgent(
        agent_id="router_001",
        message_bus=message_bus,
        load_balancing_strategy="performance_based"  # 또는 "round_robin", "least_loaded"
    )

    # 5. 전문가 등록
    router.register_expert("general_001", ["general"])
    router.register_expert("technical_001", ["technical", "engineering"])
    router.register_expert("code_001", ["code", "programming"])

    # 6. 에이전트 시작
    await general_agent.start()
    await technical_agent.start()
    await code_agent.start()
    await router.start()

    # 7. 전문가에 문서 로드 (일회성 설정)
    from ragc_core.document_processor import DocumentProcessor
    processor = DocumentProcessor()
    chunks = processor.process_document("path/to/document.txt")

    for agent in [general_agent, technical_agent, code_agent]:
        await agent.process_task({
            "task_type": "index",
            "documents": chunks
        })

    # 8. 쿼리 라우팅
    result = await router.process_task({
        "task_type": "route_query",
        "query": "Python에서 REST API를 구현하는 방법은?",
        "requester_id": "user_001"
    })

    print(f"라우팅됨: {result['result']['expert_id']}")
    print(f"카테고리: {result['result']['category']}")

    # 9. 전문가에 직접 쿼리 (또는 라우팅된 응답 대기)
    expert_id = result['result']['expert_id']
    expert = {
        "general_001": general_agent,
        "technical_001": technical_agent,
        "code_001": code_agent
    }[expert_id]

    answer = await expert.process_task({
        "task_type": "query",
        "query": "Python에서 REST API를 구현하는 방법은?",
        "top_k": 3
    })

    print(f"답변: {answer['result']['answer']}")

    # 10. 정리
    await general_agent.stop()
    await technical_agent.stop()
    await code_agent.stop()
    await router.stop()
    await message_bus.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

## 🔧 설정 옵션

### 라우터 부하 분산 전략

**Round Robin** (기본 - 공정한 분산)
```python
router = RouterAgent(load_balancing_strategy="round_robin")
```

**Least Loaded** (동적 부하 분산)
```python
router = RouterAgent(load_balancing_strategy="least_loaded")
```

**Performance Based** (속도 최적화)
```python
router = RouterAgent(load_balancing_strategy="performance_based")
```

### 전문가 에이전트 커스터마이징

각 전문가 에이전트는 해당 도메인에 최적화된 설정을 가지고 있습니다:

**General Agent** (표준 설정)
- 기본 chunk_size, overlap, temperature
- 일반 지식 쿼리 처리

**Technical Agent** (더 많은 컨텍스트)
- chunk_size: 1200 (기본값 800 대비)
- top_k: 7 (기본값 5 대비)
- 기술 문서에 더 적합

**Code Agent** (코드 최적화)
- chunk_size: 1500 (코드 컨텍스트 보존)
- chunk_overlap: 300 (연속성 유지)
- temperature: 0.3 (정확한 생성)
- 응답에서 코드 감지

## 📊 모니터링 메트릭

### 라우터 메트릭
- **Total Routed**: 라우팅된 총 쿼리 수
- **Routes by Category**: 카테고리별 분포
- **Routes by Expert**: 부하 분산
- **Average Routing Time**: 분류 + 라우팅 시간
- **Fallback Count**: 일반 에이전트로 라우팅된 쿼리

### 전문가 메트릭
- **Current Load**: 처리 중인 활성 쿼리
- **Total Queries**: 전체 쿼리 수
- **Average Response Time**: 성능 추적
- **Specialization**: 도메인 및 카테고리

## 🎯 쿼리 예제

라우터가 자동으로 쿼리를 분류합니다:

**코드 쿼리** → Code Expert
```
"팩토리얼을 계산하는 Python 함수를 어떻게 작성하나요?"
"스택을 구현하는 코드 예제를 보여주세요"
"Python의 리스트 컴프리헨션 구문은 무엇인가요?"
```

**기술 쿼리** → Technical Expert
```
"REST API 인증 방법을 설명해주세요"
"API 문서화의 모범 사례는 무엇인가요?"
"OAuth 2.0은 어떻게 작동하나요?"
```

**일반 쿼리** → General Expert
```
"머신러닝이란 무엇인가요?"
"지도 학습과 비지도 학습의 차이점을 설명해주세요"
"일반적인 데이터 구조는 무엇인가요?"
```

## 🛠️ 문제 해결

### 사용 가능한 전문가 없음 오류
**문제**: 라우터가 쿼리 카테고리에 대한 전문가를 찾을 수 없음
**해결**: 모든 전문가가 올바른 카테고리로 등록되었는지 확인

```python
router.register_expert("general_001", ["general"])  # 일반 폴백을 잊지 마세요!
```

### 전문가가 응답하지 않음
**문제**: 전문가가 등록되었지만 응답하지 않음
**해결**: 전문가가 등록 후 시작되었는지 확인

```python
router.register_expert(...)  # 먼저 등록
await expert_agent.start()   # 그 다음 시작
```

### 높은 폴백 카운트
**문제**: 많은 쿼리가 일반 에이전트로 라우팅됨
**해결**:
1. `router_agent.py`의 분류 패턴 확인
2. 도메인에 맞는 더 구체적인 패턴 추가
3. 일반적인 카테고리를 위한 새 전문가 에이전트 생성

## 📚 다음 단계

1. **더 많은 전문가 추가**: 도메인별 에이전트 생성 (의료, 법률, 금융)
2. **패턴 커스터마이징**: `router_agent.py`의 분류 패턴 업데이트
3. **ML 분류**: 정규식을 ML 기반 분류로 교체
4. **성능 튜닝**: 도메인별 청크 크기 및 검색 파라미터 조정
5. **다중 전문가 쿼리**: 복잡한 쿼리를 여러 전문가에게 라우팅

## 📖 전체 문서

전체 아키텍처 세부 정보는 [MOE_ARCHITECTURE_KOR.md](MOE_ARCHITECTURE_KOR.md)를 참조하세요.
