#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
데스크톱 위젯 자동 빌드 및 가상환경 구축 스크립트.
가상환경(.venv)을 생성하고 requirements.txt 패키지를 자동으로 설치하며,
PyInstaller를 이용해 '코롯_데스크톱위젯.exe' 및 '하노코_데스크톱위젯.exe'를 생성합니다.
"""

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path

# 프로젝트 루트 경로 정의
PROJECT_ROOT = Path(__file__).resolve().parent
VENV_DIR = PROJECT_ROOT / ".venv"
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"


def get_venv_python() -> Path:
    """가상환경 내부의 Python 실행 파일 경로를 반환합니다."""
    if platform.system() == "Windows":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def get_venv_pip() -> Path:
    """가상환경 내부의 pip 실행 파일 경로를 반환합니다."""
    if platform.system() == "Windows":
        return VENV_DIR / "Scripts" / "pip.exe"
    return VENV_DIR / "bin" / "pip"


def get_venv_pyinstaller() -> Path:
    """가상환경 내부의 PyInstaller 실행 파일 경로를 반환합니다."""
    if platform.system() == "Windows":
        return VENV_DIR / "Scripts" / "pyinstaller.exe"
    return VENV_DIR / "bin" / "pyinstaller"


def setup_virtualenv() -> bool:
    """
    파이썬 가상환경(.venv)이 존재하지 않으면 생성하고,
    requirements.txt에 명시된 모든 패키지를 설치합니다.
    """
    print("=" * 60)
    print("[1/2] 파이썬 가상환경 구축 및 의존성 패키지 설치 진행 중...")
    print("=" * 60)

    # 1. 가상환경 생성
    if not VENV_DIR.exists():
        print(f"가상환경 생성 중: {VENV_DIR}")
        try:
            subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
            print("[OK] 가상환경 생성 완료.")
        except subprocess.CalledProcessError as e:
            print(f"[Error] 가상환경 생성 실패: {e}")
            return False
    else:
        print(f"[Info] 기존 가상환경 발견: {VENV_DIR}")

    python_bin = get_venv_python()
    pip_bin = get_venv_pip()

    if not python_bin.exists() or not pip_bin.exists():
        print("[Error] 가상환경 실행 파일을 찾을 수 없습니다.")
        return False

    # 2. pip 업그레이드
    print("[Pip] pip 최신 버전으로 업그레이드 중...")
    subprocess.run([str(python_bin), "-m", "pip", "install", "--upgrade", "pip"], check=False)

    # 3. requirements.txt 설치
    if REQUIREMENTS_FILE.exists():
        print(f"[Pip] 패키지 자동 설치 시작 ({REQUIREMENTS_FILE})...")
        try:
            subprocess.run([str(pip_bin), "install", "-r", str(REQUIREMENTS_FILE)], check=True)
            print("[OK] 패키지 설치 성공적으로 완료!")
        except subprocess.CalledProcessError as e:
            print(f"[Error] 패키지 설치 중 오류 발생: {e}")
            return False
    else:
        print(f"[Warning] {REQUIREMENTS_FILE} 파일이 존재하지 않습니다.")

    return True


def build_executable(target: str = "all") -> bool:
    """
    PyInstaller를 사용하여 standalone executable 실행 파일을 생성합니다.
    target: "1" (코롯), "2" (하노코), "all" (둘 다)
    """
    print("\n" + "=" * 60)
    print(f"[2/2] PyInstaller를 통한 단일 실행 파일(.exe) 패키징 빌드 (Target: {target})...")
    print("=" * 60)

    pyinstaller_bin = get_venv_pyinstaller()
    if not pyinstaller_bin.exists():
        print("[Notice] 가상환경에 PyInstaller가 설치되어 있지 않습니다. 설치를 시도합니다.")
        pip_bin = get_venv_pip()
        subprocess.run([str(pip_bin), "install", "PyInstaller"], check=True)

    sep = ";" if platform.system() == "Windows" else ":"
    assets_dir = PROJECT_ROOT / "assets"
    sounds_dir = PROJECT_ROOT / "sounds"

    targets_to_build = []
    if target in ("1", "korot"):
        targets_to_build.append(("코롯_데스크톱위젯", PROJECT_ROOT / "src" / "main.py"))
    elif target in ("2", "hanoko"):
        targets_to_build.append(("하노코_데스크톱위젯", PROJECT_ROOT / "src" / "main_2.py"))
    else:
        targets_to_build.append(("코롯_데스크톱위젯", PROJECT_ROOT / "src" / "main.py"))
        targets_to_build.append(("하노코_데스크톱위젯", PROJECT_ROOT / "src" / "main_2.py"))

    all_success = True
    for name, script_path in targets_to_build:
        if not script_path.exists():
            print(f"[Error] 대상 스크립트를 찾을 수 없습니다: {script_path}")
            all_success = False
            continue

        cmd = [
            str(pyinstaller_bin),
            "--noconsole",
            "--onefile",
            f"--name={name}",
            "--clean",
            "--collect-all=PyQt6",
        ]

        if assets_dir.exists():
            cmd.append(f"--add-data={assets_dir}{sep}assets")
        if sounds_dir.exists():
            cmd.append(f"--add-data={sounds_dir}{sep}sounds")

        cmd.append(str(script_path))

        print(f"\n[Build Command] {' '.join(cmd)}")

        try:
            subprocess.run(cmd, check=True, cwd=str(PROJECT_ROOT))
            print(f"[SUCCESS] '{name}.exe' 빌드 성공!")
            print(f"[Output] 결과물 저장 경로: {PROJECT_ROOT / 'dist' / f'{name}.exe'}")
        except subprocess.CalledProcessError as e:
            print(f"[Error] '{name}' 빌드 실패: {e}")
            all_success = False

    return all_success


def main():
    parser = argparse.ArgumentParser(
        description="데스크톱 위젯 프로젝트 자동 구축 및 PyInstaller 빌드 도구"
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="가상환경 생성 및 requirements.txt 의존성 설치만 수행합니다.",
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="가상환경 설치 후 PyInstaller 실행 파일(.exe) 빌드까지 수행합니다.",
    )
    parser.add_argument(
        "--target",
        type=str,
        default="all",
        choices=["1", "2", "korot", "hanoko", "all"],
        help="빌드 대상 선택: 1/korot (코롯), 2/hanoko (하노코), all (둘 다 기본값)",
    )

    args = parser.parse_args()

    if not args.setup and not args.build:
        print("[Info] 인자가 지정되지 않았습니다. 기본 환경 구축을 수행합니다.")
        print("       (실행 파일까지 생성하려면 '--build' 옵션을 사용하세요.)\n")

    # 1. 환경 구축
    success = setup_virtualenv()
    if not success:
        print("[Error] 환경 구축 과정에서 오류가 발생했습니다.")
        sys.exit(1)

    # 2. 빌드 실행 (옵션 지정 시)
    if args.build:
        build_success = build_executable(target=args.target)
        if not build_success:
            sys.exit(1)

    print("\n[OK] 모든 작업이 완료되었습니다!")


if __name__ == "__main__":
    main()
