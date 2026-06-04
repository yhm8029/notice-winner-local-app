# 데스크톱 WebView 앱

이 문서는 현재 로컬 웹앱을 Windows 프로그램 창으로 실행하는 WebView 배포 방식을 설명한다.

## 실행 방식

- `notice-winner.exe`를 실행하면 내부에서 FastAPI 서버가 `127.0.0.1` 임시 포트로 시작된다.
- 프로그램 창은 `pywebview`로 열리며 `/app/` 화면을 표시한다.
- 주소창과 브라우저 탭은 노출되지 않는다.
- 창을 닫으면 내부 서버 종료 신호도 같이 보낸다.

## 로컬 데이터 경로

데스크톱 앱은 실행 파일이 있는 폴더를 쓰기 가능한 앱 루트로 사용한다.

```text
notice-winner/
├─ notice-winner.exe
├─ data/
│  └─ local.sqlite3
└─ output/
   └─ artifacts/
```

기본 저장소 백엔드는 SQLite로 설정된다. 명시적인 환경변수가 이미 있으면 그 값을 우선한다.

## 개발 실행

```powershell
python -m pip install -r backend\requirements.txt -r requirements-desktop.txt
python -m desktop.launcher
```

고정 포트가 필요하면 다음처럼 실행한다.

```powershell
python -m desktop.launcher --port 8000
```

## exe 빌드

```powershell
.\scripts\build_desktop_exe.ps1 -InstallDependencies
```

현재 `data\local.sqlite3`를 배포 폴더에 같이 복사하려면 다음처럼 실행한다.

```powershell
.\scripts\build_desktop_exe.ps1 -InstallDependencies -IncludeLocalData
```

빌드 결과는 다음 위치에 생성된다.

```text
dist/notice-winner/notice-winner.exe
```

## 배포 시 주의사항

- `dist/notice-winner/` 폴더 전체를 옮기는 폴더형 배포가 기본이다.
- `data/local.sqlite3`는 사용자 데이터이므로 단일 exe 안에 넣지 않는다.
- G2B, 건축HUB, 세움터, 교육청 등 외부 조회 사이트 연결은 기존 웹앱 동작을 그대로 사용한다.
- WebView 런타임은 Windows WebView2/Edge 기반이다. 일반적인 Windows 10/11 환경에는 이미 설치되어 있다.
