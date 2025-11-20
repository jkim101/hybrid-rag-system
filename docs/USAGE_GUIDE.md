# Hybrid RAG System - 사용 가이드

이 문서는 Hybrid RAG System의 설치부터 실행까지 전체 과정을 단계별로 설명합니다.

## 📦 시스템 요구사항

### 필수 요구사항
- **Python**: 3.8 이상
- **운영체제**: Linux, macOS, Windows (WSL 권장)
- **메모리**: 최소 4GB RAM (8GB 이상 권장)
- **디스크 공간**: 최소 2GB
- **인터넷 연결**: 패키지 설치 및 API 호출에 필요

### API 키
- **Google Gemini API Key**: https://makersuite.google.com/app/apikey 에서 발급

## 🔧 설치 과정 (자동 설치)

### 1단계: 프로젝트 압축 해제

```bash
# tar 파일 압축 해제
tar -xzvf hybrid-rag-system.tar.gz

# 프로젝트 디렉토리로 이동
cd hybrid-rag-system
```

### 2단계: 자동 설치 스크립트 실행

```bash
# 스크립트에 실행 권한 부여 (이미 되어있음)
chmod +x setup.sh

# 설치 스크립트 실행
./setup.sh
```

설치 스크립트가 자동으로 다음을 수행합니다:
- ✓ Python 버전 확인
- ✓ 가상환경 생성 (venv)
- ✓ 의존성 패키지 설치
- ✓ 필요한 디렉토리 생성
- ✓ .env 파일 생성

### 3단계: API 키 설정

`.env` 파일을 편집하여 API 키를 추가합니다:

```bash
# nano 에디터로 열기
nano .env

# 또는 vim 사용
vim .env

# 또는 아무 텍스트 에디터 사용
```

`.env` 파일 내용:
```bash
GEMINI_API_KEY=여기에_실제_API_키_입력
```

저장하고 종료합니다 (nano: Ctrl+X, Y, Enter).

### 4단계: 설치 확인

가상환경이 활성화되어 있는지 확인:
```bash
# 프롬프트 앞에 (venv)가 표시되어야 함
# 만약 활성화되지 않았다면:
source venv/bin/activate
```

Python 패키지 확인:
```bash
pip list | grep -E "google-generativeai|chromadb|streamlit"
```

## 🚀 실행 방법

### 방법 1: 메인 애플리케이션 실행

문서 업로드 및 질의응답 인터페이스:

```bash
# 가상환경 활성화 (필수)
source venv/bin/activate

# Streamlit 앱 실행
streamlit run ui/streamlit_app.py
```

브라우저가 자동으로 열리고 `http://localhost:8501` 주소로 접속됩니다.

### 방법 2: 평가 대시보드 실행

RAG 시스템 평가 및 비교:

```bash
# 가상환경 활성화
source venv/bin/activate

# 평가 UI 실행
streamlit run ui/evaluation_ui.py
```

브라우저가 `http://localhost:8501` 주소로 열립니다.

## 📖 메인 애플리케이션 사용법

### 1. 시스템 초기화

**💡 API 키는 `.env` 파일에서 자동으로 로드됩니다!**

1. **API 키 확인**
   - ✅ `.env` 파일에 설정되어 있으면: "API Key loaded from .env file" 메시지 표시
   - ⚠️ 없으면: 사이드바에서 수동으로 입력 필요
   - 💡 권장: `.env` 파일에 미리 설정해두면 편리합니다
   
2. **RAG 방식 선택**
   - Hybrid RAG (기본값, 권장)
   - Vector RAG (벡터 유사도만)
   - Graph RAG (지식 그래프만)

3. **고급 설정 조정** (선택사항)
   - Chunk Size: 텍스트 청크 크기 (기본값: 1000)
   - Chunk Overlap: 청크 간 중복 크기 (기본값: 200)
   - Top K Results: 검색할 문서 개수 (기본값: 5)
   - Temperature: LLM 생성 온도 (기본값: 0.7)

4. **Hybrid RAG 설정** (Hybrid 선택 시)
   - Merge Strategy: weighted, union, intersection, sequential 중 선택
   - Vector Weight: 벡터 검색 가중치
   - Graph Weight: 그래프 검색 가중치

5. **"🚀 Initialize System" 버튼 클릭**
   - 시스템이 초기화되고 성공 메시지 표시

### 2. 문서 업로드

1. **"📄 Document Upload" 탭 선택**

2. **파일 업로드**
   - "Choose files" 버튼 클릭
   - 지원 형식: PDF, DOCX, TXT, MD, HTML
   - 여러 파일 동시 선택 가능

3. **"📥 Process Documents" 클릭**
   - 진행 상황 표시줄로 처리 과정 확인
   - 완료되면 성공 메시지와 처리된 청크 개수 표시

### 3. 질의응답

1. **"💬 Query" 탭 선택**

2. **질문 입력**
   - "Your Question" 텍스트 영역에 질문 입력
   - 예: "What is machine learning?"

3. **"🔍 Search" 클릭**
   - 시스템이 관련 문서를 검색하고 답변 생성
   - 답변, 응답 시간, 검색된 문서 표시

4. **검색된 문서 확인** (선택사항)
   - "📚 Retrieved Documents" 확장 메뉴 클릭
   - 각 문서의 관련성 점수와 내용 미리보기

5. **쿼리 히스토리 확인**
   - 최근 5개의 질의응답 기록 자동 저장
   - 각 항목 클릭하여 세부사항 확인

### 4. 통계 확인

1. **"📊 Statistics" 탭 선택**

2. **시스템 메트릭 확인**
   - Vector Docs: 벡터 DB에 저장된 문서 수
   - Graph Nodes: 지식 그래프 노드 수
   - Graph Edges: 지식 그래프 간선 수
   - Queries: 총 쿼리 수

3. **상세 통계**
   - JSON 형식으로 전체 시스템 통계 표시

## 🧪 평가 대시보드 사용법

### 1. 시스템 준비

1. **API 키 입력** (사이드바)

2. **문서 업로드**
   - Training Documents: 평가에 사용할 문서들

3. **평가 데이터셋 업로드**
   - Evaluation JSON: 쿼리와 정답이 포함된 JSON 파일
   - 형식 예제는 "📝 Dataset Format Example" 참조

4. **평가할 시스템 선택**
   - Vector RAG, Graph RAG, Hybrid RAG 중 선택
   - 여러 개 선택하여 비교 가능

5. **"🚀 Initialize Systems" 클릭**
   - 선택한 모든 시스템 초기화

### 2. 평가 실행

1. **"🧪 Run Evaluation" 탭 선택**

2. **데이터셋 미리보기 확인**

3. **"▶️ Start Evaluation" 클릭**
   - 각 시스템에 대해 평가 진행
   - 진행 상황 표시

4. **결과 확인**
   - 평가 완료 후 자동으로 결과 탭으로 전환

### 3. 결과 분석

1. **"📈 Results" 탭**
   - 각 시스템별 메트릭 카드
   - Precision, Recall, NDCG, Relevance 등
   - 점수에 따라 색상으로 표시 (녹색: 좋음, 노란색: 보통, 빨간색: 나쁨)

2. **"📊 Comparison" 탭**
   - 시스템 간 성능 비교 테이블
   - 시각적 차트로 비교
   - 검색 메트릭 vs 생성 메트릭

### 4. 결과 내보내기

1. **CSV 다운로드**
   - 표 형식으로 결과 저장
   - Excel에서 분석 가능

2. **JSON 다운로드**
   - 상세 결과 포함
   - 프로그래밍 방식 분석 가능

## 🐍 Python API 사용 (프로그래밍)

### 기본 사용 예제

```python
from ragc_core import HybridRAG, DocumentProcessor, RAGConfig

# 1. 설정 생성
config = RAGConfig(
    gemini_api_key="your_api_key_here",
    chunk_size=1000,
    chunk_overlap=200,
    top_k=5,
    merge_strategy="weighted",
    vector_weight=0.5,
    graph_weight=0.5
)

# 2. RAG 시스템 초기화
rag = HybridRAG(config)

# 3. 문서 처리
processor = DocumentProcessor(
    chunk_size=config.chunk_size,
    chunk_overlap=config.chunk_overlap
)

# 단일 문서 처리
chunks = processor.process_document("data/documents/example.pdf")

# 여러 문서 처리
file_paths = [
    "data/documents/doc1.pdf",
    "data/documents/doc2.docx",
    "data/documents/doc3.txt"
]
all_chunks = processor.process_multiple_documents(file_paths)

# 4. 문서 추가
rag.add_documents(all_chunks)

# 5. 쿼리 실행
result = rag.query("What is machine learning?")

# 6. 결과 확인
print("Answer:", result["answer"])
print("Method:", result["method"])
print("Retrieved docs:", result["num_documents"])

for i, doc in enumerate(result["retrieved_documents"]):
    print(f"\nDocument {i+1}:")
    print(f"  Score: {doc['score']:.3f}")
    print(f"  Text: {doc['text'][:100]}...")
```

### Vector RAG만 사용

```python
from ragc_core import VectorRAG, RAGConfig

config = RAGConfig(gemini_api_key="your_key")
vector_rag = VectorRAG(config)

# 문서 추가 및 쿼리
vector_rag.add_documents(chunks)
result = vector_rag.query("your question")
```

### Graph RAG만 사용

```python
from ragc_core import GraphRAG, RAGConfig

config = RAGConfig(gemini_api_key="your_key")
graph_rag = GraphRAG(config)

# 문서 추가 및 쿼리
graph_rag.add_documents(chunks)
result = graph_rag.query("your question")
```

### 평가 실행

```python
from evaluation import RAGEvaluator
import json

# 평가 데이터 로드
with open("data/evaluation/example_evaluation.json") as f:
    test_queries = json.load(f)

# 평가자 초기화
evaluator = RAGEvaluator(k=5)

# 단일 시스템 평가
results = evaluator.evaluate(rag, test_queries)

# 리포트 생성
report = evaluator.generate_report(results, "evaluation_report.txt")
print(report)

# 여러 시스템 비교
systems = {
    "Vector RAG": vector_rag,
    "Graph RAG": graph_rag,
    "Hybrid RAG": hybrid_rag
}

comparison = evaluator.compare_systems(systems, test_queries)
print("Best system for NDCG:", comparison["summary"]["best_system"]["average_ndcg"])
```

## 🔧 고급 설정

### 환경 변수 사용

`.env` 파일을 통해 모든 설정 관리:

```bash
# API 키
GEMINI_API_KEY=your_key

# 모델 설정
MODEL_NAME=gemini-2.0-flash-exp
EMBEDDING_MODEL=models/text-embedding-004
TEMPERATURE=0.7
MAX_OUTPUT_TOKENS=2048

# 청킹 설정
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# 검색 설정
TOP_K=5
SIMILARITY_THRESHOLD=0.7

# 하이브리드 설정
MERGE_STRATEGY=weighted
VECTOR_WEIGHT=0.5
GRAPH_WEIGHT=0.5
```

### 병합 전략 선택 가이드

1. **weighted** (가중 합계)
   - 가장 균형잡힌 방식
   - 벡터와 그래프 결과를 가중치로 조합
   - 권장 사용 사례: 대부분의 경우

2. **union** (합집합)
   - 최대 재현율(recall) 목표
   - 두 시스템의 모든 결과 포함
   - 권장 사용 사례: 가능한 모든 관련 문서 찾기

3. **intersection** (교집합)
   - 최대 정밀도(precision) 목표
   - 두 시스템 모두에서 찾은 문서만 포함
   - 권장 사용 사례: 매우 관련성 높은 문서만 필요

4. **sequential** (순차)
   - 벡터 결과를 먼저, 그 다음 그래프 결과
   - 한 방식을 우선시
   - 권장 사용 사례: 특정 방식 선호

## 🐛 문제 해결

### 일반적인 문제

#### 1. 가상환경 활성화 오류
```bash
# 문제: venv를 찾을 수 없음
# 해결: 프로젝트 루트 디렉토리에서 실행 확인
cd /path/to/hybrid-rag-system
source venv/bin/activate
```

#### 2. API 키 오류
```bash
# 문제: GEMINI_API_KEY is required
# 해결: .env 파일 확인
cat .env  # API 키가 올바르게 입력되었는지 확인
```

#### 3. 모듈 import 오류
```bash
# 문제: ModuleNotFoundError: No module named 'ragc_core'
# 해결: 올바른 디렉토리에서 실행
cd /path/to/hybrid-rag-system  # 프로젝트 루트로 이동
python -c "import ragc_core"  # 테스트
```

#### 4. ChromaDB 메타데이터 오류
```python
# 문제: Expected metadata value to be a str, int, float or bool
# 해결: 시스템이 자동으로 처리, 최신 코드 사용 확인
```

#### 5. 메모리 부족
```python
# 해결 방법:
# 1. chunk_size 줄이기 (1000 -> 500)
# 2. top_k 줄이기 (5 -> 3)
# 3. 문서를 작은 배치로 나누어 처리
```

### 성능 최적화

#### 청킹 최적화
```python
# 큰 청크 (1500-2000)
# 장점: 더 많은 컨텍스트
# 단점: 처리 속도 느림
config = RAGConfig(chunk_size=1500, chunk_overlap=300)

# 작은 청크 (500-800)
# 장점: 빠른 처리
# 단점: 컨텍스트 손실 가능
config = RAGConfig(chunk_size=500, chunk_overlap=100)
```

#### Top-K 조정
```python
# 높은 K (10-20)
# 장점: 더 많은 컨텍스트
# 단점: 느린 생성 속도

# 낮은 K (3-5)
# 장점: 빠른 응답
# 단점: 관련 정보 누락 가능
```

## 📊 메트릭 이해하기

### 검색 메트릭

- **Precision@K**: 검색된 K개 문서 중 관련 문서 비율
  - 0.8 = 80% 정확도
  
- **Recall@K**: 전체 관련 문서 중 검색된 비율
  - 0.6 = 60% 재현율
  
- **F1@K**: Precision과 Recall의 조화 평균
  
- **NDCG@K**: 랭킹 품질 (순서 고려)
  - 1.0 = 완벽한 랭킹
  
- **MRR**: 첫 관련 문서의 순위
  - 1.0 = 첫 번째가 관련 문서
  
- **MAP**: 전체 검색 품질

### 생성 메트릭

- **Relevance**: 답변이 질문을 얼마나 잘 다루는지
  - 0.9+ = 매우 관련성 높음
  
- **Faithfulness**: 답변이 검색된 문서에 근거하는 정도
  - 1.0 = 완전히 근거함
  
- **Completeness**: 답변의 완성도
  - 0.8+ = 포괄적인 답변

## 🔄 시스템 관리

### 데이터 초기화

```python
# 모든 데이터 삭제
rag.clear_all()

# 벡터 DB만 삭제
rag.vector_rag.clear_collection()

# 그래프만 삭제
rag.graph_rag.clear_graph()
```

### 그래프 내보내기/가져오기

```python
# 그래프 저장
rag.graph_rag.export_graph("saved_graph.pkl")

# 그래프 로드
rag.graph_rag.import_graph("saved_graph.pkl")
```

### 통계 확인

```python
# 시스템 통계
stats = rag.get_system_stats()
print(f"Vector documents: {stats['vector_rag']['total_documents']}")
print(f"Graph nodes: {stats['graph_rag']['num_nodes']}")
print(f"Graph edges: {stats['graph_rag']['num_edges']}")
```

## 🔒 보안 고려사항

1. **API 키 보호**
   - `.env` 파일을 git에 커밋하지 마세요
   - `.gitignore`에 `.env` 추가

2. **데이터 프라이버시**
   - 민감한 문서는 로컬에서만 처리
   - API 호출 시 데이터 전송 주의

3. **접근 제어**
   - 프로덕션 환경에서는 인증 추가
   - 환경에 따라 .env 파일 분리

## 📚 추가 자료

### 문서
- [ChromaDB 공식 문서](https://docs.trychroma.com/)
- [Google Gemini API](https://ai.google.dev/)
- [NetworkX 문서](https://networkx.org/)
- [Streamlit 문서](https://docs.streamlit.io/)

### 예제 데이터
- `data/documents/example_ml_basics.md`: 머신러닝 개요 문서
- `data/evaluation/example_evaluation.json`: 평가 데이터셋 예제

## 🆘 지원

문제가 발생하면:

1. 이 가이드의 "문제 해결" 섹션 확인
2. README.md의 자세한 기술 문서 참조
3. 로그 메시지 확인 (콘솔 출력)

## ✅ 체크리스트

설치 및 실행 전 확인사항:

- [ ] Python 3.8+ 설치됨
- [ ] tar 파일 압축 해제 완료
- [ ] setup.sh 실행 완료
- [ ] .env 파일에 API 키 입력
- [ ] 가상환경 활성화 확인
- [ ] 예제 문서 준비 (선택사항)

첫 실행 체크리스트:

- [ ] Streamlit 앱이 브라우저에서 열림
- [ ] API 키 입력 및 시스템 초기화 성공
- [ ] 문서 업로드 및 처리 성공
- [ ] 쿼리 실행 및 답변 생성 확인
- [ ] 통계 탭에서 데이터 확인

---

**참고**: 이 가이드는 초보자도 쉽게 따라할 수 있도록 작성되었습니다. 
더 고급 기능이 필요하면 README.md와 코드 내 주석을 참조하세요.
