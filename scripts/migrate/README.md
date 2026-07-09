# Reality Lab — Server migration playbook

이 폴더는 홈페이지 관리 인프라(챗봇 + Admin CMS + 튜널 + 크론)를
**구 서버 → 새 서버**로 옮기기 위한 자동화 도구다.

## 배경

- 챗봇 백엔드가 로컬 `llama-server` (GPT-OSS-120B) → **OpenAI Chat Completions**
  (`gpt-5.5`) 로 전환됨. GPU 필요 없음.
- 홈페이지 자체는 GitHub Pages가 호스팅. 이 서버는 **관리·백엔드 인프라**만 담당.
- Cloudflare Tunnel은 기존 `--url` (ephemeral) 방식 유지.

## 파일

| 파일 | 용도 |
|---|---|
| `bootstrap_new_server.sh` | 새 서버에서 실행. 시스템 패키지 + Ruby/Jekyll + Python venv + 시크릿 체크리스트 |
| `crontab.new-server.txt` | 새 서버용 크론 (GPU 감시 크론 제외) |
| `bfg_dry_run.sh` | 히스토리 정리 시뮬레이션 (원본 미변경) |
| `bfg_apply.sh` | 히스토리 실제 정리 + force push (파괴적) |
| `systemd/*.service` | 재부팅 대응용 systemd 유닛 템플릿 |

## 전체 순서

### 1) 구 서버에서

```bash
# 1. 코드는 이미 GPT-5.5 API로 전환됨 (커밋됨). .env는 구 서버에도 만들어 두면 즉시 챗봇 검증 가능:
cp .env.example .env
$EDITOR .env    # OPENAI_API_KEY 채워넣기

# 2. 챗봇 헬스체크
source .venv/bin/activate  # 없으면 python3 -m venv .venv && pip install -r ai_server/requirements.txt
python3 ai_server/ai_chatbot_server.py --port 4006 &
curl -s http://localhost:4006/health | jq

# 3. (권장) 히스토리 정리 시뮬레이션
./scripts/migrate/bfg_dry_run.sh
# 만족스러우면 곧이어:
./scripts/migrate/bfg_apply.sh
```

### 2) 새 서버에서 — **오직 git + OpenAI 키 하나**로 끝

새 사람에게 넘겨줄 때 알려줘야 할 것:
1. GitHub repo URL (또는 SSH key 등록 방법)
2. **OpenAI API key** (한 개, 필수)
3. **원하는 admin 비밀번호** (자기가 새로 정함)

그 이상은 필요 없습니다. 나머지는 스크립트가 다 처리합니다.

```bash
# 1. clone
git clone git@github.com:ssurealitylab/ssurealitylab.github.io.git ~/Realitylab-site
cd ~/Realitylab-site

# 2. bootstrap — 시스템 패키지, Jekyll, Python venv, RAG index 자동 셋업.
#    도중에 admin 비밀번호를 물어봅니다 (bcrypt 해시로 저장됨).
./scripts/migrate/bootstrap_new_server.sh
# → 처음엔 .env를 만들고 멈춤. OPENAI_API_KEY 넣고:
$EDITOR .env

# 3. bootstrap 다시 실행 (idempotent — 이번엔 챗봇 smoke test까지 통과)
./scripts/migrate/bootstrap_new_server.sh

# 4. systemd + 크론
sudo cp scripts/migrate/systemd/reality-chatbot.service /etc/systemd/system/reality-chatbot@.service
sudo cp scripts/migrate/systemd/reality-admin.service   /etc/systemd/system/reality-admin@.service
sudo systemctl daemon-reload
sudo systemctl enable --now reality-chatbot@$USER reality-admin@$USER
crontab scripts/migrate/crontab.new-server.txt

# 5. 튜널 (cloudflared --url ephemeral, 로그인 불필요)
$HOME/Realitylab-site/ai_server/restart_tunnel.sh
$HOME/Realitylab-site/ai_server/restart_admin_tunnel.sh

# 6. E2E 검증
curl -s http://localhost:4005/health | jq   # 챗봇
curl -s http://localhost:4010/health | jq   # admin
```

**시크릿 SCP는 필요 없습니다** — `hierarchical_rag/`, `name_mapping.json`, `knowledge_base.json`은 git에 들어가 있고, `admin_config.json`은 bootstrap이 새로 생성해줍니다.

### 3) 컷오버

1. 새 서버 24시간 병행 관찰 (튜널 URL 자동 커밋이 오지 않아도 홈페이지 정상 표시되는지)
2. 구 서버 `crontab -e` → 모든 라인 앞에 `#` 처리 (삭제 X, 롤백용)
3. 구 서버 서비스 수동 종료: `pkill -f ai_chatbot_server; pkill -f admin_server; pkill cloudflared`
4. 최소 1주일 구 서버 파일 보존, 이상 없으면 정리

## 롤백

- **챗봇 GPT-5.5 → llama-server**: `git revert` (이 커밋). `start_server_and_tunnel.legacy.sh`가 남아 있으면 그걸 이름 변경.
- **BFG 히스토리 정리**: `bfg_apply.sh`가 만든 `~/reality-backup-<stamp>.git` mirror를 `git push --mirror --force origin` 하면 원상복구.
- **새 서버 이관 실패**: 구 서버 크론 주석 해제 → 즉시 원위치.
