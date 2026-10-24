# Third-party notices

GameCenter's own code is under the MIT license (see `LICENSE`). The following
parts keep their own licenses.

## Fonts (`gamecenter/ui/fonts`)

| Font | Copyright | License |
|---|---|---|
| Sora | 2019 The Sora Project Authors (github.com/sora-xor/sora-font) | SIL Open Font License 1.1 |
| Chakra Petch | 2018 Chakra Petch (github.com/cadsondemak/Chakra-Petch) | SIL Open Font License 1.1 |

Both license texts are next to the font files as `OFL-Sora.txt` and
`OFL-ChakraPetch.txt`.

## Cover art

Portrait capsules are fetched at runtime from Steam's public CDN
(`shared.akamai.steamstatic.com`) and cached on the user's machine. They are not
included in this repository and are not redistributed. The artwork belongs to
the respective game publishers and is shown only to identify the game.

When no art is available (offline, `GC_NO_ART=1`, or the game has no capsule),
the cover is generated locally with QPainter.

## Libraries used by the builds

| Library | License |
|---|---|
| Qt 6 and Qt for Python (PySide6, Shiboken6) | GNU LGPL v3.0 |
| Python | Python Software Foundation License |

Qt is linked dynamically, so its libraries can be replaced with a compatible
version.

## Trademarks

Steam is a trademark of Valve Corporation. GameCenter is an independent project
and is not affiliated with, endorsed by, or sponsored by Valve or any game
publisher. Store names appear only to indicate where a game comes from.
