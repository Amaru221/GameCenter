# WORKFLOW STATE — Capturas, inserción por capas y destacados de Stats

## Feature 0.19.0 — Overlay de captura y capturas en el timeline

### Descripción funcional

- **Ubicación actual de las capturas**: `%APPDATA%/GameCenter/screenshots/`
  (Linux: la carpeta `GameCenter/screenshots` dentro de `XDG_CONFIG_HOME` o
  `~/.config`). El índice nuevo vive en `%APPDATA%/GameCenter/screenshots.json`.
- Al guardar una captura:
  - aparece un **flash breve** sobre la pantalla del juego,
  - se muestra una **tarjeta con la miniatura** en la esquina inferior derecha,
    siempre encima, sin foco y con ratón atravesable,
  - desaparece sola a los ~2,7 s.
- El índice vincula cada PNG con:
  - `gameId`,
  - `sessionId`,
  - inicio de la sesión,
  - instante de la captura.
- En la ficha del juego:
  - el **timeline de sesiones** muestra las **2 primeras capturas** a la derecha
    de cada sesión,
  - si hay más, aparece la **tercera miniatura con un contador +N**,
  - una sección **SCREENSHOTS** reúne todas las capturas del juego,
  - al pulsar cualquier miniatura se abre un **visor a pantalla completa** con
    anterior/siguiente, contador y fecha.
- Las capturas sin sesión identificable siguen apareciendo en la galería del
  juego; las que ya no existen en disco se ignoran. Las capturas antiguas sin
  índice se recuperan por el prefijo del título y la marca `YYYYMMDD-HHMMSS`
  del nombre de archivo.

### Decisiones de arquitectura

- `core/screenshot_store.py`: índice JSON atómico, filtrado de archivos
  inexistentes y URL `file://` lista para QML.
- `SessionTracker.list` expone `startedAt` para que el manager pueda guardar el
  inicio exacto de la sesión.
- `ScreenshotManager` guarda el índice al capturar y expone `lastCapture`
  (`path`, `url`, `gameId`, `title`, `takenAt` y geometría de la pantalla).
- `ScreenshotOverlay.qml` es una **ventana top-level independiente** con flags
  `Frameless | StaysOnTop | TransparentForInput | DoesNotAcceptFocus | Tool`.
  Se crea una sola vez desde `app.py` (no anidada en `Main`) para evitar
  problemas de ciclo de vida y poder superponerse al juego.
- `LibraryModel._detail_payload` cruza el índice con `history_for(game)` por
  `sessionStartedAt` (tolerancia 2 s) y, como respaldo, por el intervalo
  `[start, start + seconds]`.
- `GameDetail.qml` incorpora `ShotThumb`, la galería, el visor y los atajos
  Escape/←/→ cuando el visor está abierto.
- Los tests de UI definen `GC_NO_OVERLAY=1` para no crear ventanas top-level en
  cada engine; el overlay se valida aparte.

### Contrato de API (adiciones)

| Elemento | Tipo | Descripción |
| --- | --- | --- |
| `screenshot_store.index_path()` | función | `config_dir()/screenshots.json`. |
| `screenshot_store.record(...)` | función | Indexa un PNG con juego/sesión/tiempos. |
| `screenshot_store.for_game(game_id)` | función | Capturas existentes con `url`. |
| `SessionTracker.list[].startedAt` | int | Inicio de la sesión activa. |
| `Screenshots.lastCapture` | `QVariantMap` | Datos de la última captura y geometría de pantalla. |
| `ScreenshotOverlay.play(capture)` | función QML | Muestra flash + tarjeta. |
| `gameDetail.screenshots` | list | Todas las capturas del juego, recientes primero. |
| `gameDetail.screenshotCount` | int | Total de capturas. |
| `history[].screenshots` | list | Capturas asociadas a esa sesión. |
| `history[].previewScreenshots` | list | Primeras 2 capturas. |
| `history[].overflowScreenshot` | object | Tercera captura para el contador. |
| `history[].overflowCount` | int | `total - 2`. |
| `GameDetail.openViewer(shots,index)` | función | Abre el visor. |
| `GameDetail.viewerOpen` | bool | Visor visible. |

### Checklist

- [x] `screenshot_store.py` e índice atómico.
- [x] `SessionTracker.startedAt` y `ScreenshotManager` con `lastCapture`.
- [x] Overlay top-level con flash y tarjeta click-through.
- [x] Timeline con 2 miniaturas + contador `+N`.
- [x] Miniaturas más grandes, líneas separadas y scroll propio del timeline.
- [x] X de “Add a game” anclada a la esquina superior derecha.
- [x] Scrollbar de Ajustes separada de la X de cierre.
- [x] Galería SCREENSHOTS en la ficha.
- [x] Visor a pantalla completa con anterior/siguiente y teclado.
- [x] Traducciones ES/FR/DE/IT/PT.
- [x] Tests de índice, captura, asociación a sesiones y QML.
- [x] Recuperación de capturas antiguas por título + timestamp.
- [x] README/CHANGELOG/WORKFLOW y verificación visual.

### Verificación

- [x] `python -m pytest -q` → **161 passed**.
- [x] Captura del detalle con timeline (2 miniaturas + `+2`), galería y visor.
- [x] Timeline con 9 sesiones: scroll vertical, miniaturas 64×40 y líneas largas.
- [x] Captura del diálogo Add a game con la X en la esquina derecha.
- [x] Captura de Ajustes con scrollbar visible sin solapar la X.
- [x] Comprobado el overlay como ventana independiente (`opened=true`,
  `cardOpacity=1`, geometría de pantalla).
- [x] Índice aislado en tests; sin residuos en `%APPDATA%`.

## Feature 0.18.0 — Review anual estilo Instagram Stories

### Descripción funcional

- El botón **Review year** de Estadísticas abre una presentación **a pantalla
  completa**, inmersiva y animada, en lugar de recorrer las tarjetas actuales.
- La presentación incluye:
  - apertura con el año, tiempo total, sesiones, días, juegos y juego más
    jugado;
  - una diapositiva por **mes activo** con horas, sesiones, días, mejor día,
    racha, carátula del juego principal, top 3 y actividad diaria;
  - diapositivas dedicadas a **most played game**, **sessions**,
    **longest streak**, **best day** y **busiest month**;
  - cierre con el resumen del año y “See you next year”.
- Estilo stories: barras de progreso segmentadas, avance automático (7,2 s),
  pausa/reanudación, cierre, navegación con ←/→/Espacio/Esc, mando
  (D-pad/LB/RB/B/A) y tap en el tercio izquierdo/derecho.
- Fondo con degradado por acento, orbes animados, watermark del año, tarjetas
  de cristal, carátulas grandes, revelados escalonados y barras animadas.
- El acento de cada diapositiva sale del color del juego/mes protagonista.

### Decisiones de arquitectura

- `stats.year_review()` reutiliza `build(period="year")` y añade:
  `bestDay`, `longestStreak`, `busiestMonth`, `mostSessionsMonth`,
  `mostDaysMonth`, `totalGames`, `activeMonths`, ritmo mensual y una lista
  `slides` ya ordenada con su `type` y `accent`.
- `Library.yearReview(year)` expone el payload por QML con las carátulas
  actuales.
- `YearReview.qml` gestiona la presentación, el temporizador, las barras y la
  navegación; `YearReviewSlide.qml` renderiza cada tipo de diapositiva.
- El overlay vive en `Main.qml` (z 32) para cubrir también la barra superior y
  las tarjetas. Los atajos globales de `Main` se desactivan mientras está
  abierto.
- `StatsView` emite `reviewRequested(year)` y conserva `Review year` como
  entrada; se elimina el antiguo `reviewTimer` que autoavanzaba el carrusel.

### Contrato de API (adiciones)

| Elemento | Tipo | Descripción |
| --- | --- | --- |
| `Library.yearReview(year)` | slot → `QVariantMap` | Payload completo del recap anual. |
| `stats.year_review()` | función | Construye resumen, meses activos y slides. |
| `review.slides` | `list` | Diapositivas ordenadas: `intro`, `month`, `topGame`, `sessions`, `streak`, `bestDay`, `busiest`, `outro`. |
| `review.slides[].accent` | string | Color dominante de la diapositiva. |
| `review.bestDay` | object | Fecha, horas, sesiones y juego principal del mejor día. |
| `review.longestStreak` | object | Días, inicio, fin y rango de la mejor racha. |
| `review.busiestMonth` | object | Mes con más horas. |
| `review.averageSessionText` | string | Duración media por sesión. |
| `review.monthSessions/monthTotals` | list | Ritmo mensual para las barras. |
| `StatsView.reviewRequested(year)` | signal | Abre el recap desde el botón. |
| `YearReview.open(data, year)` | función QML | Inicia la presentación. |
| `YearReview.next/previous/close/togglePause` | funciones QML | Navegación. |
| `YearReview.storyMs` | int | 7200 ms por diapositiva. |
| `YearReview.currentSlide/currentIndex/progress/paused` | propiedades | Estado de la historia. |

### Checklist

- [x] Backend: `year_review`, slides, best day, streak, busiest month y ritmo.
- [x] `LibraryModel.yearReview` y carátulas.
- [x] `YearReview.qml`: progreso, timer, pausa, navegación, teclado y mando.
- [x] `YearReviewSlide.qml`: intro, meses, top game, sesiones, racha, mejor día,
      mes ajetreado y outro animados.
- [x] `StatsView`: botón Review year, señal y eliminación del autoavance.
- [x] `Main`: overlay a pantalla completa y atajos bloqueados.
- [x] Traducciones ES/FR/DE/IT/PT.
- [x] Tests backend y QML del payload, slides y navegación.
- [x] README/CHANGELOG/WORKFLOW y verificación visual.

### Verificación

- [x] `python -m pytest -q` → **158 passed**.
- [x] Capturas offscreen de intro, mes, top game, sesiones, racha, mejor día,
      mes ajetreado y outro.
- [x] Comprobado el progreso segmentado, la pausa y la navegación QML.

## Refinamiento 0.17.0 — Estadísticas por periodo y tarjetas enriquecidas

### Descripción funcional

- La granularidad del desglose sigue al filtro:
  - **Week** → una tarjeta por día (7 días).
  - **Month** → una tarjeta por semana del mes.
  - **Year** → una tarjeta por mes (comportamiento anterior).
  - **All time** conserva el desglose mensual del año seleccionado y el total
    histórico (decisión tomada para no introducir un cuarto tipo de tarjeta).
- El banner superior de tiempo jugado muestra el **juego con más horas del
  periodo** (carátula, nombre, horas y etiqueta del periodo).
- Las tarjetas muestran:
  - carátula del juego más jugado junto al nombre,
  - **top 3** numerado con carátula, horas detalladas en negrita y barra,
  - fila **Other games** con las horas del resto, sin barra,
  - **rombo + número dentro del mismo contenedor** para las métricas líderes
    (horas, días jugados y sesiones), sin insignias sueltas arriba,
  - un **banner único** por tarjeta: *Busiest month/week/day*, *Longest streak*
    o *Best day*,
  - etiquetas de métricas y gráfico con mejor tipografía y contraste.
- Los títulos del gráfico y del banner de repaso se adaptan al periodo.
- `Other games`, `Most days played`, `Longest streak`, días de la semana y
  títulos por periodo se traducen en ES/FR/DE/IT/PT.

### Decisiones de arquitectura

- `stats.build()` construye `buckets` genéricos (`kind` = `month`, `week` o
  `day`) con el mismo payload que antes usaban los meses. `months` se conserva
  como alias compatible con el desglose anual.
- `_day_buckets()` recorre los 7 días del periodo semanal; `_week_buckets()`
  parte el mes en semanas de lunes a domingo; `_months()` mantiene el desglose
  mensual. Los tres usan `_bucket_payload()`.
- `_annotate_buckets()` calcula los máximos del periodo y genera el `banner`
  único. `topSessions`/`topDays` solo se marcan si el máximo es mayor que 1
  para evitar destacados triviales en tarjetas diarias.
- `_river()` ahora recibe los buckets del periodo, no solo los meses, y expone
  `labels` además de `months`.
- `LibraryModel.stats()` sigue pasando el mapa de carátulas.
- `StatsView` usa `statsData.buckets`, `bucketsKind`, `topGame` y
  `river.labels`; `months` queda como alias para el carrusel anual.

### Contrato de API (adiciones)

| Elemento | Tipo | Descripción |
| --- | --- | --- |
| `stats.buckets` | `list` | Tarjetas del periodo actual (mes, semana o día). |
| `stats.bucketsKind` | `string` | `month`, `week` o `day`. |
| `stats.buckets[].kind` | `string` | Tipo de la tarjeta. |
| `stats.buckets[].rangeText` | `string` | Rango legible (`26–27 Oct`, `26/10`…). |
| `stats.buckets[].topGames` | `list` | Como máximo 3 juegos, con carátula y horas detalladas. |
| `stats.buckets[].otherHoursText` | `string` | Tiempo agrupado en Other games (sin barra). |
| `stats.buckets[].hasOtherGames` | `bool` | Hay juegos fuera del top 3. |
| `stats.buckets[].topHours/topSessions/topDays` | `bool` | Líder del periodo (sesiones/días solo si el máximo > 1). |
| `stats.buckets[].banner` | `object` | `{label, value, detail, tint}` del destacado único. |
| `stats.buckets[].streak` | `int` | Racha dentro de la tarjeta. |
| `stats.topGame` | `object` | Juego con más horas del periodo (incluye `cover`). |
| `stats.river.labels` | `list` | Etiquetas de los buckets del periodo. |
| `StatsView.bucketsKind` | `string` | Tipo de tarjeta activo. |
| `StatsView.topGame` | `object` | Atajo a `statsData.topGame`. |
| `StatsView.reviewText()` | función | Texto del banner de repaso por periodo. |
| `StatsView.riverSubtitle()` | función | Subtítulo del gráfico por periodo. |

### Checklist

- [x] Backend: buckets de días, semanas y meses; top 3 + Other games + banners.
- [x] Backend: `topGame` del periodo y `river.labels`.
- [x] Traducciones nuevas y tests de periodos, top 3, Other games y banners.
- [x] QML: tarjetas con rombo+número, top 3 con carátula, Other games y banner.
- [x] QML: hero con juego más jugado y chips/labels restilizados.
- [x] QML: títulos y banner de repaso según periodo.
- [x] Tests QML de buckets por periodo y tarjetas enriquecidas.
- [x] README/CHANGELOG/WORKFLOW actualizados.
- [x] Verificación visual Week/Month/Year con capturas 1180×1400.

### Verificación

- [x] `python -m pytest -q` → **155 passed**.
- [x] Capturas offscreen de Week (días), Month (semanas) y Year (meses) con
  tarjetas completas, top 3, Other games y banners.
- [x] Comprobado que `topSessions`/`topDays` no destacan valores triviales de 1.
- [x] Comprobado el hero con el top game del periodo.

## Feature 0.17.0 — Capturas de juego, cartucho tras el dock y meses destacados

### Descripción funcional

- **Capturas de pantalla del juego**:
  - Se configura el atajo de teclado desde **Ajustes → SCREENSHOTS**.
  - Por defecto el teclado usa **Ctrl + Av Pág** (`Ctrl+PageDown`).
  - En mando, el atajo por defecto es **mantener Select/View 5 segundos**.
  - Solo se captura cuando hay una sesión de juego activa lanzada desde
    GameCenter; el PNG se guarda en `%APPDATA%/GameCenter/screenshots/`.
  - El atajo de teclado es **global en Windows** (funciona con el juego en
    primer plano) y local en el resto de plataformas.
  - Se muestra un aviso con el nombre del archivo guardado.
- **Inserción del cartucho**:
  - El cartucho que vuela al dock pasa **por detrás de la cara frontal del
    dock** (banner) y **por delante de la pletina oscura** de inserción.
  - La pletina es una pieza más oscura que el banner, situada detrás del
    cartucho, para que la animación se lea como una inserción real.
  - El cartucho que ya estaba en la ranura queda también detrás del banner.
- **Estadísticas**:
  - Cada tarjeta mensual muestra la **carátula del juego más jugado** junto al
    nombre del mes (con tooltip de título y horas).
  - Se añaden **tres insignias estéticas** en el mes del año con:
    - **más horas** jugadas,
    - **más sesiones**,
    - **más días** jugados.
  - En caso de empate, la insignia se muestra en todos los meses empatados.

### Decisiones de arquitectura

- `ScreenshotManager` (`core/screenshots.py`) centraliza la captura, el guardado
  y el registro del atajo global. Usa `QScreen.grabWindow(0)` sobre la pantalla
  del cursor y escribe en `config_dir()/screenshots/`.
- En Windows el atajo se registra con `RegisterHotKey` y un
  `QAbstractNativeEventFilter` (sin dependencias nuevas). Solo permanece
  registrado **mientras hay una sesión de juego activa**, para no apropiarse de
  la combinación cuando no hay partida. Si el sistema rechaza la combinación, el
  error se muestra en Ajustes y se mantiene el `Shortcut` local de QML como
  respaldo.
- `GamepadManager` incorpora la señal `screenshot` y un temporizador de flanco
  sobre `BUTTON_BACK` (Select/View): 5 s mantenidos. El resto del mapeo no
  cambia.
- `Preferences` valida el atajo contra una lista curada y lo persiste como
  `screenshotShortcut`.
- El `InsertEffect` deja de ser hijo de la ventana y pasa a vivir dentro de
  `libraryDock`, entre la pletina (`z: 12`) y el dock (`z: 20`). Así comparte
  el mismo contexto de apilado: pletina < cartucho en ranura < cartucho volando
  < cara frontal del dock.
- `stats.build()` recibe un mapa de carátulas desde `LibraryModel` para no
  acoplar el agregador a los proveedores de imágenes. Tras construir los meses,
  calcula los máximos anuales y añade `topHours`, `topSessions`, `topDays` y
  `mostPlayed` a cada mes.
- `StatsView.MonthCard` pinta la carátula y un componente `HighlightBadge` con
  degradado, borde y punto de color; las etiquetas se traducen vía `Tr`.

### Contrato de API

| Elemento | Tipo | Descripción |
| --- | --- | --- |
| `settings.json → screenshotShortcut` | string | `ctrl+pagedown` (defecto), `ctrl+f12`, `f12`, `printscreen`, `ctrl+shift+s`, `none`. |
| `Screenshots.shortcut` | `string` (notify `changed`) | Atajo persistido actual. |
| `Screenshots.setShortcut(value)` | slot | Valida, persiste y vuelve a registrar el atajo. |
| `Screenshots.shortcutSequence` | `string` | Secuencia Qt para el `Shortcut` local (`Ctrl+PageDown`…). |
| `Screenshots.localShortcutEnabled` | `bool` | `true` si el hotkey global no está activo (Linux o conflicto). |
| `Screenshots.registered` | `bool` | El atajo global está registrado en el sistema. |
| `Screenshots.error` | `string` | Mensaje si el sistema rechaza el atajo. |
| `Screenshots.directory` | `string` | Carpeta de capturas. |
| `Screenshots.captureIfPlaying()` | slot → `string` | Captura solo si hay sesión activa; devuelve la ruta. |
| `Screenshots.capture()` | slot → `string` | Captura siempre la pantalla actual. |
| `Screenshots.openFolder()` | slot | Abre la carpeta de capturas. |
| `Screenshots.saved(path)` / `failed(message)` | signals | Resultado de la captura para el toast. |
| `Gamepad.screenshot` | signal | Select/View mantenido 5 s. |
| `Gamepad.screenshotHoldSeconds` | `real` (constant) | 5.0. |
| `InsertEffect` | QML Item | Ahora hijo de `libraryDock`; `z: 15`. |
| `insertPlate` | QML Item | Pletina oscura detrás del cartucho; `z: 12`. |
| `slotCartridge` | QML Item | Cartucho en ranura; `z: 13`. |
| `dock` | QML Item | Cara frontal del banner; `z: 20`. |
| `stats.build(..., covers=...)` | parámetro opcional | `{game_id: cover_url}`. |
| `stats.months[].mostPlayed` | `object` | `{gameId, name, hoursText, cover, …}` del juego con más horas del mes. |
| `stats.months[].topHours/topSessions/topDays` | `bool` | El mes es el máximo del año en esa métrica. |
| `Library.stats()` | slot | Pasa las carátulas actuales de la biblioteca. |

### Checklist

#### Backend
- [x] `core/screenshots.py`: captura, guardado, hotkey global Windows y API QML.
- [x] `preferences.py`: `screenshotShortcut` validado y persistido.
- [x] `gamepad.py`: señal `screenshot` al mantener Select 5 s.
- [x] `app.py`: exponer `Screenshots` y conectar mando + hotkey.
- [x] `stats.py`: carátulas en `topGames`, `mostPlayed` y flags de máximos.
- [x] `library_model.py`: `stats()` pasa el mapa de carátulas.
- [x] Traducciones ES/FR/DE/IT/PT y tests de backend.

#### Frontend
- [x] `SettingsPanel.qml`: sección SCREENSHOTS con atajo, ayuda de mando y carpeta.
- [x] `Main.qml`: mover `InsertEffect` a `libraryDock`, pletina, z-order y toast de captura.
- [x] `StatsView.qml`: carátula junto al nombre y tres insignias de destacado.
- [x] `Dock.qml`: boca de ranura coherente con la pletina (si hace falta).
- [x] Tests QML de capas, ajuste de captura y estadísticas.
- [x] README/CHANGELOG y verificación visual.

### Verificación
- [x] `python -m pytest -q` → **150 passed**.
- [x] Capturas de ajustes, inserción (fotograma intermedio) y Stats con insignias.
- [x] Comprobación del atajo global con `WM_HOTKEY` simulado y captura PNG real.
- [x] Captura real de pantalla guardada en `screenshots/` (405 KB).
- [x] Comprobación visual del apilado: pletina (12) < ranura (13) < cartucho
  volando (15) < dock (20).

## Feature 0.16.5 — Modal de juego a pantalla completa

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
