# `dev/` — Reality Lab 로컬 개발 도구 모음

로컬 개발자용 문서 + 헬퍼 스크립트. 클론하면 바로 3개 서비스(사이트·챗봇·Admin CMS)를
띄우고 검증할 수 있습니다.

## 파일 목차

| 파일 | 용도 |
|---|---|
| `README.md` | 이 문서 |
| `DEVELOPMENT.md` | **메인 개발자 가이드** — 처음 오면 여기부터 |
| `cheatsheet.md` | 자주 쓰는 명령·자주 만나는 함정 |
| `serve_all.sh` / `stop_all.sh` | Linux/macOS — 3개 서비스 일괄 기동/종료 |
| `serve_all.ps1` / `stop_all.ps1` | Windows — 위와 동일 |

## 처음 오시는 분께

1. **Linux/macOS**: `../scripts/migrate/bootstrap_new_server.sh` 한 번이면
   Ruby·Jekyll·Python venv·RAG 인덱스까지 다 깔립니다.
   **Windows**: 부트스트랩 스크립트는 bash 전용입니다. `DEVELOPMENT.md` 의
   "Windows 세팅" 을 따르세요.
2. [`DEVELOPMENT.md`](DEVELOPMENT.md) 읽고 로컬에서 3개 서비스 띄우기
3. `_data/*.yml` 만 편집하고 싶다 → `DEVELOPMENT.md` 의 "콘텐츠만 편집" 섹션

## 포트

| 서비스 | Linux 기본 | Windows 기본 |
|---|---|---|
| Jekyll | 4000 | 4001 |
| 챗봇 | 4005 | 4205 |
| Admin CMS | 4010 | 4210 |

Windows 포트가 다른 이유는 두 가지입니다. VS Code 가 4005·4010 을 다른 머신으로
포워딩하고 있어 로컬 바인딩이 `WSAEACCES` 로 실패하고, **라이브 챗봇을 호스팅하는
PC 에서는 4105 가 프로덕션 인스턴스**라 개발용이 그 포트를 쓰면 공개 사이트가
죽습니다. 두 제약이 없는 머신이라면 `-ChatbotPort 4005` 처럼 넘겨서 맞출 수 있습니다.
