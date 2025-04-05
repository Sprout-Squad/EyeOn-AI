# ✨Project Convention✨
---

<br>

## ⚙️ 개발 환경 설정

> 아래 지침에 따라 가상환경을 구성하고 필수 라이브러리를 설치하세요.  
> 운영체제에 따라 명령어가 다릅니다.

---


## ✅ 1. VS Code 확장 설치

개발을 원활하게 진행하기 위해 아래 확장 프로그램을 설치해주세요.

### 🔌 필수 확장

- **Python** (by Microsoft)  
  Python 코드 실행 및 환경 설정

- **Jupyter** (by Microsoft)  
  `.ipynb` 노트북 파일 실행 및 작성

- **Pylance**  
  타입 추론 및 자동완성 강화

- **Jupyter Keymap** *(선택 사항)*  
  Jupyter 단축키 사용을 위한 확장


### 🍎 macOS / 🐧 Linux

```bash
# 1. 레포지토리 클론
git clone https://github.com/your-id/eyeon-ai.git
cd eyeon-ai

# 2. 가상환경 생성
python3 -m venv venv

# 3. 가상환경 활성화
source venv/bin/activate

# 4. 필수 라이브러리 설치
pip install -r requirements.txt
```

---

### 🪟 Windows (CMD 또는 PowerShell)

```bash
:: 1. 레포지토리 클론
git clone https://github.com/your-id/eyeon-ai.git
cd eyeon-ai

:: 2. 가상환경 생성
python -m venv venv

:: 3. 가상환경 활성화
venv\Scripts\activate        :: (CMD)
.\venv\Scripts\Activate.ps1  :: (PowerShell)

:: 4. 필수 라이브러리 설치
pip install -r requirements.txt
```

---

### ⛔ 가상환경 종료

> 가상환경을 종료하려면 아래 명령어를 입력하세요 (운영체제 공통):

```bash
deactivate
```

---

### 📦 새로운 라이브러리 추가 시

개발 중 새로운 패키지가 필요해 설치한 경우, 아래 명령어로 `requirements.txt`에 반영해주세요:

```bash
pip install 패키지명
pip freeze > requirements.txt
```

> 이렇게 해야 협업자들도 동일한 환경을 유지할 수 있습니다.

---

### 🧪 VS Code 설정 (Python 인터프리터 + Jupyter 커널 연동)

#### 🐍 Python 인터프리터 선택
1. `Ctrl + Shift + P`를 눌러 **Command Palette** 열기
2. `Python: Select Interpreter` 검색 후 실행
3. `./venv/bin/python` 또는 `.\venv\Scripts\python.exe` 선택

#### 📓 Jupyter Notebook 커널 연결
- `.ipynb` 파일 상단의 커널 선택 영역에서 `venv` 가상환경 커널 선택
- 목록에 없으면:
  ```bash
  python -m ipykernel install --user --name=venv
  ```
  위 명령어로 Jupyter 커널에 가상환경을 등록한 뒤 다시 시도

---
 
## ✉️ Commit Convention

커밋 메시지는 **Udacity 스타일**을 사용하며, 다음과 같은 구조로 작성

```
type: Subject (제목)

body (본문) (긴 설명이 필요한 경우에 작성)

footer  (꼬리말) (issue tracker ID를 명시하고 싶은 경우에 작성)
```
<br>


### 🛠 **type**: 커밋의 유형

| 타입       | 설명                                           |
|------------|------------------------------------------------|
| `feat`     | ✨ 새로운 기능 추가                               |
| `fix`      | 🐛 버그 수정                                      |
| `docs`     | 📝 문서 수정 (README, 주석 등)                    |
| `style`    | 💄 코드 포맷팅, 세미콜론 누락 등 기능 영향 없는 변경 |
| `refactor` | ♻️ 코드 리팩토링 (기능 변화 없음)                |
| `test`     | ✅ 테스트 코드 추가 또는 수정                    |
| `chore`    | 🔧 빌드 설정, 패키지 매니저 설정 등 기타 작업     |
| `perf`     | ⚡ 성능 개선                                      |
| `ci`       | 🔄 CI 관련 설정 및 스크립트 수정                 |
| `revert`   | ⚙️ 이전 커밋 되돌리기                            |

<br>

### 🖊️ **Subject**: 제목

- 50자 이내로 간결하게 작성
- 마침표(`.`) 금지
- 과거 시제 X, 명령어 사용

<br>

### 📝 **Body**: 본문

- **선택 사항**
- 제목에서 설명할 수 없는 추가 정보를 제공
- "무엇을"과 "왜"를 중심으로 상세히 기술
- 한 줄당 72자 이내로 작성
- 필요시 Markdown 사용 가능


---
<br>


## 🌿 Git Flow 브랜치 전략 (with `main`) 🌿


### 🌴 기본 브랜치
| 브랜치 | 역할 |
|--------|------|
| `main`     | 최종 배포용 브랜치 (stable) |
| `develop`  | 다음 배포를 위한 통합 개발 브랜치 |

<br>

### 🌱 **작업 브랜치 네이밍 규칙**

```
type/#issue번호  (작업 단위는 기능/수정/리팩토링 등으로 구분)
``` 


| prefix       | 설명                         | 예시                              |
|--------------|------------------------------|-----------------------------------|
| `feature/`   | ✨ 새로운 기능 개발             | `feature/#15`           |
| `fix/`       | 🐛 버그 수정                    | `fix/#42`     |
| `refactor/`  | ♻️ 코드 리팩토링                | `refactor/#23`       |
| `chore/`     | 🔧 설정 변경, 잡일              | `chore/#25`        |
| `perf/`      | ⚡ 성능 개선                    | `perf/#94`        |
| `hotfix/`    | 🚑 급한 수정 (main에서 바로 분기) | `hotfix/#102`          |
| `test/`      | 🧪 테스트 코드 추가/수정        | `test/#55`    |

<br>

### 🚀 브랜치 흐름 요약

```text
1. main ← 배포
2. develop ← 통합 개발 (PR 대상)
3. develop에서 feature/fix/... 브랜치 분기
4. 기능 완료 후 develop으로 PR & 머지
5. 배포 시 develop → main 머지
6. 급한 수정은 hotfix에서 main → develop 병합
```

---