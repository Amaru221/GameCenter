# WORKFLOW STATE — Big Picture con mando

## Versión 0.15.2

- Carrusel de Big Picture con **cuatro modos**: **Arco**, **Plano**, **Anillo
  3D** y **Rueda vertical**, conmutables con **LB/RB**, `C`/`Tab` o la píldora
  de modo; la navegación y los filtros se adaptan a cada modo.
- Las carátulas se muestran **completas** (`PreserveAspectFit`) y la tarjeta
  seleccionada **nunca se solapa con la barra inferior**, en cualquier tamaño.
- Efecto visual moderno tipo PS5: halo de acento, sombra en profundidad, brillo
  de cristal, pista del anillo y transiciones animadas entre modos.
- Barra superior reducida (altura, márgenes, tipografía y botón Exit) para que
  el carrusel sea el protagonista; hero contenido y carrusel más alto.
- El puntero del ratón se oculta al recibir cualquier entrada de mando
  (`GamepadManager._hide_cursor`) y reaparece al detectar movimiento del ratón
  (`_poll_cursor`), sin bloquear los clics.
- `Gamepad.showCursor()` se llama al cerrar Big Picture y al salir de la app.
- Tests: **125 passed**.

## Descripción funcional

- Modo **Big Picture** a pantalla completa (sin barra de título ni barra de
  Windows), con portada grande, información del juego, filtros y un carrusel
  cinematográfico con cuatro modos: **Arco**, **Plano**, **Anillo 3D** y
  **Rueda vertical**.
- El juego seleccionado ocupa mucho más ancho y alto que los laterales; el
  resto queda en segundo plano con menor opacidad y profundidad.
- Las carátulas se ven completas, sin recortes, y la tarjeta seleccionada queda
  siempre por encima de la barra de pistas.
- Entrada desde el menú, `Ctrl+B` o **Start** del mando.
- Salida:
  - **Start** vuelve a pulsarse y sale directamente del modo,
  - botón **Exit** de la esquina para ratón (con confirmación),
  - **B** es “volver”: cierra la ficha del juego, no sale del modo.
- **Y/Triángulo** abre la ficha del juego seleccionado, con descripción,
  metadata y timeline. También se abre con el botón **Details** del ratón.
- Mando Xbox/XInput:
  - D-pad/stick: navegar (arriba/abajo o izquierda/derecha según el modo).
  - A: jugar.
  - B: volver / cerrar ficha.
  - Y: abrir/cerrar ficha.
  - LB/RB: cambiar el modo del carrusel.
  - X: favorito.
  - Start: salir.
- Teclado: flechas, Enter, Esc, `I`, `C`/`Tab` (modo), `[`/`]` (filtros), `F`.
  Ratón: tarjetas, flechas, píldora de modo, filtros, Play, Details, favorito,
  Exit y confirmación.

## Decisiones de arquitectura

- `GamepadManager` XInput añade la señal `details` mapeada a **Y**.
- `Main.qml` enlaza `visibility` a `Window.FullScreen` al abrir Big Picture y
  vuelve a `Window.Windowed` al cerrar. `requestActivate()` trae la ventana al
  frente al entrar.
- `BigPicture.qml` usa `uiScale` y alturas proporcionales al alto de pantalla
  para adaptarse de 620 px a pantallas grandes. `heroHeight` y
  `carouselHeight` se recalculan según el modo para reservar espacio a las
  tarjetas superiores/inferiores de la rueda vertical y evitar solapes.
- El carrusel vive en `BigPictureCarousel.qml`:
  - `mode` admite `arc`, `flat`, `ring` y `wheel`.
  - posiciona una ventana de tarjetas (`windowStart`) alrededor de la
    seleccionada con transformaciones y animaciones.
  - `arc` aplica caída y giro Z; `flat` mantiene una fila; `ring` reparte las
    tarjetas en profundidad con giro Y y una pista elíptica; `wheel` apila las
    tarjetas arriba/abajo con giro X.
  - las carátulas usan `Image.PreserveAspectFit` y cada tarjeta tiene fondo
    opaco, halo, sombra y brillo de cristal.
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
| `Gamepad.pageLeft/pageRight/favorite/details` | signals | LB/RB (modo), X, Y. |
| `Library.bigPictureGames` | `QVariantList` | Juegos para Big Picture. |
| `Library.launchById(gameId)` | slot → `str` | Lanza y devuelve sesión. |
| `Library.toggleFavoriteById(gameId)` | slot → `bool` | Alterna favorito. |
| `Library.gameDetailById(gameId)` | slot → `QVariantMap` | Ficha completa por id. |
| `Library.loadDetailsById(gameId)` | slot | Carga descripción por id. |
| `Library.openFolderById/copyAppIdById` | slots | Acciones por id. |
| `BigPicture.detailOpen` | bool | Ficha abierta. |
| `BigPicture.carouselMode` | `string` | `arc`, `flat`, `ring` o `wheel`. |
| `BigPicture.cycleMode(delta)` | función | Cambia el modo del carrusel. |
| `BigPicture.openDetail()` | función | Abre ficha del seleccionado. |
| `BigPictureCarousel.mode` | `string` | Modo de presentación activo. |
| `BigPictureCarousel.selectedIndex` | `int` | Tarjeta enfocada. |
| `BigPictureCarousel.selected/activated` | signals | Clic y doble clic. |
| `GameDetail.scrollBy(delta)` | función | Scroll para mando/teclado. |

## Checklist

### Backend
- [x] XInput con conexión, flancos, repetición y señal `details` (Y).
- [x] `Gamepad` expuesto al contexto QML y desactivable.
- [x] Ocultación/restauración del cursor con la entrada de mando.
- [x] API de biblioteca por id + ficha completa.
- [x] Carga de descripción por id y acciones de carpeta/AppID.
- [x] Tests de mapeo y API.

### Frontend
- [x] Big Picture fullscreen y retorno a ventana.
- [x] Layout responsive con `uiScale` y alturas adaptadas al modo.
- [x] Carrusel con modos Arco, Plano, Anillo 3D y Rueda vertical.
- [x] Carátulas completas y tarjeta enfocada siempre sobre la barra de pistas.
- [x] Navegación y pistas adaptadas a cada modo; LB/RB y `C`/`Tab` cambian modo.
- [x] Start sale; B vuelve; Y abre ficha; botón Details para ratón.
- [x] Ficha con descripción y timeline reutilizando `GameDetail`.
- [x] Scroll de la ficha con stick/D-pad y teclado.
- [x] Pistas de mando/teclado actualizadas.
- [x] Entrada desde menú, `Ctrl+B` y Start.

### Verificación
- [x] `python -m pytest -q` → **125 passed**.
- [x] Capturas de los cuatro modos en 800×800, 1280×720 y 1920×1080.
- [x] Prueba QML de apertura de ficha, navegación y cambio de modo.
- [x] README/CHANGELOG actualizados.

## Notas

- El soporte nativo de mando es **XInput (Windows)**.
- El modo se dibuja a pantalla completa real mediante `Window.FullScreen`;
  al salir vuelve a `Window.Windowed`.
- La ficha del juego dentro de Big Picture oculta el botón de carátula para
  centrarse en descripción y timeline.
