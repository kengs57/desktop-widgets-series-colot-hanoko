import os
import random
from pathlib import Path
from PyQt6.QtCore import Qt, QPoint, QTimer, QSize
from PyQt6.QtGui import QPixmap, QIcon, QAction, QCursor
from PyQt6.QtWidgets import QWidget, QMenu, QSystemTrayIcon, QApplication

from src.sound_player import SoundPlayer

class ConyangWidget(QWidget):
    """
    바탕화면 데스크톱 코냥이 위젯 (Desktop Cat Widget)
    """
    def __init__(self, base_dir: Path):
        super().__init__()
        self.base_dir = base_dir
        self.assets_dir = base_dir / "assets"
        self.sounds_dir = base_dir / "sounds"
        
        self.sound_player = SoundPlayer(self.sounds_dir)
        
        # 상태 변수
        self.drag_position = QPoint()
        self.is_dragging = False
        self.current_state = "idle"  # idle, happy, walk, sleep
        
        # 프레임 / 타이머 설정
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_behavior)
        self.timer.start(3000)  # 3초마다 상태 변화 체크
        
        self.init_ui()

    def init_ui(self):
        """UI 초기화"""
        # 창 프레임 제거 및 최상단 고정, 투명 배경 설정
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 이미지 로드
        self.load_images()
        self.update_image()
        
        # 시스템 트레이 아이콘 설정
        self.setup_tray_icon()
        
        # 커서 모양 설정
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 창 크기 조정 및 위치 초기화
        self.resize(128, 128)
        self.show()

    def load_images(self):
        """assets 폴더에서 코냥이 이미지 로드"""
        self.images = {}
        
        idle_path = self.assets_dir / "정수리먹롯.png"
        happy_path = self.assets_dir / "cat_happy.png"
        
        if idle_path.exists():
            self.images["idle"] = QPixmap(str(idle_path)).scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        if happy_path.exists():
            self.images["happy"] = QPixmap(str(happy_path)).scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

    def update_image(self):
        """현재 상태에 맞춰 이미지 갱신"""
        pixmap = self.images.get(self.current_state) or next(iter(self.images.values()), None)
        if pixmap:
            self.setFixedSize(pixmap.size())
            self.update()

    def update_behavior(self):
        """코냥이 무작위 행동 업데이트"""
        if self.is_dragging:
            return
        
        # 랜덤하게 행복해지거나 기본 상태 전환
        behaviors = ["idle", "idle", "happy"]
        new_state = random.choice(behaviors)
        
        if new_state != self.current_state:
            self.current_state = new_state
            self.update_image()
            if self.current_state == "happy":
                self.sound_player.play_purr()

    def setup_tray_icon(self):
        """트레이 아이콘 및 메뉴 구성"""
        self.tray_icon = QSystemTrayIcon(self)
        idle_path = self.assets_dir / "정수리먹롯.png"
        if idle_path.exists():
            self.tray_icon.setIcon(QIcon(str(idle_path)))
        
        tray_menu = QMenu()
        
        meow_action = QAction("🐱 야옹~ 하기", self)
        meow_action.triggered.connect(self.say_meow)
        tray_menu.addAction(meow_action)
        
        tray_menu.addSeparator()
        
        exit_action = QAction("❌ 종료", self)
        exit_action.triggered.connect(QApplication.instance().quit)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def say_meow(self):
        """야옹 소리내며 반응하기"""
        self.current_state = "happy"
        self.update_image()
        self.sound_player.play_meow()
        
        # 2초 후 다시 기본 상태로 복귀
        QTimer.singleShot(2000, self.reset_state)

    def reset_state(self):
        self.current_state = "idle"
        self.update_image()

    # --- Mouse Interaction Events ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.sound_player.play_meow()
            self.current_state = "happy"
            self.update_image()
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            self.show_context_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        if self.is_dragging and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            QTimer.singleShot(1500, self.reset_state)
            event.accept()

    def show_context_menu(self, pos):
        """우클릭 컨텍스트 메뉴"""
        menu = QMenu(self)
        
        pet_action = QAction("✨ 코냥이 쓰다듬기", self)
        pet_action.triggered.connect(self.say_meow)
        menu.addAction(pet_action)
        
        menu.addSeparator()
        
        quit_action = QAction("🚪 코냥이 재우기 (종료)", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(quit_action)
        
        menu.exec(pos)

    def paintEvent(self, event):
        """투명 배경 위에 코냥이 그리기"""
        from PyQt6.QtGui import QPainter
        pixmap = self.images.get(self.current_state) or next(iter(self.images.values()), None)
        if pixmap:
            painter = QPainter(self)
            painter.drawPixmap(0, 0, pixmap)
