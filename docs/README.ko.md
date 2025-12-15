# AI Bio LLM (멀티 에이전트 파이프라인)

이 프로젝트는 `main.py`가 여러 에이전트를 **순차적으로 호출**하여 생물학/바이오인포매틱스 문제를 해결하는 파이프라인입니다.  
각 문제는 `problems/problem_X/` 아래에 **단계 번호가 붙은 폴더**로 아티팩트를 남기며, 기본 실행에서는 진행 상황과 저장 경로만 간단히 출력됩니다.

영문 버전은 루트의 [README.md](../README.md)를 참고하세요.

---

## 실행 방식

### 입력 파일 탐색 규칙
`main.py`는 아래 패턴으로 문제 파일을 자동 탐색합니다.
- `problems/**/problem_*.txt`
  - 예: `problems/problem_1/problem_1.txt`

### 전체 실행

```bash
python main.py
```

### 특정 문제만 실행

```bash
python main.py --only 1
python main.py --only problem_2
python main.py --only problems/problem_3/problem_3.txt
```

### 상세 로그 보기
기본은 에이전트 stdout이 대부분 숨겨집니다. 전체 로그를 보려면:

```bash
python main.py --verbose
```

---

## 파이프라인 단계(실행 순서)

각 `problem_*.txt`에 대해 아래 순서로 실행됩니다.

### 01) Brain (`01_brain/`)
- **에이전트**: `BrainAgent`
- **출력**: `01_brain/brain_decomposition.json`
- **역할**: 문제 텍스트를 구조화하여 downstream 에이전트가 참고할 컨텍스트 생성

### 02) Search (`02_search/`)
- **에이전트**: `SearchAgent`
- **입력**: `01_brain/brain_decomposition.json`
- **표준 아티팩트**
  - `02_search/system_prompt.md`
  - `02_search/user_prompt.txt`
  - `02_search/output.txt`
- **역할**: 지식/문헌 기반 조사 결과 생성(가능하면 reference 포함)

### 03) Data Analysis (`03_data_analysis/`)
- **에이전트**: `DataAnalystAgent`
- **입력**: `01_brain/brain_decomposition.json`
- **출력(항상 생성)**
  - `03_data_analysis/data_analysis_results.txt` *(스킵/실패 시에도 downstream용으로 항상 생성)*
  - 추가 산출물(있는 경우): `03_data_analysis/data_analysis.md` 또는 `03_data_analysis/data_analysis.json`
- **역할**: 문제 폴더 내 CSV/TSV 등의 데이터 파일을 찾아 요약/해석 생성

### 04) Blue Draft (`04_blue_draft/`)
- **에이전트**: `BlueAgent`
- **입력**: Search 결과 + Data analysis 요약
- **표준 아티팩트**
  - `04_blue_draft/system_prompt.md`
  - `04_blue_draft/user_prompt.txt`
  - `04_blue_draft/output.txt`
- **역할**: 문제에서 요구한 답변 형식/번호/요구사항을 맞춘 초안 생성

### 05) Red Critique (`05_red_critique/`)
- **에이전트**: `RedAgent`
- **입력**: Blue 초안
- **표준 아티팩트**
  - `05_red_critique/system_prompt.md`
  - `05_red_critique/user_prompt.txt`
  - `05_red_critique/output.txt`
- **역할**: 초안의 누락/리스크/불명확성 비판

### 06) BlueX Revision (`06_bluex_revision/`)
- **에이전트**: `BlueXAgent`
- **입력**: Blue 초안 + Red 비판 + Data analysis 요약
- **표준 아티팩트**
  - `06_bluex_revision/system_prompt.md`
  - `06_bluex_revision/user_prompt.txt`
  - `06_bluex_revision/output.txt`
- **역할**: Red 피드백을 반영하여 답변 개선(리비전)

### 07) Red Review (`07_red_review/`)
- **에이전트**: `RedAgent`
- **입력**: BlueX 결과
- **표준 아티팩트**
  - `07_red_review/system_prompt.md`
  - `07_red_review/user_prompt.txt`
  - `07_red_review/output.txt`
- **역할**: 최종 답변에 대해 **신뢰도 점수(0~100) + 비판/한계/리스크** 포함 리뷰 생성

### 08) Answer (`08_answer/`)
- **에이전트**: `AnswerAgent`
- **입력**
  - 문제 원문(Brain JSON)
  - Search 결과(reference 포함 가능)
  - BlueX 답변
  - Red 최종 리뷰(신뢰도 포함)
- **표준 아티팩트**
  - `08_answer/system_prompt.md`
  - `08_answer/user_prompt.txt`
  - `08_answer/output.txt`
- **역할**: 최종 deliverable 조립
  - 문제 형식/번호 유지
  - Red 리뷰 섹션을 끝에 붙임
  - Search 결과에 reference가 있으면 본문 인용 + **References 섹션** 포함

---

## 최종 답변 파일
각 문제 폴더에 아래 파일이 생성됩니다.
- `answer_*.txt` (예: `problem_1.txt` → `answer_1.txt`)

내용은 `08_answer/output.txt`를 그대로 복사한 것입니다.

---

## 환경 변수(.env)
프로젝트 루트에 `.env`를 생성합니다.

```bash
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# 선택: 모델 오버라이드
MODEL_BRAIN=google/gemini-2.5-flash
MODEL_SEARCH=google/gemini-2.5-flash
MODEL_BLUE=google/gemini-2.5-flash
MODEL_BLUEX=google/gemini-2.5-flash
MODEL_RED=google/gemini-2.5-flash
```

---

## 설치(micromamba/conda + pip 권장)

```bash
pip install -r requirements.txt
```

---

## 참고
- 각 단계는 `system_prompt.md`, `user_prompt.txt`, `output.txt`를 남기므로, 단계별 생성 과정을 추적하기 쉽습니다.

---

## 최근 실행 시간(예시)
아래는 최근 `micromamba run -n bio-agent python main.py` 실행(병렬 실행) 기준 시간입니다.  
모델/레이트리밋/네트워크/데이터 유무에 따라 값은 달라질 수 있습니다.

| 문제 | 총 소요(s) | Brain | Search | Data | Blue | Red critique | BlueX | Red review | Answer |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `problem_1.txt` | 371.1 | 7.6 | 159.7 | 64.4 | 24.3 | 29.9 | 25.1 | 39.3 | 20.7 |
| `problem_2.txt` | 446.2 | 18.8 | 262.5 | 0.0 | 27.0 | 39.2 | 30.8 | 39.5 | 28.3 |
| `problem_3.txt` | 343.9 | 8.0 | 195.9 | 0.0 | 21.0 | 40.7 | 22.0 | 32.0 | 24.2 |
| `problem_4.txt` | 327.6 | 11.6 | 195.4 | 0.0 | 22.3 | 28.7 | 25.8 | 28.1 | 15.6 |
| `problem_5.txt` | 282.2 | 7.4 | 154.8 | 0.0 | 17.8 | 33.9 | 17.8 | 25.9 | 24.5 |

---

## License
[MIT License](../LICENSE)


