import os
import random
import winsound
from pathlib import Path

class SoundPlayer:
    """
    사운드 재생을 담당하는 클래스 (Sound Player Manager)
    """
    def __init__(self, sounds_dir: Path):
        self.sounds_dir = sounds_dir

    def _get_random_wav(self) -> Path:
        """sounds 폴더 내 존재하는 wav 파일 중 1개 무작위 선택"""
        wav_files = list(self.sounds_dir.glob("*.wav"))
        if wav_files:
            return random.choice(wav_files)
        return None

    def play_meow(self):
        """효과음 재생 (WAV 파일 재생)"""
        meow_path = self.sounds_dir / "meow.wav"
        if not meow_path.exists():
            meow_path = self._get_random_wav()
        if meow_path:
            self._play_sound(meow_path)

    def play_purr(self):
        """효과음 재생 (WAV 파일 재생)"""
        purr_path = self.sounds_dir / "purr.wav"
        if not purr_path.exists():
            purr_path = self._get_random_wav()
        if purr_path:
            self._play_sound(purr_path)

    def _play_sound(self, sound_path: Path):
        """WAV 파일 재생"""
        if sound_path.exists():
            try:
                # Windows 기본 winsound 모듈을 사용하여 외부 라이브러리 없이 비동기 재생
                winsound.PlaySound(str(sound_path), winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception as e:
                print(f"[SoundPlayer Error] 사운드 재생 실패: {e}")
        else:
            print(f"[SoundPlayer Warning] 사운드 파일이 존재하지 않습니다: {sound_path}")
