# Evidence Desk — EU 컨베이어 기술문서 준비 PoC

**UPLOAD → CHECK → TO DO → PREPARE → RE-CHECK**

BC-100의 합성 PDF를 사전 정의한 12개 문서 준비 항목과 대조하고, 근거 위치·부족 정보·다음 작업·보완 초안·재검토 변화를 보여주는 Streamlit 앱입니다.

**기본값은 API 비용이 없는 Mock입니다.** Mock는 합성자료의 명시적 필드를 읽는 규칙 기반 시연이며, AI의 의미 매칭 성능을 보여주는 실험이 아닙니다. OpenAI 모드는 실제 Responses API의 의미 기반 매칭을 사용하도록 구현했습니다. 이번 제작 환경에는 API 키가 없어 실제 모델 호출은 실행하지 않았습니다. 검증한 범위는 [VALIDATION.md](VALIDATION.md)에 구분했습니다.

## 1. 빠르게 실행하기

Python **3.12**를 권장합니다. 아래 명령은 ZIP을 풀고 `export-reg-ai` 폴더에서 실행합니다.

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

### macOS / Linux

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

터미널에 표시된 Local URL을 브라우저에서 엽니다. 보통 `http://localhost:8501`입니다. 종료는 터미널에서 Ctrl+C입니다. Mock는 키 설정이 필요 없습니다.

## 2. 발표용 시연 순서

### UPLOAD / CHECK

1. 분석 방식은 **Mock · API 없이 체험**으로 둡니다.
2. PROJECT 기본값은 BC-100 / 설계 버전 B / EU / 2026년 출시입니다.
3. `sample_data` 바로 아래 PDF **6개만** 함께 업로드합니다. `revised` 폴더의 수정본은 처음에 넣지 않습니다. 또는 **합성 PDF 6개 불러오기**를 누릅니다.
4. **Analyze · 문서 대조**를 누르고 CHECK 탭으로 이동합니다.
5. 전체 12개 행, 문서 Gap 6개, 전문가 판단 필요 4개가 표시됩니다. 근거가 있다는 뜻과 기술적 충분성이 확인됐다는 뜻은 다릅니다.
6. 필터와 항목 상세보기에서 원문·물리적 PDF 페이지·연결 이유를 확인합니다. JSON과 Markdown 보고서를 다운로드할 수 있습니다.

| 항목 | 첫 분석의 의도된 결과 | 원인 |
|---|---|---|
| REQ-01 유지보수 | INSUFFICIENT_INFORMATION | 예방조치는 있으나 점검주기 누락 |
| REQ-02 식별 정보 | EVIDENCE_FOUND | 제조자·모델 문장 존재 |
| REQ-03 용도·한계 | EVIDENCE_FOUND | 의도된 사용과 제한 문장 존재 |
| REQ-04 설치 | EVIDENCE_FOUND | 매뉴얼 v1의 설치 설명 |
| REQ-05 조작 | EVIDENCE_FOUND | 시작·정지 조작 설명 |
| REQ-06 시험자료 | MODEL_MISMATCH | BC-100에 BC-90 시험자료 연결 |
| REQ-07 도면 | VERSION_MISMATCH | 설계 기준 B에 구버전 A 도면 |
| REQ-08 취급·운반 | NOT_FOUND_IN_UPLOAD | 업로드 자료에서 찾지 못함 |
| REQ-09 방호 설명 | VERSION_MISMATCH / 전문가 필요 | 구버전 도면에 관련 문장만 있음 |
| REQ-10 소음 | UNREADABLE / 전문가 필요 | 텍스트 없는 이미지 PDF, OCR 미지원 |
| REQ-11 변경이력 | EVIDENCE_FOUND | 변경이력 문장 존재 |
| REQ-12 잔류위험 안내 | EVIDENCE_FOUND / 전문가 필요 | 관련 문장이 있지만 충분성 미판단 |

### TO DO / PREPARE

1. 세 번째 탭에서 항목별 다음 작업을 확인하고 REQ-01을 선택합니다.
2. 현재 원문과 부족 정보, 담당자에게 확인할 질문을 읽습니다.
3. 점검주기 질문에 `Every 30 days (synthetic demonstration only).`를 입력합니다. **시연용 합성값이며 실제 기계에 적용할 권고가 아닙니다.**
4. 원문 및 입력값의 사실관계 확인 체크박스를 체크하고 **확인된 정보로 보완 초안 생성**을 누릅니다.
5. 입력값과 기존 예방조치 문장만 포함된 초안을 확인합니다. 답하지 않은 정보는 질문으로 남습니다.
6. TXT 또는 **재업로드용 보완 PDF**를 받습니다. 이때 기존 CHECK 결과는 바뀌지 않습니다.

### RE-CHECK: 두 가지 경로

**경로 A — 방금 만든 초안 재업로드**

다운로드한 `BC100_Prepared_REQ-01.pdf`를 네 번째 탭에서 추가하고 RE-CHECK를 누릅니다. 기존 파일은 유지합니다. REQ-01이 `INSUFFICIENT_INFORMATION → EVIDENCE_FOUND`로 바뀌고 **문서 Gap 보완 후보**가 됩니다. 이는 사용자 확인 사실이 문서에 생긴 것이며, 전문가 승인이나 규제 충족 표시가 아닙니다.

**경로 B — 새 버전에서 이전 정보가 사라지는 사례**

1. 기존 `BC100_User_Manual_v1.pdf`, `BC100_Drawing_Summary.pdf`를 **교체하거나 제외할 기존 파일**에서 선택합니다.
2. `sample_data/revised`의 PDF 2개를 업로드하고 RE-CHECK를 실행합니다.
3. REQ-01 유지보수, REQ-07 도면은 문서 Gap 보완 후보가 됩니다. REQ-09는 현재 버전의 근거가 생겨도 전문가 판단이 남습니다.
4. 수정 매뉴얼에서 설치 설명을 의도적으로 지웠으므로 **REQ-04가 다시 검토 필요**로 바뀝니다.
5. BC-90 시험자료, 운반 정보 부재, 판독 불가 소음 자료는 그대로 남습니다.

파일명이 같으면 새 파일로 교체합니다. 파일명이 다르면 둘 다 남으므로, 구버전을 교체하려면 기존 파일을 명시적으로 제외하세요. 구버전까지 남기면 보수적으로 불일치가 유지될 수 있습니다.

## 3. 실제 OpenAI API 사용

### 로컬 `.env` 방식

`.env.example`을 `.env`로 복사한 뒤 본인의 API 키를 설정합니다.

```dotenv
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4.1-mini
ENABLE_OPENAI=true
```

앱을 재시작하고 사이드바의 **OpenAI · 실제 의미 매칭**을 선택합니다. API 계정의 모델 접근권과 사용 가능한 크레딧이 필요합니다. 키는 소스·GitHub·화면 입력란에 넣지 않습니다. 환경변수가 설정되어 있으면 Streamlit Secrets보다 우선합니다.

### Streamlit Secrets 방식

`.streamlit/secrets.toml.example`을 참고해 로컬 `.streamlit/secrets.toml` 또는 Cloud의 Secrets에 입력합니다.

```toml
OPENAI_API_KEY = "your_api_key_here"
OPENAI_MODEL = "gpt-4.1-mini"
ENABLE_OPENAI = "true"
```

- 실제 모드에서는 추출된 PDF 텍스트·파일명·프로젝트 입력·요구사항이 API로 전송됩니다. 원본 PDF 이미지 자체는 보내지 않습니다.
- Responses API `responses.parse(..., text_format=MatchBatch)`를 사용합니다. `store=False`이며, 이는 별도의 완전 무보관 보장을 뜻하지 않습니다. 실제 기밀자료 사용 전에 공급자 정책과 기업의 허용 조건을 별도로 확인해야 합니다.
- 키·한도·네트워크·모델 오류는 오류로 보여줍니다. **실패 시 Mock 결과로 자동 대체하지 않습니다.**
- CHECK와 재검토는 문서 묶음을 의미적으로 대조하는 API 호출입니다. PREPARE는 확인된 사실 ID의 배치만 AI에 맡기고 실제 본문은 검증된 원문·사용자 입력으로 렌더링합니다.
- `gpt-4.1-mini`가 계정에서 지원되지 않으면 Structured Outputs를 지원하는 접근 가능한 모델 ID로 바꿉니다. 모델 변경 후 결과를 재검증해야 합니다.
- 공개 앱에는 로그인·요청별 비용 제한을 구현하지 않았습니다. **공개 발표용 배포는 Mock 설정을 유지**하고 실제 API는 통제된 시연 환경에서 사용하세요.

## 4. GitHub에 올리기

이 패키지는 사용자의 저장소를 생성하거나 원격으로 게시하지 않았습니다. 새 저장소 이름의 기본안은 `export-reg-ai`입니다.

### GitHub 웹에서 업로드

1. GitHub에서 New repository를 선택합니다. 공개 여부는 직접 정합니다.
2. ZIP을 풀고 프로젝트 내부의 소스, `requirements.json`, `requirements.txt`, `sample_data`, 테스트, README를 올립니다.
3. **저장소 최상위에 `app.py`와 `requirements.txt`가 오도록** 합니다. `.env`, 실제 `secrets.toml`, 가상환경은 올리지 않습니다.
4. `.gitignore`, `.streamlit/config.toml`도 포함합니다. 웹 업로드에서 숨김 파일 선택이 어려우면 아래 Git 방식을 사용합니다.
5. Commit changes를 완료합니다.

### Git 명령으로 업로드

빈 원격 저장소를 먼저 만든 뒤 프로젝트 폴더에서 실행합니다. `YOUR_GITHUB_ACCOUNT`를 본인 계정으로 바꿉니다.

```bash
git init
git add .
git status
git commit -m "Build conveyor document preparation prototype"
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_ACCOUNT/export-reg-ai.git
git push -u origin main
```

`git status`에서 API 키와 실제 기업자료가 포함되지 않았는지 확인하세요. GitHub 로그인은 Git Credential Manager 또는 GitHub의 지원 인증 방식을 이용합니다. 이 프로젝트에는 실제 키가 포함되어 있지 않습니다.

## 5. Streamlit Community Cloud 배포

1. [Streamlit Community Cloud](https://share.streamlit.io/)에 로그인하고 GitHub 저장소 접근을 연결합니다.
2. **Create app**에서 저장소와 `main` 브랜치를 선택합니다.
3. Main file path를 **`app.py`**로 설정합니다. 상위 폴더째 올렸다면 실제 경로인 `export-reg-ai/app.py`를 선택해야 합니다. 가급적 위의 저장소 최상위 구성을 사용하세요.
4. Advanced settings에서 Python **3.12**를 선택합니다.
5. 공개 Mock 시연은 Secrets를 비워 두거나 `ENABLE_OPENAI = "false"`로 설정합니다.
6. Deploy를 누릅니다. 빌드 로그에서 `requirements.txt` 설치와 앱 시작을 확인합니다.
7. 배포 URL에서 샘플 불러오기 → Analyze → PREPARE → 수정 파일 RE-CHECK 흐름을 한 번 확인합니다.
8. 통제된 API 시연이 필요할 때만 앱 설정의 Secrets에 위 값을 입력합니다. Secrets 변경 후 필요하면 앱을 재부팅합니다.

Cloud에서 쓰는 세션 메모리는 영구 저장소가 아닙니다. 결과를 JSON/보고서로 다운로드하세요. 새로고침·앱 재시작·세션 종료 시 프로젝트가 사라질 수 있습니다.

공식 안내: [앱 배포](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app), [Secrets 관리](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management).

## 6. 내부 구조와 안전장치

| 파일 | 역할 |
|---|---|
| `app.py` | 4개 탭, 업로드·상태·필터·수동 확인·다운로드 |
| `ai_engine.py` | 실제 API/명시적 Mock, 인용 검증, 다음 작업, 초안, 재검토 비교 |
| `models.py` | Pydantic 스키마 및 허용 상태 enum |
| `pdf_utils.py` | PDF 텍스트 추출, 페이지, 해시, 업로드 제한, 파일 교체 |
| `prompts.py` | 비정형 의미 매칭·출처·판단 경계 규칙 |
| `requirements.json` | 12개 사전 정의 요구사항, 정보 필드, 질문, 공개 법령 참조 |
| `export_utils.py` | 확인 사실만 포함한 TXT용 내용·PDF·Markdown 보고서 |
| `generate_samples.py` | 합성 PDF 6개 + 수정본 2개 생성 |
| `tests/` | 전체 UI 흐름, 인용·스키마·파일·재검토·SDK 계약 검증 |

### 데이터 경계

- 최대 10개 PDF, 파일당 5 MB, 전체 60페이지, 전체 추출 텍스트 90,000자입니다. 넘는 내용은 조용히 자르지 않고 요청을 거부합니다.
- PDF 텍스트만 읽습니다. 스캔 OCR, CAD 형상 이해, 도면 치수 판독은 지원하지 않습니다. 도면 설명 PDF의 텍스트를 사용하세요.
- `Model:` / `Design revision:` 명시적 헤더로 확인 가능한 모델·설계 불일치를 코드에서 재검증합니다. 실제 문서의 다른 표기 방식은 AI 및 사람 검토가 필요합니다. 파일명만으로 모델 일치를 확정하지 않습니다.
- 물리적 PDF 페이지 번호는 1부터 셉니다. 인쇄된 페이지 번호와 다를 수 있습니다.
- 각 인용은 파일·페이지·필드 ID·원문 문자열과 대조합니다. 없는 인용은 제외하고 확인을 보류합니다. **문자열 존재 검사는 의미의 적합성이나 충분성 검증이 아닙니다.**
- 문서 내용은 신뢰할 수 없는 입력으로 다룹니다. 문서 안 지시를 따르지 않도록 프롬프트에 명시했습니다. 이것이 모든 프롬프트 공격 방어를 보장하지는 않습니다.
- `EVIDENCE_FOUND`는 관련 근거 후보가 있음을 뜻합니다. AI는 `CONFIRMED_BY_USER`를 설정할 수 없습니다. 사용자 확인 기록도 인용·사실관계 확인만 의미합니다.
- 전문가 판단 필수 항목은 AI나 사용자의 일반 확인 버튼으로 승인되지 않습니다.
- PREPARE는 시험값·설계값을 자유 생성하지 않습니다. 사용자 확인 원문/입력값을 정확히 재사용하며, 잘못된 입력의 사실성까지 검증하지는 않습니다. 부족 정보 질문은 고정 검토 범위의 질문입니다.
- 현 단계의 PREPARE는 사실 기반 보완 초안이며, 자유로운 기술문서 전체 작성이나 자동 영문화 기능은 포함하지 않았습니다.
- 재검토 시 자료 해시·페이지·인용·상태를 비교합니다. 문서가 달라지면 이전 인용이 같아도 재확인을 요구할 수 있습니다. 보수적으로 사람 확인 상태는 재분석마다 초기화합니다.

### 규제 범위

2026년 EU 출시를 가정한 사람 사전확정 문서 준비 범위입니다. 공개 [Directive 2006/42/EC](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32006L0042)의 관련 위치와 자체 작성 설명을 사용했습니다. **12개 항목은 전체 법적 체크리스트가 아니며 실제 적용성이 검증된 것은 아닙니다.** ISO/EN 등 유료 표준 본문은 넣지 않았습니다. 변경이력 항목은 기술문서 추적을 위한 자체 정리 항목이며 특정 양식이 법적으로 요구된다는 뜻이 아닙니다.

적용 법령 범위, 위험성평가, 고도의 공학적 판단, 물리시험, 법적 제3자 평가 필요 여부와 최종 책임은 사람/기관 영역입니다. 앱은 인증 판정·인증 대행·시험결과 판정 도구가 아닙니다.

### API 구현 근거

[OpenAI Structured Outputs 공식 문서](https://developers.openai.com/api/docs/guides/structured-outputs), [공식 Python SDK helpers](https://github.com/openai/openai-python/blob/main/helpers.md)를 확인해 구현했습니다. 실제 모델 응답과 비용·정확도·시간 절감은 별도 검증 대상입니다.

## 7. 테스트와 샘플 재생성

가상환경의 Python을 사용해 실행합니다.

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
python generate_samples.py
```

가상환경을 활성화하지 않았다면 Windows는 `.venv\Scripts\python.exe`, macOS/Linux는 `.venv/bin/python`으로 `python`을 바꿉니다.

테스트는 실제 PDF 바이트를 Streamlit 업로더 위젯에 전달해 Analyze·필터·PREPARE·RE-CHECK를 실행합니다. SDK 테스트는 가짜 HTTP 응답을 사용하므로 API 키/요금이 필요 없고 AI 성능 검증도 아닙니다. `test_artifacts/`는 로컬 검증용 중간 출력 디렉터리이며 Git에서 제외됩니다.

## 8. 자주 만나는 문제

- **ModuleNotFoundError**: 실행에 쓰는 같은 Python으로 `-m pip install -r requirements.txt`를 실행하세요.
- **PDF가 비어 있다고 표시**: 스캔본은 텍스트 PDF로 다시 내보내세요. 앱에는 OCR이 없습니다.
- **보완했는데 VERSION_MISMATCH 유지**: RE-CHECK에서 구버전 파일을 제외했는지 확인하세요.
- **입력한 답변이 CHECK에 반영되지 않음**: 초안 작성만으로 기존 자료를 변경하지 않습니다. 보완 PDF를 받아 다시 업로드하세요.
- **API 호출 실패**: 서버 키·ENABLE_OPENAI·모델 접근·크레딧·네트워크를 확인하세요. SOCKS 프록시 환경에서 SDK 초기화 오류가 나면 해당 환경에 필요한 프록시 의존성(`socksio`)도 설치하세요.
- **Mock가 새 문장을 못 찾음**: 의도된 제한입니다. Mock는 샘플의 명시적 필드 형식을 읽습니다. 일반 문서의 의미 매칭은 실제 OpenAI 모드로 별도 테스트하세요.
