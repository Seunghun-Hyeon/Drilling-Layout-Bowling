# Drilling-Layout-Bowling

🎳 Bowling 3D Layout & Track Simulator

볼링 지공 레이아웃(Dual Angle / 2LS / VLS) · 코어 세차운동(Precession) · 2D 레인 오일 패턴 3D 물리 시뮬레이터

볼링공 내부의 코어 동역학(RG, Diff, Inter Diff)과 볼러의 지공 데이터(PAP, 스팬, 엄지 옵셋, 레이아웃 각도), 그리고 실제 KEGEL 오일 패턴 시트(2D 오일 분포)를 결합하여 오일 트랙 플레어(Track Flare)와 60ft 레인 위의 3D 볼 궤적(Skid → Hook → Roll)을 실시간으로 시각화하는 웹 애플리케이션입니다.

✨ 주요 기능 (Key Features)

1. 3대 지공 레이아웃 시스템 & 구면 기하학 계산

Dual Angle System: Drilling Angle(°) × Pin-to-PAP(") × VAL Angle(°)

2LS (Two-Handed Layout System): 투핸드/덤리스 표준 차트(1번~6번 프리셋) 및 커스텀 수치(Pin-to-PAP × Pin-to-COG × Pin-buffer) 지원

VLS (Vector Layout System): Pin-to-PAP(") × PSA-to-PAP(") × Pin-to-VAL(") 및 Pin Up/Down 지원

그립 및 홀 설정: 원핸드(3홀: 스팬 길이 및 Thumb Offset 조절) 및 투핸드/덤리스(2홀) 전환 지원

구면 대원(Great Circle) 정밀 투영: 반지름 4.295"(15lb 표준) 구면 위에서 Pin, PSA(MB), PAP, CG, VAL 라인 및 지공 홀의 위치를 3D로 정확히 계산

2. 코어 활성화(Spin Axis Migration) & 트랙 플레어 3D 시각화

코어 3축 정렬 모델링: 최저 RG축(Pin), 최고 RG축(PSA), 중간 RG축을 3D 타원체로 시각화

세차운동(Precession) & 보타이(Bowtie) 분석: 투구 직후 초기 회전축(PAP)이 최종 회전축(PSA/적도)으로 이동하는 경로와 오일 링의 전개 면적을 실시간 계산

구간별 트랙 색상 분리: 브레이크 포인트 이전(Head ~ Midlane, 금색)과 이후(Breakpoint ~ Backend, 빨간색)의 트랙 링 변화를 구분하여 표시

트랙 판정 자동화: 첫 오일 트랙과 홀(엄지/중약지) 사이의 거리를 계산해 하이 트랙 / 미디엄 트랙 / 로우 트랙 자동 분류

3. 실제 KEGEL 오일 패턴 2D 히트맵 & 3D 물리 엔진

KEGEL IKON (43ft / 25.6mL / Ratio 4.17:1) 패턴 탑재: Forward 패스(15.8mL)와 Reverse 브러시 드롭(9.8mL) 데이터를 39보드 × 60ft 2D 그리드로 구현

커스텀 패턴 지원: 표준 하우스 패턴 및 스포츠 플랫 패턴(32ft~48ft) 선택 가능

실시간 마찰 및 구간 분리: 볼이 지나가는 보드와 거리의 오일 두께를 실시간으로 조회하여 Skid(청록) → Hook(빨강) → Roll(보라) 3단계 궤적을 시뮬레이션

스페어볼 물리 분리: 폴리에스터/플라스틱 외피 선택 시 드라이존에서도 훅 가속도를 억제하여 실제 스페어 궤적을 재현

4. 투구 스펙 양방향 연동 & 프리셋 관리

투구 각도(Launch Angle °) ↔ 타겟 보드 양방향 연동: 출발 보드(레이다운)와 에임 스팟(15ft)을 조절하면 투구 각도가 자동 역산되며, 각도를 직접 입력하면 타겟 보드가 자동 계산됨

JSON 프리셋 저장/불러오기: 선수별 지공 데이터 및 AISPO 트래킹 실측 데이터(초구 스트라이크, 10번 핀 스페어) 원클릭 전환 및 커스텀 프리셋 영구 저장

🛠️ 기술 스택 (Tech Stack)

Language: Python 3.9+

Web Framework: Streamlit

3D Visualization: Plotly (go.Surface, go.Scatter3d, make_subplots)

Scientific Computing: NumPy, SciPy (scipy.spatial.transform.Rotation)

🚀 설치 및 실행 방법 (Getting Started)

1. 저장소 클론

git clone https://github.com/your-username/bowling-3d-simulator.git
cd bowling-3d-simulator


2. 필수 패키지 설치

pip install streamlit numpy scipy plotly


3. 시뮬레이터 실행

streamlit run bowling_sim_app_v11.py


실행 후 브라우저에서 http://localhost:8501 로 접속하여 바로 시뮬레이션을 조작할 수 있습니다.

📁 프로젝트 구조

├── bowling_sim_app_v11.py   # 메인 Streamlit 웹 앱 및 3D 물리/기하학 엔진
├── bowling_presets.json     # 선수 및 트래킹 데이터 프리셋 저장소 (자동 생성)
└── README.md                # 프로젝트 문서


🎮 사용 가이드 (Workflow)

상단 프리셋 선택: 기본 탑재된 Awesome_data 또는 AISPO_초구_스트라이크, AISPO_10번핀_스페어 버튼을 눌러 기준 데이터를 불러옵니다.

지공 & 코어 설정 (사이드바 1~3번): 본인의 PAP(가로/상하), 스팬, 레이아웃 방식과 볼의 RG / Diff / Inter Diff, 외피 재질, 샌딩 그릿을 입력합니다.

투구 & 레인 설정 (사이드바 4번): 스피드(km/h), 회전수(RPM), 축 회전/기울기, 오일 패턴(KEGEL IKON 등), 레이다운 보드와 에임 스팟(또는 투구 각도)을 조절합니다.

3D 결과 분석:

좌측 3D 뷰: 지공 홀 위치, 코어 방향, 트랙 플레어 폭 및 홀 간섭 여부를 마우스로 회전하며 확인합니다.

우측 3D 뷰: 레인 위의 오일 분포 히트맵과 브레이크 포인트, 핀 데크 입사 보드(17.5번 포켓)를 확인합니다.

하단 차트: 1~39번 보드별 오일 적재 프로파일 단면도를 통해 공략 라인을 점검합니다.
