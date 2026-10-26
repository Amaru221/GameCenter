# Changelog

## Unreleased

- The running game's cartridge now **stays protruding from the dock slot** while
  the game is running. With several games open, the slot shows the most recent
  one; when it closes, the next running game takes its place.
- Launching another game while one is already in the slot keeps the previous
  cartridge visible during the insertion animation and swaps it when the new
  cartridge settles.
- Sessions opened through a store URI now get a **30-second startup grace**
  before the process check can drop them, so the dock chip and the slot
  cartridge no longer vanish while the game is still starting.
- The game detail is now a **responsive summary**: title, store, release year,
  description, size, install state, total playtime, last played, genres and
  developer, with the cartridge preview switching to a compact cover on narrow
  windows.
- Descriptions come from the public Steam Store API (AppID for Steam, exact
  title search for other stores), cached in `metadata.json` and fetched in the
  current interface language.
- Added a **playtime timeline** under the summary with one entry per session
  (date/time and duration), an activity bar strip and the all-time total. New
  sessions are stored in `history.json`, including Steam sessions.
- The detail panel now scrolls when the window is short and leaves the dock out
  of the modal layer.
- The favourite star has been redesigned with a golden glow, a pop and a star
  burst when a game is added, plus a confirmation toast.

## v0.13.0

- **All stores** now always lists Steam, Epic Games, GOG, Battle.net and Riot,
  even when a store has no installed games yet.
- Added a **Most played** sort mode (descending playtime, ties by title).
- Added an **interface language** selector in Settings: English, Spanish,
  French, German, Italian and Portuguese. The choice applies instantly and is
  stored in `settings.json`.
- The Windows installer wizard now ships English, Spanish, French, German,
  Italian, Portuguese, Brazilian Portuguese, Dutch, Polish, Russian and
  Japanese.

## v0.12.0

- The pending-update icon in the navbar is now a proper download glyph with a
  pulsing badge, hover state and tooltip.
- Updates are downloaded and installed from inside GameCenter: live progress,
  SHA-256 verification, silent installer and automatic restart. No more
  redirect to GitHub.
- The update dialog, the update banner and Settings all open the same in-app
  update flow.

## v0.11.0

- The DS cartridge back now has **18 gold contacts**. The two end pads and the
  centre-most pad are slightly longer than the rest.
- The contacts sit in a pocket **two levels below the back surface**, surrounded
  by a three-layer plastic frame that is open at the bottom.
- Plastic dividers at the middle layer separate the contacts all the way down to
  the cartridge edge.
- The back shell is a separate layer and the rounded bottom-left corner keeps a
  continuous arc without a step.

## v0.10.2

- The top-bar menu now exposes **Scan Epic games** and **Scan GOG games**. Both
  stores were already supported and included in the automatic scan; they now
  have dedicated refresh actions too.

## v0.10.1

- The top-bar menu now offers **Scan Riot games**. League of Legends, VALORANT
  and future Riot products are read from their `Riot Game <product>.<patchline>`
  entries and launched through Riot Client with the product and patchline
  arguments. Unknown future products still work and get a readable title.

## v0.10.0

- The top-bar menu now offers **Scan Steam games**, **Scan Battle.net games** and
  **Scan all stores**, so installed games can be refreshed without restarting.
  A scan only replaces the games from that store and keeps the rest.
- Any game can be removed from the library from its right-click menu. Store
  games are hidden (and can be restored with **Restore removed games**); manual
  games are deleted from `manual.json`. This also clears stale entries such as a
  Battle.net folder whose game is no longer installed.

## v0.9.2

- The DS cartridge's bottom-left corner is now one continuous round arc with no
  step, and the other three corners are sharp instead of chamfered.
- Every cartridge can have its own colour: right-click a library card and choose
  **Cartridge color...**. **Use default** restores the global cartridge colour.
- SteamGridDB artwork is now paginated: the picker starts with five options and
  a **Load more** button, and the grid scrolls as more pages are loaded.

## v0.9.1

- The 3D DS cartridge now has the real game-card silhouette: almost square but
  slightly taller, noticeably thinner, with pointed top-left, top-right and
  bottom-right corners and a rounded bottom-left corner. The label covers more
  of the front and the top notch is smaller.

## v0.9.0

- The Nintendo DS cartridge is now a real 3D object (Qt Quick 3D) in the game
  detail view: a solid rounded body, textured label, notch, five gold contacts
  and a screw. Drag it to rotate it freely; the back is fully modelled.
- DS cartridges no longer flip or show a fake side strip in the library. They
  stay flat and front-facing there, and only rotate when a game is open.
- Classic and PS2 cartridges keep their previous look and behaviour.

## v0.8.2

- The Nintendo DS cartridge now shows a solid side profile when turned: the flat
  backing fades out and a thickness strip follows the edge, so a 90° view looks
  like a real cartridge edge instead of a sheet.

## v0.8.1

- The playtime fallback is now a mirror. After an uninstall/reinstall, the next
  scan copies the stored time back into the game's new root folder (store games
  by their stable id, manual games by title). Existing root files are never
  overwritten.

## v0.8.0

- Non-Steam playtime: sessions launched from GameCenter are written to
  `.gamecenter_playtime.json` in the game root (with a fallback under
  `%APPDATA%\GameCenter` when the folder is read-only), then shown in the
  detail view. Steam keeps using its own `localconfig.vdf`.

## v0.7.0

- Add games manually with the **+** button: title, root folder and executable.
  They are stored in `manual.json`, shown as **Local**, filterable and removable.
- Dynamic toolbar heading: the selected category and the number of games.
- Game titles are now bold; the persistent selection ring and the search focus
  border were removed.
- The Nintendo DS cartridge has side walls, a spine and a bottom lip.

## v0.6.1

- More natural insertion: the cartridge approaches the dock, pauses, slides in
  with a small settle and rests slightly protruding before the session chip
  appears.

## v0.6.0

- An update button (↑) next to LIBRARY/STORE opens a modal with the release
  details, even after the banner is dismissed.
- Settings: a **surface colour** for the top navbar, the Ready dock and the
  cartridge shelf, plus a separate **cartridge colour**.
- The Nintendo DS cartridge flips in both directions and tilts vertically while
  dragging.

## v0.5.0

- The app checks GitHub Releases once a day (and on demand from Settings) and
  shows a discreet update banner with Download / Later.
- Settings → Updates: current version, last check, automatic checks and a
  manual “Check now”.
- No automatic download or installation yet; the banner opens the release page.

## v0.4.1

- The Nintendo DS cartridge now flips by **dragging it with the mouse**, not
  with a button.
- The DS metallic contacts moved to the **bottom edge** of the back.
- The DS and PS2 cartridges are labelled **GC**.
- New insertion animation: Play sends the cartridge into the dock slot, with a
  glow and an “Inserting…” state.

## v0.4.0

- Settings panel with 24 accent colours and three cartridge styles: classic,
  Nintendo DS (3D flip with metallic contacts) and PS2.
- Per-game cover picker using SteamGridDB (up to 5 portrait options or the
  default). The API key is stored in the system credential store.
- Note: Heroic Games Launcher and Lutris (Linux) will be added in a later
  version.

## v0.3.0

- Steam, Epic, GOG, Battle.net and Riot as local sources.
- 3D cartridge shelf, detail view, favorites, Steam playtime and session dock.
- Windows installer (per-user) and automatic releases.
- Security policy and no API keys stored in the repository.

### Coming later

- **Heroic Games Launcher** and **Lutris** support (Linux) will be added in a
  future version. The current release focuses on Windows and the stores that
  expose local manifests or registry entries.
- More cartridge styles and per-game artwork selection.

## v0.2.0

- QML interface with 3D cartridges, procedural covers and Steam cover art.

## v0.1.0

- First Steam-only MVP: library scan, search, filters and launching.
