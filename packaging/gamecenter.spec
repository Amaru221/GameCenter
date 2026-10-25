# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec: a one-folder Windows build."""

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

ROOT = Path(SPECPATH).parent

DATAS = [
    (str(ROOT / "gamecenter" / "ui" / "qml"), "gamecenter/ui/qml"),
    (str(ROOT / "gamecenter" / "ui" / "fonts"), "gamecenter/ui/fonts"),
    (str(ROOT / "README.md"), "."),
    (str(ROOT / "LICENSE"), "."),
    (str(ROOT / "THIRD_PARTY_NOTICES.md"), "."),
    (str(ROOT / "SECURITY.md"), "."),
]

a = Analysis(
    [str(ROOT / "packaging" / "gamecenter_main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=DATAS,
    hiddenimports=collect_submodules("keyring.backends") + ["PySide6.QtQuick3D"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="GameCenter",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / "packaging" / "gamecenter.ico"),
    version=str(ROOT / "packaging" / "version_info.txt"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="GameCenter",
)
