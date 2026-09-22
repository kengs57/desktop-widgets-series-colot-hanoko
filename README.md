# 🐱 Python 데스크톱 위젯 시리즈 (코롯 & 하노코)

귀엽고 사랑스러운 바탕화면 캐릭터 데스크톱 위젯 프로젝트입니다.  
`PyQt6` 기반의 투명 위젯 창에 `pynput` 키보드 감지, `pycaw` 실시간 시스템 오디오/음악 재생 감지, 5단계 상태 머신, 마우스 인터랙션, 사운드 재생 및 말풍선 기능이 통합되어 있습니다.

본 프로젝트에는 **`코롯_데스크톱위젯`**(`src/main.py`) 및 **`하노코_데스크톱위젯`**(`src/main_2.py`) 2가지 서로 다른 이미지 구성 버전이 제공됩니다.

---

## ✨ 주요 기능 (Key Features)

- 🎵 **실시간 음악/오디오 재생 감지 & 5단계 상태 머신**:
  - 🎤 **음악 재생 중 (`Singing`)**: PC에서 노래/음악이 재생되면 마이크를 들고 노래하는 캐릭터 이미지 출력
  - 😵 **음악 멈춤 3초간 (`Exhausted`)**: 음악이 멈추면 3초 동안 마이크를 잡고 지쳐 힘들어하는 캐릭터 이미지 출력
  - ⌨️ **열일 중 (`Typing`)**: `pynput`으로 키보드 입력 감지 시 '열일하는 캐릭터'로 자동 전환
  - 💤 **평상시 (`Idle`)**: 기본 평상시 상태
  - 🛌 **유휴 (`Afk`)**: 5분(300초) 이상 입력이 없을 경우 '자거나 쉬는 캐릭터'로 자동 전환
- 💬 **마우스 좌클릭 인터랙션 & 사운드 & 말풍선**:
  - 위젯 좌클릭 시 말풍선 표시와 함께 캐릭터별 지정 효과음(코롯: 8종 신규 음성 중 무작위 1개 재생, 하노코: `aoaoaoao.mp3`)이 재생됩니다.
  - 클릭 시 캐릭터 상단에 3초간 말풍선이 캐릭터 위치 흔들림 없이 떴다가 사라집니다.
- 📐 **이미지 물리적 위치 100% 영구 고정 하단 앵커 (Fixed Bottom Anchor)**:
  - 투명 윈도우 컨테이너 규격을 고정하고 캐릭터를 바닥에 100% 락(Lock) 처리하여, 말풍선이 표시되거나 꺼져도 바탕화면 기준 단 1픽셀도 아래나 위로 밀리지 않습니다.
- 🖱️ **자유로운 드래그 이동 & 쉬운 종료**:
  - 마우스 좌클릭으로 바탕화면 어디든 자유롭게 드래그해 이동할 수 있습니다.
  - **우클릭 컨텍스트 메뉴**에서 `🚪 위젯 종료 (Quit)`를 클릭하거나, 위젯 선택 후 **`Esc` 키**를 누르면 즉시 종료됩니다.

---

## 🖼️ 버전에 따른 이미지 파일 매핑표

| 상태 (State) / 기능 | 코롯 버전 (`main.py`) | 하노코 버전 (`main_2.py`) |
| :--- | :--- | :--- |
| **🎤 음악 재생 중 (`Singing`)** | `assets/곧켁롯.png` | `assets/kimchi_love_hanoko.png` |
| **😵 음악 멈춤 3초간 (`Exhausted`)** | `assets/켁롯.png` | `assets/123d.png` |
| **💤 평상시 (`Idle`)** | `assets/cat_idle.png` | `assets/데뷔키링.png` |
| **⌨️ 열일 중 (`Typing`)** | `assets/cat_typing.png` | `assets/하노롱.png` |
| **🛌 5분 유휴 (`Afk`)** | `assets/cat_afk.png` | `assets/유휴5분.png` |
| **💬 3초 말풍선** | `assets/speech_tsundere.png` | `assets/누르면나오는거.png` |
| **🖼️ 기본 예비 이미지** | `assets/고양이메이드롯.png` | `assets/끗.png` |

---

## 📁 프로젝트 구조 (Directory Structure)

```text
d:/Anti_projects/
├── assets/                  # 🖼️ PNG 이미지 리소스 폴더
│   ├── kimchi_love_hanoko.png # 🎤 [하노코] 음악 재생 중 이미지
│   ├── 123d.png             # 😵 [하노코] 음악 멈춘 직후 3초간 이미지
│   ├── 데뷔키링.png         # 💤 [하노코] 평상시 이미지
│   ├── 하노롱.png           # ⌨️ [하노코] 열일 이미지
│   ├── 유휴5분.png          # 🛌 [하노코] 5분 유휴 이미지
│   ├── 누르면나오는거.png   # 💬 [하노코] 3초 말풍선 이미지
│   ├── 끗.png               # (Fallback) 하노코 예비 이미지
│   ├── 곧켁롯.png           # 🎤 [코롯] 음악 재생 중 이미지
│   ├── 켁롯.png             # 😵 [코롯] 음악 멈춘 직후 3초간 이미지
│   ├── cat_idle.png         # 💤 [코롯] 평상시 이미지
│   ├── cat_typing.png       # ⌨️ [코롯] 열일 이미지
│   ├── cat_afk.png          # 🛌 [코롯] 5분 유휴 이미지
│   ├── speech_tsundere.png  # 💬 [코롯] 3초 말풍선 이미지
│   └── 고양이메이드롯.png    # (Fallback) 코롯 예비 이미지
├── sounds/                  # 🔊 사운드 리소스 폴더
│   ├── 냐냐냐냐.wav 등 8종  # 코롯 신규 랜덤 효과음 (8종 중 무작위 1개 재생)
│   └── aoaoaoao.mp3         # 하노코 말풍선 효과음
├── src/                     # 💻 소스코드 폴더
│   ├── __init__.py
│   ├── main.py              # 코롯 데스크톱 위젯 메인 스크립트
│   ├── main_2.py            # 하노코 데스크톱 위젯 메인 스크립트
│   ├── widget.py            # PyQt6 기반 독립 위젯 로직
│   └── sound_player.py      # 사운드 관리 헬퍼
├── dist/                    # 📦 빌드 결과물 폴더
│   ├── 코롯_데스크톱위젯.exe # PyInstaller 코롯 실행 파일
│   └── 하노코_데스크톱위젯.exe # PyInstaller 하노코 실행 파일
├── build.py                 # 🛠️ 자동 빌드 스크립트 (--target 옵션 지원)
├── requirements.txt         # 📦 의존성 패키지 목록
└── README.md                # 📄 프로젝트 안내 문서
```

---

## 🚀 실행 및 빌드 방법 (Getting Started)

### 1. 가상환경 구축 및 의존성 패키지 설치
`build.py` 스크립트를 사용하여 가상환경(`.venv`)을 생성하고 의존성을 자동 설치합니다:
```bash
python build.py --setup
```

### 2. PyInstaller 독립 실행 파일(.exe) 패키징 빌드
* **전체 빌드 (코롯 & 하노코 둘 다)**:
  ```bash
  python build.py --build
  ```
* **하노코 위젯 전용 빌드 (`dist/하노코_데스크톱위젯.exe`)**:
  ```bash
  python build.py --build --target=2
  ```
* **코롯 위젯 전용 빌드 (`dist/코롯_데스크톱위젯.exe`)**:
  ```bash
  python build.py --build --target=1
  ```

### 3. 소스코드 수동 실행 (개발 환경)
* **하노코 위젯 실행**:
  ```bash
  .venv\Scripts\python.exe -m src.main_2
  ```
* **코롯 위젯 실행**:
  ```bash
  .venv\Scripts\python.exe -m src.main
  ```
