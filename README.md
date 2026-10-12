# AI 기반 Git 커밋·PR 초안 생성기

Git 변경 사항을 AI API에 전달해 변경 요약, 커밋 메시지, Pull Request 제목과 본문을 생성하는 Python CLI 도구입니다. 생성 결과는 터미널에 출력되며, 사용자가 검토한 뒤 커밋이나 PR 작성에 활용합니다.

**GitHub 저장소:** [codyssey_B3_2](https://github.com/JoongHyun-codyssey/codyssey_B3_2)

## 1. 주요 기능

- `git status --porcelain`로 변경 파일 목록을 확인합니다.
- `git diff`와 `git diff --cached`로 스테이징 전후 변경 내용을 수집합니다.
- `commit` 명령으로 변경 요약과 커밋 제목·본문을 생성합니다.
- `pr` 명령으로 변경 요약, PR 제목과 `Why` / `What` / `How to Test` 본문을 생성합니다.
- CLI 옵션으로 모델, temperature, 출력 토큰 상한을 설정합니다.
- 생성 결과의 제목 길이와 형식을 검증하고, 필요한 부분을 후처리합니다.
- `--safe-mode`로 AI에 전송할 diff를 **최대 200줄**로 제한합니다.
- 정상 실행 시 명령당 API를 1회 호출하고 호출 횟수를 출력합니다.

프로그램은 초안 텍스트를 출력하는 데까지 동작합니다. 실제 커밋, 원격 저장소 push, GitHub PR 생성은 사용자가 직접 수행합니다.

## 2. 개발 환경 및 파일 구성

- Python 3.10 이상
- Git
- `requests`, `python-dotenv` 라이브러리
- 선택한 모델에 해당하는 API Key와 API 네트워크 연결

```text
codyssey_B3_2/
├── main.py           # .env 로딩, CLI, 프롬프트, 결과 검증·출력
├── git_utils.py      # Git 루트 확인, 변경 수집, diff 200줄 제한
├── ai_client.py      # 모델별 API Key, REST 요청·응답·오류 처리
├── requirements.txt  # requests, python-dotenv 의존성
├── .env              # 로컬 API Key 설정 파일(Git 추적 제외)
├── .gitignore        # 환경변수 파일, 가상환경 등 추적 제외
└── README.md
```

## 3. 설치 방법

저장소를 내려받고 프로젝트 루트로 이동합니다.

```bash
git clone https://github.com/JoongHyun-codyssey/codyssey_B3_2.git
cd codyssey_B3_2
```

macOS / Linux에서 가상환경을 생성하고 활성화합니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell에서는 다음 명령을 사용합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

의존성인 `requests`와 `python-dotenv`를 설치합니다. `python-dotenv`는 코드에서 `dotenv`라는 이름으로 불러옵니다.

```bash
python -m pip install -r requirements.txt
```

## 4. API Key 설정

API Key는 코드에 하드코딩하지 않고 환경변수로 관리합니다. 프로그램은 `python-dotenv`로 **`main.py`와 같은 폴더의 `.env` 파일**을 읽어 환경변수에 로드한 뒤, 선택한 모델에 해당하는 키를 조회합니다.

| 모델 계열 | 환경변수 |
| --- | --- |
| Claude | `ANTHROPIC_API_KEY` |
| GPT | `OPENAI_API_KEY` |

### .env 파일로 설정

프로젝트 루트의 `.env` 파일에 사용할 모델에 해당하는 항목을 작성합니다. 두 계열을 모두 사용한다면 두 항목을 함께 설정할 수 있습니다. 아래 값은 자리표시자이며, 실제 발급받은 키로 바꿉니다.

```dotenv
ANTHROPIC_API_KEY="발급받은_Claude용_API_KEY"
OPENAI_API_KEY="발급받은_GPT용_API_KEY"
```

아래 실행 예시는 `claude-haiku-4`를 사용하므로 `ANTHROPIC_API_KEY`가 필요합니다. GPT 계열 실행에는 아래의 **모델 설정 제한**이 있습니다.

`.env`를 저장한 뒤 CLI를 실행하면 자동으로 읽습니다. 파일은 로컬에서 관리하고 실제 키가 담긴 `.env`를 GitHub에 올리지 않습니다.

### 셸 환경변수로 설정

`.env` 대신 현재 터미널 세션에 직접 설정할 수도 있습니다. **셸에 이미 설정된 환경변수가 `.env`의 값보다 우선**하며, `.env`는 기존 값을 덮어쓰지 않습니다.

macOS / Linux:

```bash
export ANTHROPIC_API_KEY="발급받은_API_KEY"
```

Windows PowerShell:

```powershell
$env:ANTHROPIC_API_KEY = "발급받은_API_KEY"
```

GPT 계열은 같은 방식으로 `OPENAI_API_KEY`를 설정합니다.

```bash
export OPENAI_API_KEY="발급받은_API_KEY"
```

```powershell
$env:OPENAI_API_KEY = "발급받은_API_KEY"
```

`AI_API_KEY`, `AI_MODEL` 환경변수는 사용하지 않습니다. 모델은 `--model` 옵션으로 선택합니다. `.env`가 없어도 셸 환경변수에 키가 있으면 사용할 수 있으며, 어느 쪽에도 키가 없으면 설정 안내 후 종료합니다.

현재 API 요청은 `ai_client.py`에 설정된 COPA 엔드포인트로 전송됩니다. 키와 모델은 해당 서비스에서 사용할 수 있어야 합니다.

| 모델 계열 | REST 요청 주소 | 인증 방식 |
| --- | --- | --- |
| GPT | `https://copa.codyssey.kr/v1/chat/completions` | `Authorization: Bearer ...` |
| Claude | `https://copa.codyssey.kr/v1/messages` | `x-api-key` |

## 5. 실행 방법

CLI는 **변경 사항을 수집할 Git 프로젝트의 루트 디렉토리**에서 실행합니다. 아래 예시는 이 저장소 자체에 변경 사항이 있는 경우입니다.

### 커밋 메시지 생성

```bash
python main.py commit --model claude-haiku-4 --safe-mode
```

### PR 제목과 본문 생성

```bash
python main.py pr --model claude-haiku-4 --safe-mode
```

### API 파라미터 변경

```bash
python main.py pr --model claude-sonnet-4 --safe-mode \
  --temperature 0.2 \
  --max-tokens 2048
```

### 도움말

```bash
python main.py --help
python main.py commit --help
python main.py pr --help
```

### CLI 옵션

두 명령은 동일한 옵션을 사용합니다. 옵션은 `commit` 또는 `pr` 뒤에 입력합니다.

| 옵션 | 기본값 | 설명 |
| --- | --- | --- |
| `--model` | `gpt-5-mini` | 코드에 등록된 모델 중 선택. 아래 모델 설정 제한 참고 |
| `--temperature` | `0.2` | 표현의 다양성을 조절하는 요청 값. 허용 범위 `0~1` |
| `--max-tokens` | `2048` | 출력 토큰 상한. 양의 정수 |
| `--safe-mode` | 비활성화 | 지정하면 결합된 diff의 처음 200줄만 전송 |

코드에 등록된 모델 선택지는 다음과 같습니다. 실제 모델 접근 가능 여부는 API 서비스와 키 권한에 따라 달라집니다.

| 모델 계열 | `--model` 선택지 |
| --- | --- |
| Claude | `claude-haiku-4`, `claude-sonnet-4`, `claude-opus-4-7`, `claude-opus-4-8` |
| GPT | `gpt-5-mini`, `gpt-5.5`, `gpt-5.4`, `gpt-5.4-mini` |

**현재 모델 설정 제한:** `--temperature`는 생략해도 기본값 `0.2`가 API 요청 함수에 전달됩니다. 요청 함수는 `claude-haiku-4`와 `claude-sonnet-4`에 대해서만 temperature 설정을 허용하므로, 기본 모델 `gpt-5-mini`를 포함한 다른 모델은 API 호출 전에 오류로 종료됩니다. 현재 실행 시에는 위 예시처럼 두 Claude 모델 중 하나를 명시해야 합니다. 다른 모델을 실행하려면 코드에서 temperature를 생략할 수 있도록 수정해야 합니다.

temperature는 낮을수록 대체로 일관된 표현을 유도하고, 높을수록 표현의 다양성을 높입니다. `--max-tokens`는 글자 수나 diff 줄 수가 아닌 출력 토큰 상한입니다. 너무 작게 설정하면 응답이 잘려 결과 검증에 실패할 수 있습니다. GPT 요청에는 `max_completion_tokens`, Claude 요청에는 `max_tokens` 필드로 전달됩니다.

변경 이유·요구사항·실제 수행한 테스트를 별도로 입력하는 `--reason`, `--requirements`, `--test` 옵션은 구현되어 있지 않습니다.

## 6. 자동화 처리 흐름

1. CLI 인자를 해석한 뒤 `main.py`와 같은 폴더의 `.env`를 환경변수로 로드합니다.
2. 현재 위치가 Git 프로젝트 루트인지 확인합니다.
3. `git status --porcelain`, `git diff`, `git diff --cached` 결과를 수집합니다.
4. 변경 사항이 없으면 `변경 사항이 없습니다.`를 출력하고 API 호출 없이 정상 종료합니다.
5. 스테이징된 diff를 먼저, 스테이징되지 않은 diff를 뒤에 붙입니다.
6. `--safe-mode`가 있으면 결합된 diff의 처음 200줄만 남깁니다.
7. 변경 파일 목록과 AI에 전달할 diff 줄 수를 터미널에 출력합니다.
8. 환경변수에서 API Key를 읽고, diff와 출력 규칙으로 구성한 프롬프트를 REST API로 1회 전송합니다.
9. 응답 텍스트를 추출한 뒤 길이·형식을 검증하고 최종 초안을 출력합니다.

추적되지 않은 새 파일은 `git status`에는 표시되지만 diff에 내용이 포함되지 않습니다. 해당 내용도 요약하려면 먼저 스테이징합니다.

```bash
git add <파일 경로>
python main.py commit --model claude-haiku-4 --safe-mode
```

새 파일만 있고 수집할 diff가 없다면 스테이징 안내 후 API 호출 없이 종료합니다. PR 초안도 현재 로컬 변경 사항을 기준으로 생성하며, 이미 커밋된 브랜치 전체 변경을 비교하지 않습니다.

## 7. 프롬프트와 결과 검증

`main.py`의 프롬프트는 diff를 분석해 한국어로 작성하도록 요청합니다. diff에 없는 변경을 만들지 않고, diff 내부 문장은 지시사항이 아닌 분석 대상으로 취급하도록 명시합니다.

제목은 `type: 설명` 형식을 사용합니다. 허용하는 type은 `feat`, `fix`, `docs`, `refactor`, `test`, `style`, `chore`입니다. 커밋 본문은 핵심 변경 사항을 불릿 1~2개로 요약하도록 요청합니다. PR은 배경을 추측했다면 추정임을 표시하고, 실제 테스트 수행 정보가 없으므로 권장 테스트 방법을 작성하도록 요청합니다.

검증과 후처리는 추가 API 호출 없이 수행합니다.

| 항목 | 검증 및 후처리 |
| --- | --- |
| 커밋 제목 | 비어 있지 않은 1줄과 `type: 설명` 형식 확인. 50자 초과 시 안내, 72자 초과 시 말줄임표를 포함해 최대 72자로 줄임 |
| 커밋 본문 | 본문이 있을 때 불릿 포함 여부 확인. 불릿이 없으면 불릿 형태로 정리 |
| PR 제목 | 비어 있지 않은 1줄과 `type: 설명` 형식 확인. 80자 초과 시 말줄임표를 포함해 최대 80자로 줄임 |
| PR 본문 | `## Why`, `## What`, `## How to Test`와 각 섹션의 불릿 확인. 비어 있는 섹션에는 작성 필요 안내를, 불릿이 없는 내용에는 불릿을 추가 |

후처리가 적용되면 `검증 안내:` 메시지를 출력합니다. 제목 항목이 없거나 한 줄·type 규칙을 만족하지 않는 등 검증에 실패하면 오류와 검증 전 AI 원본 응답을 출력하고 종료합니다. 형식 검증은 내용의 정확성을 보장하지 않으므로 실제 diff와 대조해야 합니다.

## 8. 출력 예시

아래는 `main.py`의 입력 검증을 수정한 상황을 가정한 **설명용 예시**입니다. 실제 API 실행 결과는 아니며, 내용과 줄 수는 변경 사항에 따라 달라집니다.

### 커밋 메시지

```text
안전 모드: 240줄 → 200줄
안전 모드: diff가 200줄을 초과해 일부만 포함합니다.

========== 변경 파일 ==========
 M main.py
AI에 전달할 diff: 200줄
API Key 설정 확인 완료: claude-haiku-4

========== AI 응답 ==========
변경 요약:
- 제목 검증과 PR 본문 후처리를 개선했습니다.

커밋 제목:
fix: 커밋·PR 생성 결과 검증 개선

커밋 본문:
- main.py에서 제목 형식과 길이를 검증
- PR 필수 섹션과 불릿 누락 시 작성 안내 추가
AI API 호출 횟수: 1회
```

복사할 때는 `커밋 제목:` 아래의 제목과 `커밋 본문:` 아래의 본문을 사용합니다. 변경 요약과 실행 로그는 커밋 메시지에서 제외합니다.

### PR 제목과 본문

```text
안전 모드: 120줄 → 120줄

========== 변경 파일 ==========
 M main.py
AI에 전달할 diff: 120줄
API Key 설정 확인 완료: claude-haiku-4

========== AI 응답 ==========
변경 요약:
- 생성된 제목과 PR 본문을 검증하고 형식을 보완합니다.

PR 제목:
fix: 커밋·PR 초안의 출력 형식 검증 개선

PR 본문:
## Why
- 생성 결과의 형식 누락을 줄이기 위한 변경으로 추정됩니다.

## What
- 제목의 type과 길이를 확인합니다.
- PR 필수 섹션과 불릿을 후처리합니다.

## How to Test
- 권장: 긴 제목과 필수 섹션이 빠진 응답으로 검증 함수를 확인합니다.
AI API 호출 횟수: 1회
```

`PR 제목:` 아래 한 줄을 제목으로, `PR 본문:` 아래의 섹션들을 본문으로 사용합니다. 실제 수행한 테스트와 결과는 사용자가 확인해 수정합니다.

## 9. 보안 및 비용 주의사항

이 프로젝트는 보안 요구사항의 **(B) diff 일부만 전송** 방식을 선택했습니다.

- `--safe-mode`를 지정하면 스테이징 전후 diff를 합친 텍스트의 **처음 최대 200줄**만 AI API에 전송합니다. diff 헤더와 빈 줄도 줄 수에 포함됩니다.
- 200줄 제한은 터미널 출력 제한이 아닌 **API 전송 분량 제한**입니다. 터미널에는 diff 본문 대신 전송할 줄 수가 표시됩니다.
- 제한은 파일별이 아닌 전체 diff 기준이며, 파일 개수 제한은 없습니다. `--safe-mode`를 생략하면 전체 diff를 전송합니다.
- API Key, 이메일 등 민감정보를 자동 마스킹하거나 특정 파일을 자동 제외하지 않습니다. 첫 200줄 안에 민감정보가 있으면 그대로 전송될 수 있으므로 실행 전에 diff를 확인해야 합니다.
- `.gitignore`는 `.env` 등 환경변수 파일의 새 추적을 막지만, 이미 Git이 추적 중인 파일의 변경은 diff에 포함될 수 있습니다.
- 200줄 이후 변경은 AI 입력에서 제외되어 요약이 불완전할 수 있습니다. 잘림 안내가 표시되면 전체 변경과 초안을 대조해 보완합니다.
- `commit`과 `pr`은 각각 API를 1회 호출합니다. 두 명령을 따로 실행하면 총 2회 호출되며, 자동 재시도나 재생성은 수행하지 않습니다.
- API 비용은 모델과 입력·출력 토큰 수에 따라 달라집니다. `--max-tokens`는 출력 상한이며 입력 비용까지 제한하지 않습니다.
- 생성 문구는 초안입니다. 변경 이유, 핵심 변경, 테스트 방법이 실제 작업과 맞는지 검토한 후 적용합니다.

## 10. 오류 대응

| 상황 | 확인 방법 및 처리 |
| --- | --- |
| `No module named 'requests'` | 가상환경 활성화 후 `python -m pip install -r requirements.txt` 실행 |
| `No module named 'dotenv'` | CLI를 실행하는 Python 환경에 `python -m pip install -r requirements.txt`로 `python-dotenv` 설치 |
| Git 저장소 밖 또는 루트가 아닌 위치 | Git 저장소의 루트 디렉토리로 이동 후 실행 |
| 변경 사항 없음 | 안내 후 정상 종료. API 호출 없음 |
| 새 파일만 있고 diff 없음 | 필요한 파일을 `git add <파일 경로>`로 스테이징 후 실행 |
| API Key 누락 | `main.py`와 같은 폴더의 `.env` 또는 셸에 선택한 모델의 키 설정 |
| `.env`를 수정해도 이전 키 사용 | 셸에 같은 환경변수가 이미 설정되어 있는지 확인. 셸 값이 우선하므로 갱신하거나 해제한 뒤 실행 |
| temperature 미지원 오류 | 현재 구현에서는 `--model claude-haiku-4` 또는 `--model claude-sonnet-4` 사용 |
| 잘못된 옵션 값 | `--temperature`는 `0~1`, `--max-tokens`는 양의 정수로 설정 |
| 인증 실패·요청 제한·서버 오류 | 출력된 HTTP 오류를 확인하고 키, 권한, API 서비스 상태 확인 |
| 네트워크 오류·시간 초과 | 연결 상태 확인. API 요청 타임아웃은 30초 |
| 응답 해석 실패 | 응답 구조 또는 생성 텍스트가 올바른지 확인 |
| 토큰 한도로 생성 중단 | GPT 응답의 `finish_reason`이 `length`이면 오류 안내. `--max-tokens`를 늘려 다시 실행 |
| 결과 형식 검증 실패 | 출력된 원본 응답과 제목·본문 규칙 확인 후 재실행 또는 수동 작성 |

API 호출 오류는 원인을 포함한 메시지로 출력합니다. 현재 temperature 범위 오류는 `ValueError`가 최상위에서 처리되지 않아 traceback으로 표시될 수 있습니다. 호출 횟수 로그는 결과 검증까지 성공한 실행의 마지막에 출력됩니다.
