# WORKFLOW STATE — Big Picture con mando

## Descripción funcional

- Modo **Big Picture** a pantalla completa (sin barra de título ni barra de
  Windows), con portada grande, información del juego, filtros y un carrusel
  cinematográfico.
- El juego seleccionado ocupa mucho más ancho y alto que los laterales; el
  resto queda en segundo plano con menor opacidad.
- Entrada desde el menú, `Ctrl+B` o **Start** del mando.
- Salida:
  - **Start** vuelve a pulsarse y sale directamente del modo,
  - botón **Exit** de la esquina para ratón (con confirmación),
  - **B** es “volver”: cierra la ficha del juego, no sale del modo.
- **Y/Triángulo** abre la ficha del juego seleccionado, con descripción,
  metadata y timeline. También se abre con el botón **Details** del ratón.
- Mando Xbox/XInput:
  - D-pad/stick: navegar.
  - A: jugar.
  - B: volver / cerrar ficha.
  - Y: abrir/cerrar ficha.
  - LB/RB: filtros.
  - X: favorito.
  - Start: salir.
- Teclado: flechas, Enter, Esc, `I`, `[`/`]`, `F`. Ratón: tarjetas, flechas,
  filtros, Play, Details, favorito, Exit y confirmación.

## Decisiones de arquitectura

- `GamepadManager` XInput añade la señal `details` mapeada a **Y**.
- `Main.qml` enlaza `visibility` a `Window.FullScreen` al abrir Big Picture y
  vuelve a `Window.Windowed` al cerrar. `requestActivate()` trae la ventana al
  frente al entrar.
- `BigPicture.qml` usa `uiScale` y alturas proporcionales al alto de pantalla
  para adaptarse de 620 px a pantallas grandes.
- Carrusel cinematográfico: el delegado actual usa `cinematicCardWidth` y toda
  la altura; los laterales usan `smallCardWidth`/`smallCardHeight` y menor
  opacidad, con animaciones de tamaño.
- La ficha reutiliza `GameDetail.qml` dentro de Big Picture:
  - `Library.gameDetailById`, `loadDetailsById`, `openFolderById`,
    `copyAppIdById` evitan depender de filas filtradas.
  - `GameDetail` gana `showArt` (oculta “Choose art” en Big Picture) y
    `scrollBy()` para el scroll con stick/D-pad.
  - La descripción carga con `Library.loadDetailsById`.
- La B ya no abre la salida; Start cierra el modo directamente. El botón Exit
  conserva confirmación.

## Contrato interno

| Elemento | Tipo | Descripción |
| --- | --- | --- |
| `Gamepad.connected` | bool | Mando XInput activo. |
| `Gamepad.navigate/accept/back/menu` | signals | D-pad/A/B/Start. |
| `Gamepad.pageLeft/pageRight/favorite/details` | signals | LB/RB/X/Y. |
| `Library.bigPictureGames` | `QVariantList` | Juegos para Big Picture. |
| `Library.launchById(gameId)` | slot → `str` | Lanza y devuelve sesión. |
| `Library.toggleFavoriteById(gameId)` | slot → `bool` | Alterna favorito. |
| `Library.gameDetailById(gameId)` | slot → `QVariantMap` | Ficha completa por id. |
| `Library.loadDetailsById(gameId)` | slot | Carga descripción por id. |
| `Library.openFolderById/copyAppIdById` | slots | Acciones por id. |
| `BigPicture.detailOpen` | bool | Ficha abierta. |
| `BigPicture.openDetail()` | función | Abre ficha del seleccionado. |
| `GameDetail.scrollBy(delta)` | función | Scroll para mando/teclado. |

## Checklist

### Backend
- [x] XInput con conexión, flancos, repetición y señal `details` (Y).
- [x] `Gamepad` expuesto al contexto QML y desactivable.
- [x] API de biblioteca por id + ficha completa.
- [x] Carga de descripción por id y acciones de carpeta/AppID.
- [x] Tests de mapeo y API.

### Frontend
- [x] Big Picture fullscreen y retorno a ventana.
- [x] Layout responsive con `uiScale` y alturas proporcionales.
- [x] Carrusel cinematográfico con seleccionado mucho más amplio.
- [x] Start sale; B vuelve; Y abre ficha; botón Details para ratón.
- [x] Ficha con descripción y timeline reutilizando `GameDetail`.
- [x] Scroll de la ficha con stick/D-pad y teclado.
- [x] Pistas de mando/teclado actualizadas.
- [x] Entrada desde menú, `Ctrl+B` y Start.

### Verificación
- [x] `python -m pytest -q` → **124 passed**.
- [x] Capturas de Big Picture fullscreen, carrusel cinematográfico y ficha.
- [x] Prueba QML de apertura de ficha y navegación.
- [x] README/CHANGELOG actualizados.

## Notas

- El soporte nativo de mando es **XInput (Windows)**.
- El modo se dibuja a pantalla completa real mediante `Window.FullScreen`;
  al salir vuelve a `Window.Windowed`.
- La ficha del juego dentro de Big Picture oculta el botón de carátula para
  centrarse en descripción y timeline.
