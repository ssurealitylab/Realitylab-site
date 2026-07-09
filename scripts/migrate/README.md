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

### 2) 새 서버에서

```bash
# 1. GitHub SSH key 등록 (또는 https + PAT)
ssh-keygen -t ed25519 -C 'reality-lab-new-server'
cat ~/.ssh/id_ed25519.pub  # → GitHub Settings > Deploy keys 또는 개인키에 추가

# 2. clone + bootstrap
git clone git@github.com:JuHyoungLee02/Realitylab-site.git ~/Realitylab-site
cd ~/Realitylab-site
./scripts/migrate/bootstrap_new_server.sh

# 3. 시크릿 (구 서버에서 SCP)
#   admin_cms/admin_config.json
#   ai_server/name_mapping.json
#   ai_server/knowledge_base.json
#   ai_server/hierarchical_rag/
#   .env  (OPENAI_API_KEY)
#   ~/.cloudflared/  (cert 재사용하려면)

# 4. .env 최종 확인 후 재실행 (idempotent)
./scripts/migrate/bootstrap_new_server.sh

# 5. systemd 서비스 등록
sudo cp scripts/migrate/systemd/reality-chatbot.service /etc/systemd/system/reality-chatbot@.service
sudo cp scripts/migrate/systemd/reality-admin.service   /etc/systemd/system/reality-admin@.service
sudo systemctl daemon-reload
sudo systemctl enable --now reality-chatbot@$USER reality-admin@$USER

# 6. 크론
crontab scripts/migrate/crontab.new-server.txt
crontab -l

# 7. 튜널 (한쪽씩 검증)
$HOME/Realitylab-site/ai_server/restart_tunnel.sh
$HOME/Realitylab-site/ai_server/restart_admin_tunnel.sh

# 8. E2E 검증
curl -s http://localhost:4005/health | jq          # 챗봇
curl -s http://localhost:4010/health | jq          # admin
# 브라우저: reality.ssu.ac.kr → AI 챗 시도, admin 페이지 로그인
```

### 3) 컷오버

1. 새 서버 24시간 병행 관찰 (튜널 URL 자동 커밋이 오지 않아도 홈페이지 정상 표시되는지)
2. 구 서버 `crontab -e` → 모든 라인 앞에 `#` 처리 (삭제 X, 롤백용)
3. 구 서버 서비스 수동 종료: `pkill -f ai_chatbot_server; pkill -f admin_server; pkill cloudflared`
4. 최소 1주일 구 서버 파일 보존, 이상 없으면 정리

## 롤백

- **챗봇 GPT-5.5 → llama-server**: `git revert` (이 커밋). `start_server_and_tunnel.legacy.sh`가 남아 있으면 그걸 이름 변경.
- **BFG 히스토리 정리**: `bfg_apply.sh`가 만든 `~/reality-backup-<stamp>.git` mirror를 `git push --mirror --force origin` 하면 원상복구.
- **새 서버 이관 실패**: 구 서버 크론 주석 해제 → 즉시 원위치.
