"""Small, read-only helpers for the Windows registry.

They do nothing on other platforms, so importing a source is always safe.
"""

from __future__ import annotations

import sys
from typing import Iterator


def _winreg():
    if sys.platform != "win32":
        return None
    import winreg

    return winreg


def uninstall_roots():
    winreg = _winreg()
    if winreg is None:
        return ()
    return (
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            winreg.KEY_WOW64_64KEY,
        ),
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
            0,
        ),
        (
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Uninstall",
            0,
        ),
    )


def read_values(key) -> dict:
    winreg = _winreg()
    values: dict = {}
    index = 0
    while True:
        try:
            name, value, _ = winreg.EnumValue(key, index)
        except OSError:
            break
        values[name] = value
        index += 1
    return values


def iter_subkeys(hive, path: str, view: int = 0) -> Iterator[tuple[str, dict]]:
    winreg = _winreg()
    if winreg is None:
        return
    try:
        root = winreg.OpenKey(hive, path, 0, winreg.KEY_READ | view)
    except OSError:
        return
    with root:
        index = 0
        while True:
            try:
                name = winreg.EnumKey(root, index)
            except OSError:
                break
            index += 1
            try:
                with winreg.OpenKey(root, name, 0, winreg.KEY_READ | view) as key:
                    yield name, read_values(key)
            except OSError:
                continue


def iter_uninstall() -> Iterator[tuple[str, dict]]:
    for hive, path, view in uninstall_roots():
        yield from iter_subkeys(hive, path, view)
