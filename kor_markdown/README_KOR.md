# 🔮 하이브리드 RAG 시스템

벡터 기반 및 그래프 기반 검색 방식을 결합하여 향상된 문서 검색과 질의응답을 제공하는 프로덕션 레디 하이브리드 RAG(Retrieval-Augmented Generation) 시스템입니다.

## 🌟 기능

### 핵심 기능
- **Vector RAG**: ChromaDB와 Gemini 임베딩을 사용한 의미론적 유사도 검색
- **Graph RAG**: NetworkX를 사용한 엔티티 관계 기반 지식 그래프 검색
- **Hybrid RAG**: 구성 가능한 병합 전략으로 두 가지 접근 방식을 결합

### 문서 처리
- 다양한 포맷 지원: PDF, DOCX, TXT, MD, HTML
- 구성 가능한 크기와 오버랩을 가진 지능형 청킹
- 자동 텍스트 정제 및 전처리

### 사용자 인터페이스
- **메인 UI**: 문서 업로드 및 질의를 위한 대화형 웹 인터페이스
- **평가 UI**: 메트릭 및 비교를 포함한 종합 평가 대시보드

### 평가 프레임워크
- **검색 메트릭**: Precision@K, Recall@K, F1@K, NDCG@K, MRR, MAP
- **생성 메트릭**: Relevance, Faithfulness, Completeness
- **성능 메트릭**: 지연 시간 측정
- CSV 및 JSON으로 결과 내보내기

## 📋 요구사항

- Python 3.8 이상
- Google Gemini API 키 ([여기서 발급받기](https://makersuite.google.com/app/apikey))

## 🚀 빠른 시작

### 설치

1. **프로젝트 클론 또는 압축 해제**
```bash
cd hybrid-rag-system
```

2. **설정 스크립트 실행**
```bash
chmod +x setup.sh
./setup.sh
```

3. **API 키 설정**
```bash
nano .env
# Gemini API 키를 추가하세요
```

### 수동 설치 (대안)

수동 설치를 선호하는 경우:

```bash
# 가상 환경 생성
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# .env 파일 생성
cp .env.example .env
# .env를 편집하고 API 키를 추가하세요
```

## 💻 사용법

### 메인 애플리케이션

대화형 웹 인터페이스 실행:

```bash
streamlit run ui/streamlit_app.py
```

**참고**: `.env` 파일에 API 키를 설정하면 자동으로 로드됩니다. 그렇지 않으면 UI에서 입력하라는 메시지가 표시됩니다.

기능:
1. **설정** RAG 유형 선택 (Vector, Graph, 또는 Hybrid)
2. **업로드** 지원되는 포맷의 문서
3. **질의** 자연어로 문서에 질문
4. **확인** 통계 및 시스템 메트릭

### 평가 인터페이스

평가 대시보드 실행:

```bash
streamlit run ui/evaluation_ui.py
```

기능:
1. **로드** 평가 데이터셋
2. **비교** 다양한 RAG 접근 방식
3. **분석** 종합 메트릭
4. **내보내기** 보고서용 결과

### Python API

시스템을 프로그래밍 방식으로 사용:

```python
from ragc_core import HybridRAG, DocumentProcessor, RAGConfig

# 설정 초기화
config = RAGConfig(
    gemini_api_key="your_api_key",
    chunk_size=1000,
    top_k=5,
    merge_strategy="weighted"
)

# RAG 시스템 생성
rag = HybridRAG(config)

# 문서 처리
processor = DocumentProcessor()
chunks = processor.process_document("path/to/document.pdf")
rag.add_documents(chunks)

# 질의
result = rag.query("머신러닝이란 무엇인가요?")
print(result["answer"])
```

## 📁 프로젝트 구조

```
hybrid-rag-system/
├── ragc_core/              # 핵심 RAG 모듈
│   ├── __init__.py
│   ├── config.py          # 설정 관리
│   ├── document_processor.py  # 문서 처리
│   ├── vector_rag.py      # 벡터 기반 RAG
│   ├── graph_rag.py       # 그래프 기반 RAG
│   └── hybrid_rag.py      # 두 가지를 결합한 하이브리드 RAG
│
├── ui/                     # 사용자 인터페이스
│   ├── streamlit_app.py   # 메인 애플리케이션 UI
│   └── evaluation_ui.py   # 평가 대시보드
│
├── evaluation/             # 평가 프레임워크
│   ├── __init__.py
│   ├── metrics.py         # 평가 메트릭
│   └── evaluator.py       # RAG 평가자
│
├── data/                   # 데이터 디렉토리
│   ├── documents/         # 문서 저장
│   └── evaluation/        # 평가 데이터셋
│
├── chroma_db/             # ChromaDB 영구 저장소
├── requirements.txt       # Python 의존성
├── setup.sh              # 설치 스크립트
├── .env.example          # 환경 변수 템플릿
└── README.md             # 영문 README
```

## ⚙️ 설정

### 환경 변수 (.env)

```bash
# 필수
GEMINI_API_KEY=your_api_key_here

# 선택 사항 - 모델 설정
MODEL_NAME=gemini-2.0-flash-exp
EMBEDDING_MODEL=models/text-embedding-004
TEMPERATURE=0.7

# 선택 사항 - 청킹
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# 선택 사항 - 검색
TOP_K=5
SIMILARITY_THRESHOLD=0.7

# 선택 사항 - 하이브리드 설정
MERGE_STRATEGY=weighted  # 옵션: weighted, union, intersection, sequential
VECTOR_WEIGHT=0.5
GRAPH_WEIGHT=0.5
```

### RAG 설정 객체

```python
from ragc_core import RAGConfig

config = RAGConfig(
    # API 설정
    gemini_api_key="your_key",
    model_name="gemini-2.0-flash-exp",

    # 청킹
    chunk_size=1000,
    chunk_overlap=200,

    # 검색
    top_k=5,

    # 하이브리드 전용
    merge_strategy="weighted",  # 또는 "union", "intersection", "sequential"
    vector_weight=0.5,
    graph_weight=0.5
)
```

## 📊 병합 전략

하이브리드 RAG 시스템은 네 가지 병합 전략을 지원합니다:

1. **Weighted**: 구성 가능한 가중치로 점수를 결합
   - 최적 사용처: 두 소스에서 균형 잡힌 검색
   - 공식: `score = vector_score * vector_weight + graph_score * graph_weight`

2. **Union**: 두 접근 방식의 모든 고유 문서를 포함
   - 최적 사용처: 최대 재현율
   - 반환: 두 시스템 중 하나에서 나온 모든 문서

3. **Intersection**: 두 접근 방식 모두에서 발견된 문서만
   - 최적 사용처: 높은 정밀도
   - 반환: 두 결과 집합에 모두 있는 문서만

4. **Sequential**: 벡터 결과 우선, 그 다음 그래프
   - 최적 사용처: 한 접근 방식을 다른 것보다 우선시
   - 반환: 벡터 결과, 그 다음 남은 슬롯을 채우는 그래프 결과

## 🧪 평가

### 평가 데이터셋 생성

다음 형식의 JSON 파일 생성:

```json
[
    {
        "query": "머신러닝이란 무엇인가요?",
        "relevant_doc_ids": ["doc_0_0", "doc_0_1"],
        "ground_truth": "머신러닝은 AI의 하위 집합으로..."
    }
]
```

### 평가 실행

```python
from evaluation import RAGEvaluator
from ragc_core import VectorRAG, GraphRAG, HybridRAG

# 평가 데이터셋 로드
with open("eval_data.json") as f:
    test_queries = json.load(f)

# 시스템 초기화
systems = {
    "Vector RAG": VectorRAG(config),
    "Graph RAG": GraphRAG(config),
    "Hybrid RAG": HybridRAG(config)
}

# 시스템 비교
evaluator = RAGEvaluator(k=5)
results = evaluator.compare_systems(systems, test_queries)

# 보고서 생성
report = evaluator.generate_report(results["Hybrid RAG"])
print(report)
```

## 📈 메트릭 설명

### 검색 메트릭

- **Precision@K**: 상위 K개 결과 중 관련 문서의 비율
- **Recall@K**: 검색된 모든 관련 문서의 비율
- **F1@K**: 정밀도와 재현율의 조화 평균
- **NDCG@K**: 정규화된 할인 누적 이득 (순위 고려)
- **MRR**: 평균 역순위 (첫 번째 관련 결과의 위치)
- **MAP**: 평균 정밀도 (전체 검색 품질)

### 생성 메트릭

- **Relevance**: 답변이 질의를 얼마나 잘 다루는지
- **Faithfulness**: 답변이 검색된 컨텍스트에 얼마나 근거하는지
- **Completeness**: 답변이 얼마나 포괄적인지

## 🔧 고급 사용법

### 커스텀 문서 프로세서

```python
from ragc_core import DocumentProcessor

processor = DocumentProcessor(
    chunk_size=1500,
    chunk_overlap=300
)

# 단일 문서 처리
chunks = processor.process_document(
    "document.pdf",
    metadata={"source": "research_paper", "year": 2024}
)

# 여러 문서 처리
file_paths = ["doc1.pdf", "doc2.docx", "doc3.txt"]
all_chunks = processor.process_multiple_documents(file_paths)
```

### 시스템 통계

```python
# 시스템 통계 가져오기
stats = rag.get_system_stats()
print(f"벡터 문서: {stats['vector_rag']['total_documents']}")
print(f"그래프 노드: {stats['graph_rag']['num_nodes']}")
print(f"그래프 엣지: {stats['graph_rag']['num_edges']}")
```

### 데이터 삭제

```python
# 모든 데이터 삭제
rag.clear_all()

# 벡터 저장소만 삭제
rag.vector_rag.clear_collection()

# 그래프만 삭제
rag.graph_rag.clear_graph()
```

## 🐛 문제 해결

### 일반적인 문제

1. **ChromaDB 메타데이터 오류**
   - 문제: `Expected metadata value to be a str, int, float or bool`
   - 해결: 시스템이 자동으로 메타데이터 변환을 처리합니다. 최신 버전을 사용하고 있는지 확인하세요.

2. **API 키를 찾을 수 없음**
   - 문제: `GEMINI_API_KEY is required`
   - 해결: 유효한 API 키가 있는 `.env` 파일이 있는지 확인하거나 환경 변수를 설정하세요

3. **임포트 오류**
   - 문제: `ModuleNotFoundError: No module named 'ragc_core'`
   - 해결: 프로젝트 루트 디렉토리에서 실행하고 있는지 확인하세요

4. **큰 문서로 인한 메모리 문제**
   - 해결: `chunk_size`를 줄이거나 문서를 배치로 처리하세요

### 성능 팁

1. **청킹 최적화**:
   - 큰 청크 (1500-2000): 더 나은 컨텍스트, 느린 처리
   - 작은 청크 (500-800): 빠른 처리, 컨텍스트 손실 가능

2. **top_k 조정**:
   - 높은 k: 더 많은 컨텍스트, 느린 생성
   - 낮은 k: 빠름, 관련 정보 놓칠 수 있음

3. **적절한 병합 전략 선택**:
   - Weighted: 대부분의 사용 사례에 최적
   - Sequential: 가장 빠름 (병합 로직 없음)

## 📝 라이선스

이 프로젝트는 교육 및 연구 목적으로 있는 그대로 제공됩니다.

## 🤝 기여

기여를 환영합니다! 개선 가능한 영역:
- 향상된 엔티티 추출 (spaCy 통합)
- 고급 관계 추출
- 추가 병합 전략
- 더 정교한 관련성 점수 매김
- 다국어 지원

## 📚 참고 자료

- [ChromaDB 문서](https://docs.trychroma.com/)
- [Google Gemini API](https://ai.google.dev/)
- [NetworkX 문서](https://networkx.org/)
- [Streamlit 문서](https://docs.streamlit.io/)

## 🙏 감사의 말

다음으로 구축됨:
- Google Gemini - LLM 기능
- ChromaDB - 벡터 저장소
- NetworkX - 지식 그래프
- Streamlit - 웹 인터페이스

---

**참고**: 이것은 연구 및 교육 프로젝트입니다. 프로덕션 사용을 위해서는 다음을 고려하세요:
- 적절한 인증 구현
- 속도 제한 추가
- 프로덕션급 데이터베이스 사용
- 포괄적인 오류 처리 구현
- 모니터링 및 로깅 추가
