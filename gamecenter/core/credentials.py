"""API keys in the operating system's credential store, never in the repo.

Windows: Credential Manager. Linux/macOS: whatever backend keyring finds
(Secret Service, KWallet, Keychain). If no backend is available the calls fail
softly and the UI says so.
"""

from __future__ import annotations

SERVICE = "GameCenter"
STEAMGRIDDB = "steamgriddb"


def get_key(name: str = STEAMGRIDDB) -> str:
    try:
        import keyring

        return keyring.get_password(SERVICE, name) or ""
    except Exception:  # noqa: BLE001 - a missing/locked backend must not crash
        return ""


def set_key(value: str, name: str = STEAMGRIDDB) -> bool:
    try:
        import keyring

        keyring.set_password(SERVICE, name, value)
        return True
    except Exception:  # noqa: BLE001
        return False


def clear_key(name: str = STEAMGRIDDB) -> None:
    try:
        import keyring

        keyring.delete_password(SERVICE, name)
    except Exception:  # noqa: BLE001
        pass
