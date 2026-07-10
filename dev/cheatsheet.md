# Cheatsheet — 자주 쓰는 명령 & 함정 모음

포트는 Linux 기본값(4000/4005/4010) 기준입니다. Windows 는 4001/4205/4210.

## 자주 쓰는 명령

```bash
# 1. Jekyll 로컬 미리보기 (자동 갱신)
bundle exec jekyll serve --port 4000 --livereload

# 2. Jekyll 캐시 완전 초기화 (뭔가 이상할 때)
rm -rf _site/ .jekyll-cache/
bundle exec jekyll build

# 3. RAG 인덱스만 재빌드 (챗봇 재시작 없이)
RESTART_CHATBOT=0 ./ai_server/update_rag.sh

# 4. 챗봇 헬스체크 — rag_loaded 와 api_key_present 를 꼭 보세요
curl -s http://localhost:4005/health | jq

# 5. 챗봇에 질문 던지기
curl -s -X POST http://localhost:4005/chat \
    -H 'content-type: application/json' \
    -d '{"question":"연구실 위치는?","mode":"deep"}' | jq

# 6. Admin CMS 비밀번호 재설정
python3 admin_cms/set_admin_password.py

# 7. 버전.yml 강제 갱신 (footer 버전 안 오를 때)
./update_version.sh

# 8. 사이트가 지금 가리키는 챗봇 주소 확인
grep -o "DIRECT_AI_SERVER_URL = '[^']*'" _includes/chatbot.html
```

---

## 함정 모음

### A. `_site/` 가 이상하게 남아있음

Jekyll 이 파일 삭제를 감지 못 해서 이전 빌드가 남아 있을 수 있음.

```bash
rm -rf _site/ .jekyll-cache/
bundle exec jekyll serve
```

### B. 한글 파일명 문제

논문 이미지는 반드시 `assets/img/publications/<year>/` 에 영문/숫자 파일명으로.

### C. 로컬 Jekyll 에서 챗봇 위젯이 프로덕션에 붙음

`_includes/chatbot.html` 에 프로덕션 터널 URL 이 하드코딩되어 있어서.
그 URL 은 터널이 재시작될 때마다 바뀌므로 여기 적어두지 않습니다. 현재 값은:

```bash
grep -o "DIRECT_AI_SERVER_URL = '[^']*'" _includes/chatbot.html
```

로컬 챗봇에 붙이려면 그 줄을 임시로 `http://localhost:4005` 로 바꾸세요
(Windows 는 `4205`). `_includes/bug-report.html` 에도 같은 상수가 있습니다.

**이 변경을 커밋하지 마세요.** `git stash` 로 임시 저장 후 개발, 끝나면 `git stash pop`.

> 터널 감시자(`scripts/windows/tunnel_watchdog.ps1`)가 URL 회전 시 이 두 파일을
> 자동으로 다시 쓰고 커밋합니다. 로컬 수정본을 커밋해두면 그 자동 커밋과 충돌합니다.

### D. `international.md` 는 하드코딩

`publications.yml` 에 논문을 추가해도 국제학회 페이지에는 자동 반영 안 됩니다.
`international.md` 에도 같은 형식으로 카드 하나 추가 필요. 파일 상단 주석 블록 참고.

### E. Admin CMS "Session expired" 무한 반복

`admin_config.json` 의 `secret_key` 가 재생성되면 기존 세션 무효화. 로그아웃 후 재로그인.

### F. 챗봇이 "AI 서버에 연결할 수 없습니다" — 네트워크 문제가 아닐 수 있음

`call_openai()` 는 **모든 예외를 삼키고** `None` 을 반환하며, 핸들러는 그걸
연결 오류 메시지로 표시합니다. 실제 원인은 서버 로그의 `OpenAI ... error:` 줄에 있습니다.
과거 사례: 모델이 `gpt-5.x` 인데 `max_tokens` / 비기본 `temperature` 를 보내서 400.

### G. `.env` 가 여러 곳에 있으면?

`ai_chatbot_server.py` 는 **저장소 루트의 `.env`** 만 읽습니다.
`ai_server/.env` 가 있어도 무시. 루트에 하나만 두세요.

그리고 **셸에 이미 `OPENAI_API_KEY` 가 export 되어 있으면 `.env` 가 무시됩니다.**
`load_dotenv()` 는 기존 환경변수를 덮어쓰지 않습니다.

### H. 저장소가 큼

로그·pid 파일은 이제 추적하지 않지만, 과거 커밋에 남아 있어 `.git` 이 ~1GB 입니다.
`scripts/migrate/bfg_dry_run.sh` 로 시뮬레이션 → `bfg_apply.sh` 로 정리 가능.
(히스토리 재작성이라 협업자 전원 재클론 필요.)

### I. Ruby 가 엉뚱한 걸 잡음

- **Linux**: conda 환경의 Ruby 를 잡으면 문제가 생깁니다. `which ruby` 로
  시스템 Ruby(`/usr/bin/ruby`) 가 잡히는지 확인, 아니면 `conda deactivate`.
- **Windows**: 반대로 conda ruby 를 **쓰면 안 됩니다.** `mswin` 빌드라
  `commonmarker` / `eventmachine` 이 MSVC 에서 컴파일 실패합니다.
  RubyInstaller(`x64-mingw-ucrt`) 를 쓰세요. `ruby -e "puts RUBY_PLATFORM"` 으로 확인.

### J. 포트가 이미 쓰이는 중

```bash
lsof -i :4005                     # Linux
pkill -f ai_chatbot_server.py
```
```powershell
Get-NetTCPConnection -LocalPort 4205 -State Listen   # Windows
powershell -File dev\stop_all.ps1
```

`bundle.bat` 은 자식 ruby 를 낳으므로 기록된 PID 만 죽이면 포트를 계속 물고 있습니다.
`stop_all.ps1` 은 포트를 붙들고 있는 프로세스까지 정리합니다.

### K. Windows: 챗봇은 뜨는데 답이 엉뚱함

콘솔이 cp949 라 로딩 중 이모지 `print` 가 예외를 내고, 그게 `load_rag()` 를 통째로
죽입니다. 서버는 정상 기동한 것처럼 보이지만 `/health` 의 `rag_loaded` 가 `false`.
`PYTHONUTF8=1` 을 주세요 (`serve_all.ps1` 은 이미 설정합니다).

### L. Windows: `.sh` 를 편집해 커밋하면 서버에서 깨짐

CRLF 로 저장되면 리눅스에서 `bad interpreter` 가 납니다. 커밋 전 확인:

```bash
git show HEAD:ai_server/update_rag.sh | file -
```
