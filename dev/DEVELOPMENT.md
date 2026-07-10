# Reality Lab — 개발자 가이드

로컬에서 사이트 + 챗봇 + Admin CMS 를 돌리고, 수정하고, 검증하는 전체 흐름.

---

## 0. 처음 한 번 (환경 세팅)

### Linux / macOS

프로덕션 서버 부트스트랩과 동일합니다. 저장소 최상위에서:

```bash
./scripts/migrate/bootstrap_new_server.sh
```

이거 하나로 시스템 패키지(ruby, python3, cloudflared), Bundler + Jekyll,
Python venv(`.venv/`) + 의존성, Admin CMS 비밀번호 프롬프트, RAG 인덱스 확인,
임시 포트 챗봇 smoke test 까지 끝납니다.

### Windows

부트스트랩 스크립트는 bash 전용이라 수동입니다.

1. **Ruby** — [RubyInstaller **with MSYS2**](https://rubyinstaller.org/) 3.3.x 설치.
   conda 의 ruby 는 쓰지 마세요 (`mswin` 빌드라 `commonmarker`/`eventmachine` 이
   MSVC 에서 컴파일 실패).
2. **Gem** — `BUNDLE_PATH` 를 **저장소 밖**으로 두고 `bundle install`.
   저장소 안에 두면 Jekyll 이 `vendor/` 를 스캔하다 gem 내부 fixture 에서 빌드 실패합니다.
3. **Python** — conda env (예: `RS`, Python 3.11) 만들고
   `pip install -r ai_server/requirements.txt -r admin_cms/requirements.txt`
4. **Admin 비밀번호** — `python admin_cms/set_admin_password.py`

`.env` 는 저장소 루트에 하나만, 최소한 `OPENAI_API_KEY` 하나면 됩니다.
개발용은 본인 개인 키 쓰세요.

> Windows 계정에 다른 프로젝트용 `OPENAI_API_KEY` 환경변수가 있으면
> `load_dotenv()` 가 그걸 덮어쓰지 않아서 `.env` 가 무시됩니다.
> `serve_all.ps1` 은 실행 전에 그 변수를 비웁니다.

---

## 1. 3개 서비스 로컬 실행

**한 번에** (Linux/macOS):

```bash
./dev/serve_all.sh          # 백그라운드로 3개 다 기동
tail -f /tmp/reality-dev/*.log
./dev/stop_all.sh           # 종료
```

**한 번에** (Windows):

```powershell
powershell -ExecutionPolicy Bypass -File dev\serve_all.ps1
Get-Content $env:TEMP\reality-dev\chatbot.log -Wait
powershell -ExecutionPolicy Bypass -File dev\stop_all.ps1
```

둘 다 `all|jekyll|chatbot|admin` 인자를 받습니다.

**따로 띄우고 싶으면** (각각 다른 터미널, Linux 기준):

| 서비스 | 명령 | 접속 |
|---|---|---|
| Jekyll (사이트) | `bundle exec jekyll serve --port 4000 --livereload` | http://localhost:4000 |
| 챗봇 백엔드 | `source .venv/bin/activate && python3 ai_server/ai_chatbot_server.py --port 4005` | http://localhost:4005/health |
| Admin CMS | `source .venv/bin/activate && python3 admin_cms/admin_server.py --port 4010` | http://localhost:4010 |

Windows 는 포트가 4001 / 4205 / 4210 입니다 (이유는 `README.md`).

**포인트**: Jekyll 은 GitHub Pages 와 동일한 정적 사이트를 로컬 빌드합니다.
챗봇/Admin 은 프로덕션과 별개로 로컬에서 돕니다.

---

## 2. 시나리오별 워크플로우

### A. 논문 하나 추가하려면 (콘텐츠 편집자)

**옵션 1 — Admin CMS (권장)**
1. Admin CMS 기동 후 접속 → 로그인
2. Publications 페이지에서 "새 논문 추가" 폼 작성
3. 저장 → `_data/publications.yml` 반영 + 타임스탬프 백업 + Jekyll 빌드 + smoke test + 로컬 커밋
4. UI 의 "Apply/Push" 버튼 → 리모트 반영

**옵션 2 — 직접 YAML 편집**
1. `_data/publications.yml` 에 스키마대로 항목 추가
   ([`_data/README_PUBLICATIONS.md`](../_data/README_PUBLICATIONS.md))
2. 논문 이미지는 `assets/img/publications/<year>/` 에
3. **`international.md` 는 하드코딩이라 카드 하나 수동 추가 필요** (같은 형식 복사)
4. 로컬 Jekyll 로 미리보기
5. `git add ... && git commit && git push`

### B. 챗봇 시스템 프롬프트 / 답변 스타일 바꾸려면

1. `ai_server/ai_chatbot_server.py` 의 `SYSTEM_PROMPT_KO`, `SYSTEM_PROMPT_EN` 수정
2. 챗봇 재시작 후 검증:
   ```bash
   curl -s -X POST http://localhost:4005/chat \
        -H 'content-type: application/json' \
        -d '{"question":"연구실 위치 어디야?","mode":"deep"}' | jq
   ```
3. `_includes/chatbot.html` 을 로컬 챗봇에 붙이려면 `cheatsheet.md` 의 "로컬 챗봇 붙이기"

> `04:00–08:00 KST` 는 `is_rest_time()` 이 걸려 `/chat` 이 답변 대신
> "AI 쉬는시간" 을 반환합니다. 이 시간대 테스트는 그래서 실패처럼 보입니다.

### C. Admin CMS 에 새 편집 필드 추가하려면

1. `admin_cms/schemas.py` 에 스키마 규칙 추가
2. UI 는 별도 템플릿 폴더가 아니라 `admin_cms/admin_server.py` 의
   `render_template_string` + `admin_cms/static/admin-overlay.{css,js}` 조합입니다.
   여기를 고치세요.
3. 새 YAML 파일을 편집 대상에 넣으려면 `admin_cms/config.py` 의 `EDITABLE_FILES` 에 추가
4. admin 재시작 후 브라우저 새로고침

### D. RAG 품질 튜닝

1. `_data/chatbot_knowledge.yml` 에 Q&A 추가 → 답변에 "연구원이 검증한 정보 기반"
   초록 ✓ 배지가 붙습니다 (`qa` 카테고리에서 나오면 `verified_by_researchers=true`)
2. 인덱스만 재빌드:
   ```bash
   RESTART_CHATBOT=0 ./ai_server/update_rag.sh                       # Linux
   RESTART_CHATBOT=0 PYTHON_BIN=<conda RS python> bash ai_server/update_rag.sh   # Windows (Git Bash)
   ```
   Windows 에서 `RESTART_CHATBOT=1` 은 `pkill`/`nohup` 을 써서 동작하지 않습니다.
3. 챗봇 재시작 (또는 Admin CMS 의 `POST /api/rag/update`)
4. 질의 테스트

`ai_server/hierarchical_retriever.py` 의 `min_score`, `k` 튜닝 가능.
카테고리 분류 키워드도 같은 파일의 `category_keywords` 에 있습니다.

---

## 3. 콘텐츠만 편집 (Python·Ruby 몰라도 됨)

1. GitHub 웹 UI 로 저장소 열기
2. `_data/publications.yml` 등을 웹에서 직접 편집
3. "Commit changes" → `main`
4. 1~3분 후 https://reality.ssu.ac.kr 반영 확인

이걸로 안 되는 것: 이미지 업로드(경로 정확해야 함), `international.md` 같은
하드코딩 페이지, 논문 모달 등 인터랙션 확인.

---

## 4. 디버깅 치트시트

| 증상 | 확인할 곳 |
|---|---|
| Jekyll 빌드 실패 | 터미널의 Liquid/YAML 오류 → 대개 `_data/*.yml` syntax |
| `_site/` 이 이상하게 남음 | `rm -rf _site/ .jekyll-cache/` 후 재빌드 |
| 챗봇 500/503 | `serve_all` 로그 (`/tmp/reality-dev/` 또는 `%TEMP%\reality-dev\`) |
| 챗봇이 "AI 서버에 연결할 수 없습니다" | **네트워크 문제가 아닐 수 있음.** `call_openai()` 가 모든 예외를 삼키고 이 메시지를 냅니다. 로그의 `OpenAI ... error:` 줄을 보세요 |
| 챗봇이 답은 하는데 내용이 엉뚱 | `rag_loaded` 확인. Windows 에서 `PYTHONUTF8=1` 없으면 이모지 print 예외로 RAG 로딩이 통째로 실패합니다 |
| Admin CMS 로그인 실패 | `admin_cms/admin_config.json` 없으면 `set_admin_password.py` |
| Admin CMS "File too large" | `admin_cms/config.py` 의 `MAX_UPLOAD_SIZE` |
| RAG 가 새 콘텐츠를 못 찾음 | `update_rag.sh` 실행했는지 |
| 터널 URL 이 계속 바뀜 | 정상. cloudflared `--url` ephemeral 모드 |

---

## 5. PR / 배포 흐름

- **main 직접 push** 가 주류 — GitHub Pages 가 main 기준 자동 빌드
- 큰 변경은 브랜치 + PR
- 커밋 후 1~3분이면 프로덕션 반영. 사고나면 `git revert` 후 push

**푸시 전 체크리스트**:
- [ ] 로컬 Jekyll 빌드 통과?
- [ ] 논문/멤버 추가 시 `international.md` 도 반영?
- [ ] 이미지 파일도 커밋? (`git status`)
- [ ] `.env`, `admin_config.json` 같은 시크릿이 스테이징에 없는지?
- [ ] `.sh` 파일 편집 시 줄바꿈이 LF 인지? (Windows 에서 CRLF 로 커밋하면 서버에서 깨짐)

---

## 6. 참고

- 프로덕션 서버 구조: [`../scripts/migrate/README.md`](../scripts/migrate/README.md)
- 챗봇 내부: [`../ai_server/README.md`](../ai_server/README.md)
- Admin CMS 내부: [`../admin_cms/README.md`](../admin_cms/README.md)
- publications 스키마: [`../_data/README_PUBLICATIONS.md`](../_data/README_PUBLICATIONS.md)
- Windows 터널 감시자: [`../scripts/windows/tunnel_watchdog.ps1`](../scripts/windows/tunnel_watchdog.ps1)
- 자주 만나는 함정: [`cheatsheet.md`](cheatsheet.md)
