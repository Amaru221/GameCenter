# Security policy

## Secrets

GameCenter **does not use API keys, tokens, passwords or accounts**. There is
nothing secret to configure, and the repository contains no credentials.

The application reads local game libraries (Steam, Epic, GOG, Battle.net and
Riot) from files and the Windows registry. It never writes to those locations.

## Data on your machine

| Data | Location | Contents |
|---|---|---|
| Favorites | `%APPDATA%\GameCenter\settings.json` (Linux: `~/.config/GameCenter/settings.json`) | game IDs only |
| Cover cache | `~/.cache/gamecenter/art` | JPEG capsules downloaded from Steam's public CDN |

No library contents, paths, account names or play history are uploaded.

## Network

The only request is for cover art: the numeric **AppID** is sent to
`shared.akamai.steamstatic.com`. Set `GC_NO_ART=1` to disable it and use the
locally generated covers.

## Reporting a vulnerability

Please use GitHub's **Security → Report a vulnerability** (private advisory) on
this repository. Do not open a public issue for a security problem.

## Contributing

Never commit `.env` files, private keys, certificates or local settings.
`.gitignore` already excludes the usual names; check `git status` before
pushing.
