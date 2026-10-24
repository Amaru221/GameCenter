# Changelog

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
