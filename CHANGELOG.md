# Changelog

## v0.20.0

- **Custom screenshot shortcuts**:
  - **Keyboard**: in Settings → SCREENSHOTS, **Record** listens for the next
    combination (modifiers + key) and stores it; **Clear** disables it. Any valid
    combination is registered as a global hotkey on Windows, with a local
    fallback when the system rejects it.
  - **Gamepad**: **Record** captures the buttons you press (for example
    `LB + RB`). Without a custom combination the previous **hold Select for 5
    seconds** gesture is kept.
  - Shortcuts are stored in canonical form (`Ctrl+PgDown`) and old
    `settings.json` values are migrated automatically.
- **Covers from your computer**: the artwork picker gains a **Browse…** button
  that uses a local image (png/jpg/webp/bmp) as the cover, copied into the app
  cache.
- **Modern menus**: the cartridge context menu and the top-right menu now use a
  gradient panel, section labels, store colour dots, a hover accent bar and a
  danger style for *Remove from library*.
- **Cartridge tag**: the DS and PS2 shells show the store (STEAM, EPIC, GOG,
  BATTLE.NET, RIOT) or LOCAL instead of `GC`. Library titles have more room
  below the cover.
- **Big Picture**: the button legend moved to the top bar (between the title and
  the controller status), the local time is highlighted in an accent pill, the
  carousel uses the freed height and clamps cards to the viewport so covers are
  never cropped, and the filter pills size themselves to their text.
- **Dock**: the green dot, *Ready* and the clock are vertically centred.
- **Stats**: hovering the river chart draws a guide line with dots on every
  layer and a tooltip with the date, the period total and the per-game
  breakdown.

## v0.19.1

- **Idle power**: the window no longer repaints while nothing happens. Measured
  on 1920×1080 @ 179 Hz with the library idle: **179.8 → 0 fps**, **17 % → 0.6 %
  CPU** and **12-30 % → 0 % GPU**.
  - The Year in Review background orbs only animate while the presentation is
    open (`running: root.opened`). A running animation inside a closed overlay
    keeps the whole window repainting at the monitor refresh rate, because
    `visible: false` / `opacity: 0` do not stop QML animations.
  - The update badge no longer pulses forever: a short one-shot pulse when it
    appears, then it stays still (same dot, accent border and tooltip).
  - **Big Picture** is created on demand and freed after its fade-out instead of
    living in the tree from startup, which removes the idle carousel repaints.
  - The dock clock only rewrites its text when the minute changes.
- New `tools/idle_probe.py`: measures idle frames and CPU, and fails when the
  app renders more than `--max-fps` (2 fps by default) with no interaction.
- New `tests/test_idle_animations.py`: every `loops: Animation.Infinite` must be
  gated with `running:`, and Big Picture must not exist while closed.

## v0.19.0

- **In-game screenshot overlay**: after a capture, a short white flash and a
  gameplay thumbnail card appear at the bottom-right of the active screen,
  always on top, click-through and without stealing focus from the game.
  Hidden automatically after a couple of seconds.
- **Screenshots linked to sessions**:
  - a new `screenshots.json` index records the game, session, session start and
    timestamp of every capture,
  - the game timeline shows the first two captures to the right of their
    session and a third thumbnail with a **+N** counter when there are more,
  - a new **SCREENSHOTS** section in the game detail gathers every capture of
    the game,
  - thumbnails open a full-screen viewer with prev/next, counter and date.
- Timeline refinements: larger thumbnails, longer session connectors and a
  dedicated vertical scroll area when there are many sessions.
- UI fixes: the Add-game close button is pinned to the panel's top-right
  corner, and the Settings scrollbar no longer overlaps the close button.
- Legacy PNGs without an index entry are recovered by their game-title prefix
  and filename timestamp.
- Screenshots are stored, as before, under
  `%APPDATA%\GameCenter\screenshots`.
- Added ES/FR/DE/IT/PT strings and isolated the screenshot index in tests.
- The overlay is created as a separate top-level tool window so it can stay
  above windowed/borderless games.

## v0.18.0

- **Year in Review**: the **Review year** button in Stats opens a full-screen
  Instagram-Stories-style presentation instead of auto-scrolling the cards.
  - Segmented story progress, auto-advance, pause/resume, close, keyboard
    (←/→/Space/Esc), controller (D-pad/LB/RB/B/A) and tap-left/right navigation.
  - Animated slides for the year summary, every active month, the most played
    game, total sessions, longest streak, best day, busiest month and a closing
    recap.
  - Each slide uses the month/game accent, large covers, staggered reveals,
    animated bar charts and glass cards.
- `Library.yearReview(year)` builds the story payload (`slides`, top game,
  best day, longest streak, busiest month, monthly rhythm) with localized
  labels and covers.
- Added ES/FR/DE/IT/PT strings for the review UI.
- `tools/screenshot.py` can render any review slide with `GC_REVIEW` and
  `GC_REVIEW_SLIDE` for design review.

## v0.17.0

- **Game screenshots**:
  - Configurable keyboard shortcut in **Settings → Screenshots**; the default is
    **Ctrl + Page Down**.
  - With a controller, **hold Select/View for 5 seconds**.
  - Only captures while a GameCenter-launched game is running and saves a PNG
    under `%APPDATA%/GameCenter/screenshots/` with a toast naming the file.
  - On Windows the keyboard shortcut is a real **global hotkey**, so it works
    while the game owns the foreground. If the combination is taken, Settings
    explains the conflict and the in-app shortcut is kept as a fallback.
- **Cartridge insertion now reads like real hardware**: the flying cartridge
  slides **behind the opaque front face of the dock** and **in front of a
  darker insertion plate**, instead of being painted on top of the banner. The
  cartridge already resting in the slot follows the same stacking order.
- **Statistics** now adapt their breakdown to the selected period:
  **Week → days**, **Month → weeks**, **Year → months**. All time keeps the
  monthly breakdown of the selected year.
  - The hero panel also shows the **game with the most hours** in that period,
    with cover, name and hours.
  - Month/week/day cards show the **cover of their most played game**, a
    **numbered top 3** (cover, detailed bold hours and progress bar) and an
    **Other games** row with the remaining time and no bar.
  - Metric leaders use a **diamond + number inside the value container**
    (hours, days played, sessions) instead of loose badges at the top.
  - Every card has one **unique highlight banner**: *Busiest month/week/day*,
    *Longest streak* or *Best day*.
  - Hero chips, metric labels and chart titles were restyled for readability.
- New ES/FR/DE/IT/PT strings for the screenshot settings and month badges.
- `tools/screenshot.py` can now render deterministic Stats and insertion
  previews (`GC_STATS`, configurable `GC_WIDTH`/`GC_HEIGHT`).

## v0.16.5

- **Game detail is now a full-screen modal** with a frosted, opaque translucent
  backdrop (the library behind it is blurred and captured once per opening), so
  there is no centered box or border anymore.
- The **cartridge is pinned to the top-left corner** in a free layer outside
  the scrolling column: it is never clipped by a frame, including the 3D DS
  model.
  - dragging over the cartridge rotates the 3D model (it never moves),
  - the 3D viewport is wider than the card (`modelScale`), so no corner is cut
    at any rotation,
  - double-click still plays, and the compact layout keeps the small cover.
- The **search box is hidden in Stats** and `Ctrl+F` only focuses it from the
  library.
- **Stats is now a dedicated window**: the bottom dock (Ready slot, clock and
  inserted cartridge) and the update banner are hidden there, and the view uses
  the full window height.
- The **Month by Month carousel runs newest first**: the current month (e.g.
  October) leads and January closes the list. Each card keeps its real calendar
  index, so *Open month* still selects the right month.
- **Clicking outside the search box clears its focus**, so the text cursor
  disappears while the click still reaches the item below.
- New ES/FR/DE/IT/PT translation for the rotate hint.

## v0.16.0

- Added a **game profile** to the detail view: a 0–100 score and a status
  (Playing, On Going, Beaten, Completed, Played, Plan to Play, On Hold,
  Not Played, Abandoned), persisted per game id in `profiles.json`.
- Added **manual cross-platform unification** from the game settings:
  - the source field starts empty and the user explicitly picks the entry to
    import (nothing is pre-selected),
  - pick another library entry — including an entry that no longer appears in
    the store but still has GameCenter data — and import its playtime and
    session timeline,
  - the imported timeline keeps an **"Imported"** marker,
  - the source cover is snapshotted under `recap_covers/` for recaps,
  - if the target has no real cover, it adopts the imported one,
  - imported entries stay listed in the target as traceability, and
  - the source can be hidden after merging to avoid duplicate statistics.
- Steam-only native time imported into a Steam target is layered on top of
  Steam's own playtime, and a source that was already unified is protected
  against double imports.
- Detail view now shows a compact status/score strip with an **Edit profile**
  action, and status pills, a score slider and the traceability panel adapt to
  normal and Big Picture layouts.
- Added translations for the new UI in ES/FR/DE/IT/PT.

## v0.15.2

- **Big Picture carousel with four presentation modes**: **Arc**, **Flat**,
  **3D Ring** and **Vertical Wheel**. Switch with **LB/RB**, `C`/`Tab` or the
  mode pill; navigation and filters adapt (up/down or left/right) to each mode.
- Covers are always shown **complete** (`PreserveAspectFit`), never cropped, and
  the focused card **never overlaps the bottom hints**, at any window size.
- New PS5-style presentation: accent glow, depth shadow, glass sheen, ring
  track, floating depth and smooth animated transitions between modes.
- Big Picture has a more compact top bar so the **game carousel is the main
  focus**; the selected cover is larger and the side covers keep a readable
  size.
- The mouse pointer is hidden as soon as the controller is used in Big Picture
  and reappears when the mouse moves.
- **Start** exits Big Picture directly, **B** goes back, and **Y** opens the
  selected game's detail with description and timeline.

## v0.15.0

- Added **Big Picture**, a couch-friendly mode with a large cover and game
  summary, a full-screen layout, a cinematic carousel where the selected game is
  much wider than the rest, All/Recent/Favorites filters and an exit
  confirmation. It is fully usable with an Xbox/XInput controller
  (D-pad/stick, A, B, LB/RB, X, Y, Start), keyboard or mouse. **Start** enters
  and exits Big Picture, **Y** opens the game detail with description and
  timeline, and the **Details** button does the same with a mouse.

## v0.14.0

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
- Removed the small favourite star from library covers; favourites are managed
  from the detail view. The detail scrollbar now leaves a gutter for the
  content, and the close control has a clearer icon and hover state.
- Added a **Statistics** section next to Library and Store with Week / Month /
  Year / All time filters, a year browser, a review banner, the total time and
  secondary metrics (comparison, active days, streak and sessions).
- Added the **Month by Month** river chart (stacked game areas), a horizontal
  carousel of month cards with top games, progress bars, daily activity and
  “Open month”, plus a “Watch” auto-scroll mode.

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
