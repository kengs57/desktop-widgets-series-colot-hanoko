import sys
import os
from pathlib import Path

# --- Windows 환경에서 외부 Qt DLL 충돌 방지 및 안전 로드 설정 ---
if sys.platform == "win32":
    qt_paths = []
    
    # 1) PyInstaller 실행 파일 내부 번들 경로
    if hasattr(sys, '_MEIPASS'):
        base_path = Path(sys._MEIPASS)
        qt_paths.append(base_path)
        qt_paths.append(base_path / "PyQt6")
        qt_paths.append(base_path / "PyQt6" / "Qt6" / "bin")
    
    # 2) 파이썬 실행 환경 site-packages 경로
    py_dir = Path(sys.executable).parent
    qt_paths.append(py_dir / "Lib" / "site-packages" / "PyQt6" / "Qt6" / "bin")
    try:
        import site
        for s_dir in site.getsitepackages() + [site.getusersitepackages()]:
            qt_paths.append(Path(s_dir) / "PyQt6" / "Qt6" / "bin")
    except Exception:
        pass

    # 3) PATH 환경변수 재구성: 내장 Qt 경로를 1순위로 선점
    current_paths = os.environ.get("PATH", "").split(os.path.pathsep)
    clean_paths = []
    
    for qp in qt_paths:
        if qp.exists():
            qp_str = str(qp)
            if qp_str not in clean_paths:
                clean_paths.append(qp_str)
            try:
                os.add_dll_directory(qp_str)
            except Exception:
                pass

    for p in current_paths:
        p_lower = p.lower()
        if ("anaconda" in p_lower or "miniconda" in p_lower) and "library\\bin" in p_lower:
            continue
        if p and p not in clean_paths:
            clean_paths.append(p)

    os.environ["PATH"] = os.path.pathsep.join(clean_paths)

import time
from enum import Enum, auto
from PyQt6.QtCore import Qt, QPoint, QTimer
from PyQt6.QtGui import QPixmap, QGuiApplication, QMouseEvent, QAction
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QMenu
from pynput import keyboard

# pygame.mixer 오디오 라이브러리 로드
try:
    import pygame
    pygame.mixer.init()
    AUDIO_ENABLED = True
except Exception as e:
    AUDIO_ENABLED = False
    print(f"[Warning] 오디오 시스템 초기화 실패: {e}")

# pycaw Windows 시스템 오디오 출력 피크 감지 모듈 로드
PYCAW_AVAILABLE = False
try:
    import comtypes
    from pycaw.pycaw import AudioUtilities, IAudioMeterInformation
    from comtypes import CLSCTX_ALL
    PYCAW_AVAILABLE = True
except Exception as e:
    print(f"[Warning] pycaw 오디오 감지 모듈 로드 실패: {e}")

def get_system_audio_peak() -> float:
    """Windows 기본 스피커의 현재 오디오 출력 피크 수치(0.0 ~ 1.0) 반환"""
    if not PYCAW_AVAILABLE:
        return 0.0
    try:
        try:
            comtypes.CoInitialize()
        except Exception:
            pass

        speakers = AudioUtilities.GetSpeakers()
        if not speakers:
            return 0.0
        
        # 최신 pycaw (AudioDevice wrapper) 및 구버전 pycaw 모두 지원
        if hasattr(speakers, '_dev'):
            unk = speakers._dev.Activate(IAudioMeterInformation._iid_, CLSCTX_ALL, None)
        elif hasattr(speakers, 'Activate'):
            unk = speakers.Activate(IAudioMeterInformation._iid_, CLSCTX_ALL, None)
        else:
            return 0.0

        if unk:
            meter = unk.QueryInterface(IAudioMeterInformation)
            if meter:
                return meter.GetPeakValue()
    except Exception:
        pass
    return 0.0

class State(Enum):
    IDLE = auto()       # 💤 평상시 (하노코데뷔키링.png)
    TYPING = auto()     # ⌨️ 열일 중 (타이핑: 하노롱.png)
    AFK = auto()        # 🛌 5분 유휴 (입력 없음: 멘헤라노코.png)
    SINGING = auto()    # 🎤 음악 재생 중 (김치사랑노코.png)
    EXHAUSTED = auto()  # 😵 음악 멈춘 후 3초간 (화난하노코.png)

def get_base_dir() -> Path:
    """
    PyInstaller 단일 실행 파일(--onefile) 환경과 일반 파이썬 실행 환경을 모두 지원하는
    기준 베이스 경로 반환 함수
    """
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent

class TransparentWindow(QMainWindow):
    """
    하노코 데스크톱 위젯 (main_2.py 버전)
    상태 머신(Idle, Typing, Afk, Singing, Exhausted), 오디오 피크 감지,
    하단 앵커 고정 오버레이, 3초 음악 멈춤 유지 기능 통합 구현
    """
    AFK_THRESHOLD_SECONDS = 300        # 5분 이상 입력 없을 시 AFK
    TYPING_TIMEOUT_SECONDS = 3         # 입력 후 3초간 TYPING 상태 유지
    MUSIC_STOP_EXHAUSTED_SECONDS = 3    # 음악 멈춘 후 3초간 EXHAUSTED 상태 유지
    AUDIO_PEAK_THRESHOLD = 0.003       # 오디오 재생 감지 피크 임계값

    # --- 📐 이미지 크기 통일 규격 설정 (픽셀 단위) ---
    CHARACTER_MAX_WIDTH = 250          # 캐릭터 이미지 최대 가로 크기
    CHARACTER_MAX_HEIGHT = 250         # 캐릭터 이미지 최대 세로 크기
    SPEECH_BUBBLE_MAX_WIDTH = 220      # 말풍선 이미지 최대 가로 크기
    SPEECH_BUBBLE_MAX_HEIGHT = 120     # 말풍선 이미지 최대 세로 크기

    # 윈도우 전체 컨테이너 고정 크기 (말풍선 120px + 캐릭터 250px)
    WINDOW_CONTAINER_WIDTH = 270
    WINDOW_CONTAINER_HEIGHT = 360

    def __init__(self, base_dir: Path):
        super().__init__()
        self.base_dir = base_dir
        self.assets_dir = base_dir / "assets"
        self.sounds_dir = base_dir / "sounds"

        # 마우스 드래그 관련 변수
        self._is_dragging = False
        self._drag_pos = QPoint()

        # 상태 머신 및 오디오 감지 관련 변수
        self.current_state = None
        self.last_input_time = time.time()
        self.last_music_time = 0.0       # 마지막 외부 음악(오디오) 감지 시각
        self.last_self_sound_time = 0.0  # 위젯 자체 야옹 효과음 발생 시각

        # =========================================================================
        # 🖼️ [하노코 버전 상태별 이미지 파일 경로 매핑]
        # =========================================================================
        self.image_files = {
            # 1) 🎤 음악 재생 중 (Singing): 김치사랑노코.png
            State.SINGING: [
                self.assets_dir / "김치사랑노코.png",
                self.assets_dir / "끗.png",
            ],

            # 2) 😵 음악 멈춘 후 3초간 (Exhausted): 화난하노코.png
            State.EXHAUSTED: [
                self.assets_dir / "화난하노코.png",
                self.assets_dir / "끗.png",
            ],

            # 3) 💤 평상시 (Idle): 하노코데뷔키링.png
            State.IDLE: [
                self.assets_dir / "하노코데뷔키링.png",
                self.assets_dir / "끗.png",
            ],

            # 4) ⌨️ 열일 중 (Typing): 하노롱.png
            State.TYPING: [
                self.assets_dir / "하노롱.png",
                self.assets_dir / "끗.png",
            ],

            # 5) 🛌 5분 유휴 (Afk): 멘헤라노코.png
            State.AFK: [
                self.assets_dir / "멘헤라노코.png",
                self.assets_dir / "끗.png",
            ],
        }

        # 6) 💬 마우스 좌클릭 시 3초간 띄우는 말풍선 이미지: 하무스타와의추억사진노코.png
        self.speech_bubble_files = [
            self.assets_dir / "하무스타와의추억사진노코.png",
            self.assets_dir / "끗.png",
        ]

        # 1. 테두리 제거 및 항상 최상단 설정
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint
        )

        # 2. 배경 완전히 투명화
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # 3. 윈도우 컨테이너 고정 크기 지정 (말풍선이 켜져도 전체 창 및 캐릭터 위치가 미동도 없음)
        self.setFixedSize(self.WINDOW_CONTAINER_WIDTH, self.WINDOW_CONTAINER_HEIGHT)

        central_widget = QWidget(self)
        central_widget.setFixedSize(self.WINDOW_CONTAINER_WIDTH, self.WINDOW_CONTAINER_HEIGHT)
        self.setCentralWidget(central_widget)

        # 캐릭터 이미지를 표시할 Label (컨테이너 하단 중앙에 영구 고정)
        self.image_label = QLabel(central_widget)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 말풍선 이미지를 표시할 Label (캐릭터 머리 위 오버레이)
        self.speech_label = QLabel(central_widget)
        self.speech_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.speech_label.setVisible(False)

        # 말풍선 타이머 객체 생성 (단발성 3초 타이머)
        self.speech_timer = QTimer(self)
        self.speech_timer.setSingleShot(True)
        self.speech_timer.timeout.connect(self.hide_speech_bubble)

        # 초기 상태(IDLE) 설정 및 이미지 로드
        self.change_state(State.IDLE)

        # 4. 화면 중앙에 위치 배치
        self.center_on_screen()

        # 5. 상태 및 오디오 감지 체크 타이머 설정 (200ms 주기)
        self.state_timer = QTimer(self)
        self.state_timer.timeout.connect(self.check_state_update)
        self.state_timer.start(200)

        # 6. 전역 키보드 감지 리스너 시작
        self.start_keyboard_listener()

    def update_fixed_layout(self):
        """
        윈도우 전체 창 크기를 고정(Fixed)하고 캐릭터를 맨 아래 하단에 절대 배치하여,
        말풍선이 나타나거나 사라져도 캐릭터 위치가 단 1픽셀도 흔들리지 않도록 완벽 고정.
        """
        char_pix = self.image_label.pixmap()
        char_w = char_pix.width() if char_pix and not char_pix.isNull() else 200
        char_h = char_pix.height() if char_pix and not char_pix.isNull() else 200

        # 캐릭터는 컨테이너 하단 중앙에 100% 완벽 고정
        char_x = (self.WINDOW_CONTAINER_WIDTH - char_w) // 2
        char_y = self.WINDOW_CONTAINER_HEIGHT - char_h
        self.image_label.setGeometry(char_x, char_y, char_w, char_h)

        # 말풍선 위치: 캐릭터 바로 위쪽 머리 위 오버레이 (약 10px 겹침)
        speech_pix = self.speech_label.pixmap()
        if self.speech_label.isVisible() and speech_pix and not speech_pix.isNull():
            sp_w = speech_pix.width()
            sp_h = speech_pix.height()
            
            sp_x = (self.WINDOW_CONTAINER_WIDTH - sp_w) // 2
            sp_y = max(0, char_y - sp_h + 10)
            
            self.speech_label.setGeometry(sp_x, sp_y, sp_w, sp_h)
            self.speech_label.raise_()

    def change_state(self, new_state: State):
        """상태 변경 및 고품질 크기 규격 제한(Smooth Scaling) 적용"""
        if self.current_state == new_state:
            return

        self.current_state = new_state
        print(f"[State Machine - 하노코] 상태 변경 -> {new_state.name}")

        candidates = self.image_files.get(new_state, [])
        image_path = next((p for p in candidates if p.exists()), None)

        pixmap = QPixmap(str(image_path)) if image_path and image_path.exists() else QPixmap()
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                self.CHARACTER_MAX_WIDTH,
                self.CHARACTER_MAX_HEIGHT,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            self.update_fixed_layout()
        else:
            self.image_label.resize(200, 200)

    def check_state_update(self):
        """음악/오디오 피크 및 키보드 입력 경과 시간에 따라 상태 자동 전환"""
        now = time.time()
        
        # 위젯 자체 말풍선 효과음이 나오는 3초 동안은 외부 음악 재생으로 오인하지 않도록 예외 차단
        is_self_sound_playing = (now - self.last_self_sound_time) < 3

        # 1. Windows 스피커 오디오 피크 모니터링 (외부 음악/소리 재생 감지)
        peak = get_system_audio_peak()
        is_music_playing = (peak >= self.AUDIO_PEAK_THRESHOLD) and (not is_self_sound_playing)

        if is_music_playing:
            self.last_music_time = now
            self.change_state(State.SINGING)
            return

        # 2. 음악이 나오다가 멈춘 지 3초 이내인 경우 -> EXHAUSTED (마이크 잡고 힘들어하는 이미지)
        time_since_music_stopped = now - self.last_music_time
        if self.last_music_time > 0 and time_since_music_stopped < self.MUSIC_STOP_EXHAUSTED_SECONDS:
            self.change_state(State.EXHAUSTED)
            return

        # 3. 음악이 멈춘 지 3초가 지난 후 -> 기존 키보드/유휴 상태 로직 적용
        elapsed_input = now - self.last_input_time

        if elapsed_input >= self.AFK_THRESHOLD_SECONDS:
            self.change_state(State.AFK)
        elif elapsed_input < self.TYPING_TIMEOUT_SECONDS:
            self.change_state(State.TYPING)
        else:
            self.change_state(State.IDLE)

    def center_on_screen(self):
        """현재 주 모니터의 사용 가능한 영역 중앙으로 윈도우 이동"""
        screen = QGuiApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            window_geometry = self.frameGeometry()
            center_point = screen_geometry.center()
            window_geometry.moveCenter(center_point)
            self.move(window_geometry.topLeft())

    # --- 클릭 시 사운드 및 말풍선 처리 ---
    def play_meow_sound(self):
        """하노코 위젯 말풍선 효과음 재생 (우선순위: aoaoaoao.mp3)"""
        # 자체 말풍선 효과음 재생 시각 기록 (외부 음악 오감지 차단용)
        self.last_self_sound_time = time.time()

        sound_candidates = [
            self.sounds_dir / "aoaoaoao.mp3"
        ]
        sound_path = next((p for p in sound_candidates if p.exists()), None)

        if sound_path and AUDIO_ENABLED:
            try:
                sound = pygame.mixer.Sound(str(sound_path))
                sound.play()
                print(f"[Sound] 하노코 말풍선 효과음 재생: {sound_path.name}")
            except Exception as e:
                print(f"[Error] 사운드 재생 에러: {e}")
        else:
            print("[Notice] 하노코 말풍선 효과음 파일을 찾을 수 없거나 오디오가 비활성화되었습니다.")

    def show_speech_bubble(self):
        """말풍선 이미지 고품질 크기 스케일링 후 캐릭터 상단에 3초간 오버레이 표시"""
        speech_path = next((p for p in self.speech_bubble_files if p.exists()), None)

        if speech_path and speech_path.exists():
            pixmap = QPixmap(str(speech_path))
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    self.SPEECH_BUBBLE_MAX_WIDTH,
                    self.SPEECH_BUBBLE_MAX_HEIGHT,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.speech_label.setPixmap(scaled_pixmap)
                self.speech_label.setVisible(True)
                self.update_fixed_layout()

                # 3초 말풍선 타이머 시작
                self.speech_timer.start(3000)
                print(f"[Speech Bubble] 말풍선 표시: {speech_path.name} (3초간 유지)")
        else:
            print("[Notice] 표시할 말풍선 이미지 파일이 존재하지 않습니다.")

    def hide_speech_bubble(self):
        """말풍선 감추기 (캐릭터 위치 100% 고정)"""
        self.speech_label.setVisible(False)
        self.update_fixed_layout()
        print("[Speech Bubble] 말풍선 숨김")

    # --- 🖱️ 마우스 이벤트 (좌클릭 드래그 / 우클릭 팝업 메뉴) ---
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

            # 좌클릭 시 사운드 재생 및 말풍선 띄우기
            self.play_meow_sound()
            self.show_speech_bubble()

            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._is_dragging and (event.buttons() & Qt.MouseButton.LeftButton):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = False
            event.accept()

    def contextMenuEvent(self, event):
        """위젯 우클릭 시 컨텍스트 팝업 메뉴 표시 (종료 기능 추가)"""
        menu = QMenu(self)

        status_name = self.current_state.name if self.current_state else "IDLE"
        status_action = QAction(f"📌 하노코 위젯 상태: {status_name}", self)
        status_action.setEnabled(False)
        menu.addAction(status_action)

        menu.addSeparator()

        quit_action = QAction("🚪 하노코 위젯 종료 (Quit)", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(quit_action)

        menu.exec(event.globalPos())

    def keyPressEvent(self, event):
        """Esc 키 입력 시 위젯 빠르게 종료"""
        if event.key() == Qt.Key.Key_Escape:
            print("[System] Esc 키 입력으로 하노코 위젯을 종료합니다.")
            QApplication.instance().quit()
        else:
            super().keyPressEvent(event)

    # --- pynput 전역 키보드 입력 감지 로직 ---
    def start_keyboard_listener(self):
        def on_press(key):
            self.last_input_time = time.time()

        self.keyboard_listener = keyboard.Listener(on_press=on_press)
        self.keyboard_listener.daemon = True
        self.keyboard_listener.start()
        print("[System] 전역 키보드 입력 감지 리스너가 시작되었습니다.")

    def closeEvent(self, event):
        """윈도우 종료 시 pynput 키보드 리스너 중지"""
        if hasattr(self, 'keyboard_listener') and self.keyboard_listener:
            self.keyboard_listener.stop()
        event.accept()

def main():
    app = QApplication(sys.argv)

    base_dir = get_base_dir()
    window = TransparentWindow(base_dir)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
