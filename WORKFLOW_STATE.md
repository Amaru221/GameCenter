# WORKFLOW STATE — Big Picture con mando

## Feature 0.17.0 — Modal de juego a pantalla completa

### Descripción funcional

- La ficha del juego deja de ser una caja centrada: pasa a ocupar **toda la
  ventana** con un fondo **blur opaco translúcido** (cristal esmerilado) sobre
  la escena que queda detrás.
- La **carátula/cartucho 3D** queda **fija en la esquina superior izquierda**,
  fuera del área de scroll. El visor 3D es más ancho que el modelo para que,
  al rotarlo, **ninguna esquina se recorte**:
  - arrastrar sobre el cartucho **rota** el modelo (sin desplazarlo),
  - doble clic sigue lanzando el juego.
- El **buscador se oculta en Estadísticas** (y `Ctrl+F` solo funciona en la
  biblioteca). Al entrar en Stats tampoco se muestra el **dock inferior**
  (ranura Ready, reloj y cartucho insertado) ni el aviso de actualización: es
  una ventana dedicada solo a estadísticas.
- El **carrusel de meses va del más reciente al más antiguo**: primero el mes
  actual y al final enero.
- Si el buscador tiene el foco y se pulsa en cualquier otro sitio de la
  ventana, el campo **pierde el foco** y desaparece el cursor de escritura,
  sin bloquear el clic que se estaba haciendo.

### Decisión de arquitectura

- `GameDetail.qml` recibe `backdropItem` (la escena a difuminar). Se captura
  una sola vez por apertura con `ShaderEffectSource` (`live: false`) y se
  procesa con `MultiEffect` de `QtQuick.Effects`; es barato y no requiere
  refactorizar el render.
- `Main.qml` agrupa la escena de biblioteca en un `Item` (`libraryScene`) para
  poder pasarla como `backdropItem`. La ficha y el toast quedan fuera.
- En Big Picture no se captura la escena (la ficha es hija del propio root):
  `backdropItem` queda a `null` y la ficha usa `image://bg/1` difuminado como
  respaldo. `GameDetail` funciona igual en ambos contextos.
- El cartucho vive en `cartridgeHost`, fijado arriba a la izquierda
  (`cartridgeMarginX/Y`), fuera del `Flickable` que recorta el contenido.
- El visor 3D es mayor que la tarjeta (`cartridgeWidth/Height`) y el modelo se
  reduce dentro con `DsCartridge3D.modelScale`, dejando margen en los cuatro
  lados para rotaciones de hasta ±50° de inclinación y giro completo.
- La ficha compacta (<940 px) mantiene la portada pequeña dentro del contenido
  y oculta el cartucho fijo para no tapar la lectura.
- El buscador se oculta con `visible` en `TopBar.qml`; el foco se limpia con una
  capa `MouseArea` de guardia en `Main.qml` que deja pasar el pulso
  (`mouse.accepted = false` + `propagateComposedEvents`).
- El dock, la ranura y el `UpdateBanner` viven en `libraryDock` (dentro de
  `libraryScene`) y solo son visibles en la biblioteca. `StatsView` usa todo el
  alto disponible.
- `StatsView.months` invierte `statsData.months` (que sigue en orden
  cronológico en el backend) y `carouselIndexForMonth()` traduce el mes
  calendario a su posición invertida; el `MonthCard` conserva el
  `monthIndex` original para abrir el mes correcto.

### Contrato de API (QML)

| Elemento | Tipo | Descripción |
| --- | --- | --- |
| `GameDetail.backdropItem` | `Item` | Escena a desenfocar; `null` usa `image://bg/1`. |
| `GameDetail.compact` | `bool` (readonly) | `width < 940`; layout de una columna. |
| `GameDetail.cartridgeMarginX/Y` | `real` (readonly) | Posición fija del cartucho (24, 72). |
| `GameDetail.cartridgeWidth/Height` | `real` (readonly) | Visor 3D ancho (hasta 400×480). |
| `DsCartridge3D.modelScale` | `real` | Escala del modelo dentro del visor (0.82 en la ficha). |
| `GameDetail.scrollBy(delta)` | función | Sin cambios (mando/teclado en Big Picture). |
| `TopBar.searchFocused` | `bool` (readonly) | El `TextField` tiene el foco activo. |
| `TopBar.clearSearchFocus()` | función | Quita el foco del buscador. |
| `StatsView.months` | `list` (readonly) | Meses en orden inverso (actual → enero). |
| `StatsView.carouselIndexForMonth(monthIndex)` | función | Índice del mes en el carrusel invertido. |
| `DsCartridge3D.interactive` | `bool` | Desactiva su `MouseArea` para que la ficha gestione la rotación. |
| `Cartridge.interactive` | `bool` | El 2D sigue interactivo (hover y doble clic) pero sin desplazarse. |

### Checklist

#### Backend
- [x] Traducciones nuevas (ES/FR/DE/IT/PT) de las pistas de arrastre.

#### Frontend
- [x] `GameDetail.qml`: overlay a pantalla completa, sin caja, con blur + tinte.
- [x] `GameDetail.qml`: carátula fija arriba a la izquierda, rotable y nunca recortada.
- [x] `DsCartridge3D.qml`: visor ampliado (`modelScale`) para no cortar esquinas al rotar.
- [x] `Main.qml`: escena envuelta para el blur, `backdropItem` y toast recolocado.
- [x] `TopBar.qml`: buscador oculto en Estadísticas y API de foco.
- [x] `Main.qml`: ocultar dock/ranura/aviso en Stats y usar todo el alto.
- [x] `StatsView.qml`: meses del actual a enero conservando `monthIndex`.
- [x] `Main.qml`: capa de guardia para limpiar el foco al pulsar fuera.
- [x] `DsCartridge3D.qml`/`Cartridge.qml`: el 3D desactiva su `MouseArea` (rota la ficha); el 2D mantiene hover y doble clic.
- [x] `BigPicture.qml`: pasa `backdropItem: null` explícito y conserva el scroll.
- [x] Tests QML: buscador oculto en stats, foco del buscador y ficha abierta.
- [x] Tests QML: dock oculto en stats y meses en orden inverso.
- [x] README/CHANGELOG/WORKFLOW actualizados.
- [x] Verificación visual (normal, compacta y Big Picture).

### Verificación
- [x] `python -m pytest -q` → **140 passed**.
- [x] Capturas de la ficha a 1180×800 (clásico y DS 3D), 900×620 (compacta) y
  dentro de Big Picture, incluida la rotación extrema (±50° de inclinación y
  giro completo) para comprobar que no se corta ninguna esquina.
- [x] Comprobado con `QTest`: el buscador se oculta en Stats, el clic fuera
  quita el foco y el clic sigue abriendo la ficha del juego.
- [x] Captura de Stats sin dock (todo el alto) con octubre primero y la
  comprobación de que la lista termina en enero.

## Feature 0.16.0 — Perfil de juego, unificación y estado

### Descripción funcional

- Añadir a la ficha de cada juego un **perfil GameCenter** independiente de la
  tienda: puntuación 0–100 y estado (Playing, On Going, Beaten, Completed,
  Played, Plan to Play, On Hold, Not Played, Abandoned).
- El perfil se muestra siempre en la información del juego con un diseño
  moderno y se edita desde los **ajustes del juego** (engranaje / Edit profile).
- Permitir **unificar manualmente** los datos de otra entrada conocida, aunque
  ya no aparezca en la biblioteca, sobre el juego abierto (destino):
  - el selector de origen empieza **vacío**: no se preselecciona ninguna entrada,
  - suma horas y contador de sesiones,
  - mueve el timeline de sesiones al ID destino,
  - guarda una **captura de la carátula del origen** en disco para recaps,
  - si el destino no tiene carátula real, adopta la del origen,
  - deja un registro de trazabilidad (`mergedSources`) visible en la ficha,
  - permite ocultar el origen tras unificar para no duplicar estadísticas.
- La identidad sigue siendo el ID de tienda, pero el perfil permite reconstruir
  una trazabilidad constante entre plataformas.

### Contrato de API

| Elemento | Tipo | Descripción |
| --- | --- | --- |
| `profiles.json` | archivo | `%APPDATA%/GameCenter/profiles.json`; metadatos por ID. |
| `profiles.rating` | int/null | 0–100; `null` si no se ha puntuado. |
| `profiles.status` | string | `playing`, `ongoing`, `beaten`, `completed`, `played`, `plan`, `onhold`, `notplayed`, `abandoned`. |
| `profiles.merged_sources` | list | Registros importados con id, título, fuente, fecha, segundos, sesiones y captura. |
| `profiles.merged_into` | string | ID destino cuando esta entrada ya fue unificada. |
| `profiles.extra_seconds` | int | Horas importadas que se suman a las de Steam en el destino. |
| `Library.mergeCandidates(gameId)` | slot → `QVariantList` | Entradas importables, incluidas las retiradas con datos (`orphan`); mismo título primero. |
| `Library.mergeGameData(sourceId, targetId, hideSource)` | slot → `QVariantMap` | `{ok, message, targetId}`. |
| `Library.setGameRating(gameId, rating)` | slot | Guarda 0–100. |
| `Library.setGameStatus(gameId, status)` | slot | Guarda el estado validado. |
| `Library.rowForId(gameId)` | slot → int | Fila visible actual o `-1`. |
| `gameDetailById()/gameAt()` | payload | Añade `rating`, `hasRating`, `status`, `mergedSources`, `mergedInto`, `mergedIntoTitle`; cada sesión lleva `imported`. |
| `GameDetail.profileChanged()` | signal | El padre recarga la ficha tras editar o unificar. |

### Checklist

#### Backend
- [x] `profiles.py`: lectura/escritura atómica, estados válidos, rating 0–100, registros de fusión.
- [x] `playtime.py`: helpers para escribir/limpiar resumen y mover historial entre IDs.
- [x] `sources/__init__.py`: sumar `extra_seconds` del perfil a las horas de Steam y restar el tiempo ya unificado del origen.
- [x] `LibraryModel`: candidatos, merge, rating y status; refresco de datos.
- [x] Captura de carátula en `recap_covers/` y adopción si el destino no tiene.
- [x] Tests de perfiles, merge, rating/status, entradas eliminadas y aislamiento de rutas.

#### Frontend
- [x] `GameProfilePanel.qml`: estados, slider 0–100, selector de origen vacío, unificación, registros importados.
- [x] `GameDetail.qml`: tira de perfil visible, botón de ajustes y panel expandible.
- [x] `Main.qml`/`BigPicture.qml`: recargar ficha con `profileChanged`.
- [x] Traducciones ES/FR/DE/IT/PT.
- [x] Verificación visual en ventana normal, compacta y Big Picture.

### Verificación
- [x] `python -m pytest -q` → **138 passed**.
- [x] Capturas de la ficha con perfil y del panel de unificación (normal, 900×620 y Big Picture).
- [x] README/CHANGELOG/WORKFLOW actualizados.

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
- El perfil vive en `%APPDATA%/GameCenter/profiles.json`; las capturas de
  carátula de las fusiones se guardan en `%APPDATA%/GameCenter/recap_covers/`.
- El origen de una unificación se vacía (horas/sesiones/timeline) y, por
  defecto, se oculta para no duplicar estadísticas. Se puede restaurar desde
  Ajustes; un origen ya unificado no se puede volver a importar.
- Las horas nativas de Steam se conservan en Steam; el tiempo importado hacia
  un destino Steam se superpone desde el perfil (`extra_seconds`) sin tocar
  `localconfig.vdf`.
