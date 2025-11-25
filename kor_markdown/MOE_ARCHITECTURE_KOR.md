# Mixture of Experts (MoE) 아키텍처

## 개요

하이브리드 RAG 시스템은 이제 쿼리 분류 및 부하 분산을 기반으로 쿼리를 전문 RAG 에이전트로 지능적으로 라우팅하는 **Mixture of Experts (MoE) 아키텍처**를 포함합니다.

## 아키텍처 구성 요소

### 1. 라우터 에이전트 (`agents/router_agent.py`)

라우터 에이전트는 MoE 시스템의 중앙 오케스트레이터입니다.

**주요 책임:**
- 정규식 기반 패턴 매칭을 사용한 쿼리 분류
- 전문가 선택 및 라우팅
- 여러 전문가 에이전트 간 부하 분산
- 성능 추적 및 메트릭 수집

**지원되는 쿼리 카테고리:**
- **Technical**: API 문서, 소프트웨어 개발, 알고리즘, 디버깅
- **Code**: 프로그래밍 예제, 코드 구현, 튜토리얼
- **Medical**: 헬스케어, 임상, 의학 용어 (확장 가능)
- **Legal**: 법적 개념, 규정, 규정 준수 (확장 가능)
- **General**: 분류되지 않은 쿼리의 폴백 카테고리

**부하 분산 전략:**

1. **Round Robin** (기본값)
   - 사용 가능한 전문가 간에 순차적으로 쿼리 분산
   - 전문가 성능에 관계없이 공정한 분산
   - 균일한 워크로드에 최적

2. **Least Loaded**
   - 현재 부하가 가장 낮은 전문가로 라우팅
   - 동적 부하 분산
   - 다양한 쿼리 복잡도에 최적

3. **Performance Based**
   - 평균 응답 시간이 가장 좋은 전문가로 라우팅
   - 속도 최적화
   - 지연 시간에 민감한 애플리케이션에 최적

**사용법:**
```python
from agents import RouterAgent

router = RouterAgent(
    agent_id="router_001",
    message_bus=message_bus,
    load_balancing_strategy="round_robin"  # 또는 "least_loaded", "performance_based"
)

# 전문가 등록
router.register_expert(
    expert_id="technical_expert_001",
    categories=["technical", "engineering"],
    metadata={"specialization": "technical_docs"}
)

# 쿼리 라우팅
result = await router.process_task({
    "task_type": "route_query",
    "query": "REST API 인증 설명",
    "requester_id": "client_001"
})
```

### 2. 전문화된 RAG 에이전트 (`agents/specialized_rag_agents.py`)

특정 도메인에 최적화된 세 가지 전문 에이전트:

#### General RAG Agent
- **전문화**: 일반 지식, 광범위한 주제
- **카테고리**: `["general"]`
- **사용 사례**: 분류되지 않은 쿼리의 폴백, 일반 Q&A
- **설정**: 표준 RAG 설정

```python
from agents import GeneralRAGAgent

general_agent = GeneralRAGAgent(
    agent_id="general_expert_001",
    config=config,
    message_bus=message_bus
)
```

#### Technical RAG Agent
- **전문화**: 기술 문서, 엔지니어링 개념
- **카테고리**: `["technical", "engineering"]`
- **사용 사례**: API 문서, 시스템 아키텍처, 기술 참조
- **설정**:
  - `chunk_size=1200` (기술 컨텍스트를 위한 큰 청크)
  - `top_k=7` (기술 정확도를 위한 더 많은 컨텍스트)

```python
from agents import TechnicalRAGAgent

technical_agent = TechnicalRAGAgent(
    agent_id="technical_expert_001",
    config=config,
    message_bus=message_bus
)
```

#### Code RAG Agent
- **전문화**: 코드 예제, 프로그래밍 튜토리얼
- **카테고리**: `["code", "programming"]`
- **사용 사례**: 코드 생성, 디버깅, 구현 가이드
- **설정**:
  - `chunk_size=1500` (코드 컨텍스트 보존)
  - `chunk_overlap=300` (코드 연속성 유지)
  - `temperature=0.3` (정확한 코드 생성)
  - 응답에서 코드 감지

```python
from agents import CodeRAGAgent

code_agent = CodeRAGAgent(
    agent_id="code_expert_001",
    config=config,
    message_bus=message_bus
)
```

### 3. 메시지 버스 통신

모든 MoE 구성 요소는 메시지 버스를 통해 통신합니다:

**워크플로우:**
1. 사용자 쿼리 → 라우터 에이전트
2. 라우터가 쿼리 분류 → 전문가 선택
3. 라우터 → 전문가 (메시지 버스를 통해)
4. 전문가가 쿼리 처리 → 응답 생성
5. 전문가 → 라우터 (메시지 버스를 통해)
6. 라우터 → 원래 요청자

## 통합 테스트

종합적인 MoE 통합 테스트 실행:

```bash
python test_moe_system.py
```

**테스트 기능:**
- 모든 구성 요소와 함께 완전한 MoE 시스템 설정
- 모든 전문가 에이전트에 샘플 문서 로드
- 8개의 다양한 테스트 쿼리를 적절한 전문가에게 라우팅
- 쿼리 분류 및 라우팅 시연
- 전문가 간 부하 분산 표시
- 라우팅 메트릭 및 성능 표시

**예상 출력:**
- 카테고리 분류와 함께 쿼리 라우팅 결정
- 전문화 메타데이터가 포함된 전문가 응답
- 라우팅 통계 (총 라우팅됨, 카테고리별, 전문가별)
- 부하 분산 메트릭
- 성능 타이밍

## 모니터링 대시보드

에이전트 모니터 대시보드 (`ui/agent_monitor.py`)에는 이제 MoE 전용 시각화가 포함됩니다:

### 라우터 에이전트 섹션
- **Total Routed Queries**: 라우팅된 모든 쿼리 수
- **Fallback Count**: 전문가가 없을 때 일반 에이전트로 라우팅된 쿼리
- **Average Routing Time**: 쿼리 분류 및 라우팅에 소요된 시간
- **Load Balancing Strategy**: 현재 사용 중인 전략

### 라우팅 시각화
1. **Routes by Category** (파이 차트)
   - 카테고리(기술, 코드, 일반 등) 간 쿼리 분포 표시
   - 일반적인 쿼리 유형 식별에 도움

2. **Routes by Expert** (막대 차트)
   - 전문가 에이전트 간 부하 분산 표시
   - 부하 분산 효과 시각화

### 전문가 에이전트 섹션
각 전문 에이전트에 대해:
- **Specialization Domain**: 에이전트의 초점 영역 표시
- **Categories Handled**: 전문가가 처리하는 쿼리 카테고리 나열
- **Focus Indicators**: 코드/기술 초점을 위한 시각적 배지

## 파일 구조

```
hybrid-rag-system/
├── agents/
│   ├── router_agent.py              # 라우터 에이전트 구현
│   ├── specialized_rag_agents.py    # GeneralRAGAgent, TechnicalRAGAgent, CodeRAGAgent
│   └── __init__.py                  # MoE 내보내기로 업데이트됨
├── test_moe_system.py               # MoE 통합 테스트
├── ui/
│   └── agent_monitor.py             # MoE 시각화로 업데이트됨
└── MOE_ARCHITECTURE.md              # 이 파일 (영문)
```

## 성능 메트릭

라우터 에이전트 추적:
- **총 라우팅된 쿼리**
- **카테고리별 라우팅** (분류)
- **전문가별 라우팅** (부하 분산)
- **평균 라우팅 시간**
- **폴백 카운트** (전문가가 없을 때)

각 전문가 에이전트 추적:
- **현재 부하** (활성 쿼리)
- **처리된 총 쿼리**
- **평균 응답 시간**
- **응답의 전문화 메타데이터**

## MoE 시스템 확장

### 새로운 전문화된 에이전트 추가

1. `RAGAgent`를 상속하는 새 전문화된 에이전트 클래스 생성:

```python
class MedicalRAGAgent(RAGAgent):
    def __init__(self, agent_id="medical_expert_001", config=None, message_bus=None):
        if config is None:
            config = RAGConfig()

        # 의료 도메인에 대한 설정 커스터마이징
        config.chunk_size = 1000
        config.top_k = 5

        super().__init__(agent_id, config, message_bus)

        self.agent_type = "medical_rag_agent"
        self.specialization = "medical"
        self.categories = ["medical", "healthcare"]

        self.capabilities.extend([
            "medical_terminology",
            "clinical_references",
            "healthcare_guidance"
        ])
```

2. 라우터에 등록:

```python
router.register_expert(
    expert_id="medical_expert_001",
    categories=["medical", "healthcare"],
    metadata={"specialization": "medical_knowledge"}
)
```

3. `router_agent.py`의 분류 패턴 업데이트:

```python
self.classification_patterns = {
    # ... 기존 패턴 ...
    "medical": [
        r'\b(patient|doctor|medical|disease|treatment|symptom|diagnosis)\b',
        r'\b(medicine|healthcare|clinical|hospital|pharmacy)\b'
    ],
}
```

### 부하 분산 커스터마이징

`RouterAgent`를 확장하여 커스텀 부하 분산 전략 생성:

```python
class CustomRouterAgent(RouterAgent):
    def _select_expert(self, category, available_experts):
        # 커스텀 선택 로직
        # 예: 우선순위 기반 라우팅
        for expert_id in available_experts:
            if self.experts[expert_id]["metadata"].get("priority") == "high":
                return expert_id

        # 부모 구현으로 폴백
        return super()._select_expert(category, available_experts)
```

## 장점

1. **전문화된 전문 지식**: 각 에이전트가 특정 도메인에 최적화됨
2. **확장성**: 새로운 전문화된 에이전트를 쉽게 추가 가능
3. **부하 분산**: 전문가 간 균형 잡힌 워크로드
4. **성능**: 도메인 최적화를 통한 빠른 응답
5. **유연성**: 여러 부하 분산 전략
6. **모니터링**: 종합적인 라우팅 및 성능 메트릭
7. **확장성**: 새로운 카테고리 및 전문가를 간단하게 추가

## 향후 개선 사항

- **머신러닝 분류**: 정규식을 ML 기반 쿼리 분류로 교체
- **동적 전문가 등록**: 시스템 재시작 없이 전문가 교체
- **다중 전문가 합의**: 복잡한 쿼리를 여러 전문가에게 라우팅
- **적응형 부하 분산**: ML 기반 전략 선택
- **전문가 성능 프로파일링**: 쿼리 유형에 따른 자동 튜닝
- **계층적 라우팅**: 복잡한 도메인을 위한 다단계 라우팅
- **쿼리 캐싱**: 유사한 쿼리에 대한 라우팅 결정 캐싱

## 참고 자료

- Base Agent: [agents/base_agent.py](agents/base_agent.py)
- RAG Agent: [agents/rag_agent.py](agents/rag_agent.py)
- Message Bus: [agents/message_bus.py](agents/message_bus.py)
- Integration Test: [test_agent_system.py](test_agent_system.py)
